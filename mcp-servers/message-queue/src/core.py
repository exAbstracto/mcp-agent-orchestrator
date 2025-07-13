"""
Core Message Queue Business Logic

Contains the core data structures and business logic for the message queue
that can be used by different MCP implementations.
"""

import asyncio
import logging
import sys
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Set


@dataclass
class Message:
    """Represents a message in the queue system."""

    id: str
    channel: str
    sender: str
    content: Any
    timestamp: float
    expiry: Optional[float] = None
    priority: int = 0  # Higher = more priority
    delivery_attempts: int = 0
    max_delivery_attempts: int = 3


@dataclass
class Subscription:
    """Represents a client subscription to a channel."""

    agent_id: str
    channel: str
    created_at: float
    filters: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceMetrics:
    """Performance monitoring metrics."""

    messages_sent: int = 0
    messages_delivered: int = 0
    messages_failed: int = 0
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    peak_latency_ms: float = 0.0
    channels_count: int = 0
    subscribers_count: int = 0


class MessageQueueCore:
    """
    Core message queue implementation with pub/sub messaging.

    Provides reliable pub/sub messaging with:
    - Channel-based messaging
    - Reliable delivery with retries
    - Performance monitoring
    - Message persistence (in-memory)
    - Priority handling
    """

    def __init__(self, name: str = "message-queue"):
        """Initialize the message queue core."""
        self.name = name
        self.logger = self._setup_logging()

        # Message storage and delivery
        self.messages: Dict[str, deque] = defaultdict(deque)  # channel -> messages
        self.pending_messages: Dict[str, Message] = {}  # message_id -> message
        self.subscriptions: Dict[str, List[Subscription]] = defaultdict(
            list
        )  # channel -> subscriptions
        self.agent_subscriptions: Dict[str, Set[str]] = defaultdict(
            set
        )  # agent_id -> channels

        # Performance monitoring
        self.metrics = PerformanceMetrics()
        self.latency_samples: deque = deque(maxlen=1000)  # Keep last 1000 samples

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

        self.logger.info(f"Initialized message queue core: {name}")

    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def start(self):
        """Start background tasks."""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_messages())
        self.logger.info("Message queue core started")

    async def stop(self):
        """Stop background tasks."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Message queue core stopped")

    async def _cleanup_expired_messages(self):
        """Background task to clean up expired messages."""
        while self._running:
            try:
                current_time = time.time()
                expired_message_ids = []

                # Find expired messages
                for msg_id, message in self.pending_messages.items():
                    if message.expiry and current_time > message.expiry:
                        expired_message_ids.append(msg_id)

                # Remove expired messages
                for msg_id in expired_message_ids:
                    message = self.pending_messages.pop(msg_id, None)
                    if message:
                        self.logger.debug(
                            f"Expired message {msg_id} from channel {message.channel}"
                        )
                        self.metrics.messages_failed += 1

                # Clean up empty channel queues
                empty_channels = [
                    channel
                    for channel, queue in self.messages.items()
                    if len(queue) == 0
                ]
                for channel in empty_channels:
                    if channel in self.messages:
                        del self.messages[channel]

                await asyncio.sleep(10)  # Check every 10 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(5)

    def publish_message(
        self,
        channel: str,
        content: Any,
        sender: str,
        priority: int = 0,
        ttl_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Publish a message to a channel."""
        start_time = time.time()

        try:
            # Create message
            message_id = str(uuid.uuid4())
            timestamp = time.time()
            expiry = timestamp + ttl_seconds if ttl_seconds else None

            message = Message(
                id=message_id,
                channel=channel,
                sender=sender,
                content=content,
                timestamp=timestamp,
                expiry=expiry,
                priority=priority,
            )

            # Store message
            self.messages[channel].append(message)
            self.pending_messages[message_id] = message

            # Sort by priority (higher priority first)
            self.messages[channel] = deque(
                sorted(self.messages[channel], key=lambda m: m.priority, reverse=True)
            )

            # Update metrics
            self.metrics.messages_sent += 1
            latency_ms = (time.time() - start_time) * 1000
            self._record_latency(latency_ms)

            self.logger.info(f"Published message {message_id} to channel {channel}")

            return {
                "message_id": message_id,
                "timestamp": timestamp,
                "channel": channel,
                "latency_ms": latency_ms,
            }

        except Exception as e:
            raise ValueError(f"Error publishing message: {e}")

    def subscribe_channel(
        self, channel: str, agent_id: str, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Subscribe to a channel."""
        try:
            # Check if already subscribed
            existing = any(
                sub.agent_id == agent_id for sub in self.subscriptions[channel]
            )

            if not existing:
                subscription = Subscription(
                    agent_id=agent_id,
                    channel=channel,
                    created_at=time.time(),
                    filters=filters,
                )

                self.subscriptions[channel].append(subscription)
                self.agent_subscriptions[agent_id].add(channel)

                self.logger.info(f"Agent {agent_id} subscribed to channel {channel}")

            # Update metrics
            self.metrics.subscribers_count = sum(
                len(subs) for subs in self.subscriptions.values()
            )
            self.metrics.channels_count = len(self.subscriptions)

            result = {
                "channel": channel,
                "agent_id": agent_id,
                "subscribed": True,
                "message_count": len(self.messages.get(channel, [])),
            }

            # Include filters in response if provided
            if filters is not None:
                result["filters"] = filters

            return result

        except Exception as e:
            raise ValueError(f"Error subscribing: {e}")

    def unsubscribe_channel(self, channel: str, agent_id: str) -> Dict[str, Any]:
        """Unsubscribe from a channel."""
        try:
            # Remove subscription
            self.subscriptions[channel] = [
                sub for sub in self.subscriptions[channel] if sub.agent_id != agent_id
            ]

            self.agent_subscriptions[agent_id].discard(channel)

            # Clean up empty channel subscriptions
            if not self.subscriptions[channel]:
                del self.subscriptions[channel]

            self.logger.info(f"Agent {agent_id} unsubscribed from channel {channel}")

            # Update metrics
            self.metrics.subscribers_count = sum(
                len(subs) for subs in self.subscriptions.values()
            )
            self.metrics.channels_count = len(self.subscriptions)

            return {
                "channel": channel,
                "agent_id": agent_id,
                "unsubscribed": True,
            }

        except Exception as e:
            raise ValueError(f"Error unsubscribing: {e}")

    def get_messages(
        self, agent_id: str, channel_filter: Optional[str] = None, limit: int = 10
    ) -> Dict[str, Any]:
        """Get pending messages for an agent."""
        try:
            messages = []

            # Get channels agent is subscribed to
            agent_channels = self.agent_subscriptions.get(agent_id, set())
            if channel_filter:
                agent_channels = agent_channels.intersection({channel_filter})

            # Collect messages from subscribed channels
            for channel in agent_channels:
                channel_messages = list(self.messages.get(channel, []))
                for message in channel_messages[:limit]:
                    message_dict = asdict(message)
                    message_dict["delivery_time"] = time.time()
                    messages.append(message_dict)

            # Sort by priority and timestamp
            messages.sort(key=lambda m: (m["priority"], m["timestamp"]), reverse=True)
            messages = messages[:limit]

            self.logger.debug(
                f"Retrieved {len(messages)} messages for agent {agent_id}"
            )

            return {
                "agent_id": agent_id,
                "messages": messages,
                "count": len(messages),
            }

        except Exception as e:
            raise ValueError(f"Error getting messages: {e}")

    def acknowledge_message(self, message_id: str, agent_id: str) -> Dict[str, Any]:
        """Acknowledge message delivery."""
        try:
            # Remove from pending messages
            message = self.pending_messages.pop(message_id, None)
            if message:
                # Remove from channel queue
                channel_queue = self.messages.get(message.channel)
                if channel_queue:
                    self.messages[message.channel] = deque(
                        msg for msg in channel_queue if msg.id != message_id
                    )

                self.metrics.messages_delivered += 1
                self.logger.debug(
                    f"Message {message_id} acknowledged by agent {agent_id}"
                )

                return {
                    "message_id": message_id,
                    "agent_id": agent_id,
                    "acknowledged": True,
                }
            else:
                return {
                    "message_id": message_id,
                    "agent_id": agent_id,
                    "acknowledged": False,
                    "reason": "Message not found",
                }

        except Exception as e:
            raise ValueError(f"Error acknowledging message: {e}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        try:
            # Update real-time metrics
            self.metrics.channels_count = len(self.messages)
            self.metrics.subscribers_count = sum(
                len(subs) for subs in self.subscriptions.values()
            )

            metrics_dict = asdict(self.metrics)
            metrics_dict["pending_messages"] = len(self.pending_messages)
            metrics_dict["total_channels"] = len(self.messages)
            metrics_dict["timestamp"] = time.time()

            return metrics_dict

        except Exception as e:
            raise ValueError(f"Error getting metrics: {e}")

    def list_channels(self) -> Dict[str, Any]:
        """List all active channels."""
        try:
            channels = []

            # Include all channels with either messages or subscriptions
            all_channels = set(self.messages.keys()) | set(self.subscriptions.keys())
            for channel_name in all_channels:
                subscribers = [
                    sub.agent_id for sub in self.subscriptions.get(channel_name, [])
                ]
                message_count = len(self.messages.get(channel_name, []))

                channels.append(
                    {
                        "name": channel_name,
                        "subscribers": subscribers,
                        "subscriber_count": len(subscribers),
                        "message_count": message_count,
                        "created_at": min(
                            (
                                sub.created_at
                                for sub in self.subscriptions.get(channel_name, [])
                            ),
                            default=time.time(),
                        ),
                    }
                )

            return {"channels": channels, "total_channels": len(channels)}

        except Exception as e:
            raise ValueError(f"Error listing channels: {e}")

    def _record_latency(self, latency_ms: float):
        """Record latency measurement."""
        self.latency_samples.append(latency_ms)
        self.metrics.total_latency_ms += latency_ms

        if latency_ms > self.metrics.peak_latency_ms:
            self.metrics.peak_latency_ms = latency_ms

        # Calculate rolling average
        if self.latency_samples:
            self.metrics.avg_latency_ms = sum(self.latency_samples) / len(
                self.latency_samples
            )
