"""
Message Queue MCP Server Implementation

Provides async pub/sub messaging between agents with reliable delivery
and performance monitoring.
"""

import asyncio
import json
import logging
import sys
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Union, Set
from datetime import datetime


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


class MessageQueueServer:
    """
    Message Queue MCP Server implementation.

    Provides reliable pub/sub messaging with:
    - Channel-based messaging
    - Reliable delivery with retries
    - Performance monitoring
    - Message persistence (in-memory)
    - Priority handling
    """

    def __init__(self, name: str = "message-queue", version: str = "1.0.0"):
        """Initialize the message queue server."""
        self.name = name
        self.version = version
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

        # MCP capabilities
        self.capabilities = {
            "tools": [
                {
                    "name": "publish_message",
                    "description": "Publish a message to a channel",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "channel": {
                                "type": "string",
                                "description": "Channel name",
                            },
                            "content": {"description": "Message content"},
                            "sender": {
                                "type": "string",
                                "description": "Sender agent ID",
                            },
                            "priority": {"type": "integer", "default": 0},
                            "ttl_seconds": {
                                "type": "number",
                                "description": "Time to live",
                            },
                        },
                        "required": ["channel", "content", "sender"],
                    },
                },
                {
                    "name": "subscribe_channel",
                    "description": "Subscribe to messages on a channel",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "channel": {
                                "type": "string",
                                "description": "Channel name",
                            },
                            "agent_id": {
                                "type": "string",
                                "description": "Subscriber agent ID",
                            },
                            "filters": {
                                "type": "object",
                                "description": "Optional message filters",
                            },
                        },
                        "required": ["channel", "agent_id"],
                    },
                },
                {
                    "name": "unsubscribe_channel",
                    "description": "Unsubscribe from a channel",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "channel": {
                                "type": "string",
                                "description": "Channel name",
                            },
                            "agent_id": {"type": "string", "description": "Agent ID"},
                        },
                        "required": ["channel", "agent_id"],
                    },
                },
                {
                    "name": "get_messages",
                    "description": "Get pending messages for an agent",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "agent_id": {"type": "string", "description": "Agent ID"},
                            "channel": {
                                "type": "string",
                                "description": "Optional channel filter",
                            },
                            "limit": {"type": "integer", "default": 10},
                        },
                        "required": ["agent_id"],
                    },
                },
                {
                    "name": "acknowledge_message",
                    "description": "Acknowledge message delivery",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "message_id": {
                                "type": "string",
                                "description": "Message ID",
                            },
                            "agent_id": {"type": "string", "description": "Agent ID"},
                        },
                        "required": ["message_id", "agent_id"],
                    },
                },
                {
                    "name": "get_performance_metrics",
                    "description": "Get performance metrics",
                    "inputSchema": {"type": "object", "properties": {}},
                },
                {
                    "name": "list_channels",
                    "description": "List all active channels",
                    "inputSchema": {"type": "object", "properties": {}},
                },
            ],
            "resources": [
                {
                    "uri": "queue://metrics",
                    "name": "Performance Metrics",
                    "description": "Real-time performance metrics",
                },
                {
                    "uri": "queue://channels",
                    "name": "Channel List",
                    "description": "List of active channels and subscribers",
                },
            ],
        }

        self.logger.info(f"Initialized {name} v{version}")

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
        self.logger.info("Message queue server started")

    async def stop(self):
        """Stop background tasks."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Message queue server stopped")

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

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a JSON-RPC 2.0 request."""
        # Validate basic JSON-RPC structure
        if not isinstance(request, dict):
            return self._create_error_response(None, -32600, "Invalid Request")

        request_id = request.get("id")

        if "jsonrpc" not in request or "method" not in request:
            return self._create_error_response(request_id, -32600, "Invalid Request")

        method = request.get("method")
        params = request.get("params", {})

        self.logger.debug(f"Handling request: {method}")

        # Route to appropriate handler
        try:
            if method == "initialize":
                return self._handle_initialize(request_id, params)
            elif method == "tools/call":
                return self._handle_tool_call(request_id, params)
            elif method == "resources/read":
                return self._handle_resource_read(request_id, params)
            elif method == "resources/list":
                return self._handle_resource_list(request_id)
            else:
                return self._create_error_response(
                    request_id, -32601, "Method not found"
                )

        except Exception as e:
            self.logger.error(f"Error handling {method}: {e}")
            return self._create_error_response(
                request_id, -32603, f"Internal error: {str(e)}"
            )

    def _handle_initialize(
        self, request_id: Union[str, int, None], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle the initialize method."""
        protocol_version = params.get("protocolVersion", "2024-11-05")
        client_info = params.get("clientInfo", {})

        self.logger.info(
            f"Client {client_info.get('name', 'unknown')} "
            f"v{client_info.get('version', 'unknown')} connected"
        )

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": protocol_version,
                "serverInfo": {"name": self.name, "version": self.version},
                "capabilities": self.capabilities,
            },
        }

    def _handle_tool_call(
        self, request_id: Union[str, int, None], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle tool call requests."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "publish_message":
            return self._publish_message(request_id, arguments)
        elif tool_name == "subscribe_channel":
            return self._subscribe_channel(request_id, arguments)
        elif tool_name == "unsubscribe_channel":
            return self._unsubscribe_channel(request_id, arguments)
        elif tool_name == "get_messages":
            return self._get_messages(request_id, arguments)
        elif tool_name == "acknowledge_message":
            return self._acknowledge_message(request_id, arguments)
        elif tool_name == "get_performance_metrics":
            return self._get_performance_metrics(request_id, arguments)
        elif tool_name == "list_channels":
            return self._list_channels(request_id, arguments)
        else:
            return self._create_error_response(
                request_id, -32601, f"Unknown tool: {tool_name}"
            )

    def _publish_message(
        self, request_id: Union[str, int, None], arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Publish a message to a channel."""
        start_time = time.time()

        try:
            channel = arguments["channel"]
            content = arguments["content"]
            sender = arguments["sender"]
            priority = arguments.get("priority", 0)
            ttl_seconds = arguments.get("ttl_seconds")

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
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "message_id": message_id,
                    "timestamp": timestamp,
                    "channel": channel,
                    "latency_ms": latency_ms,
                },
            }

        except KeyError as e:
            return self._create_error_response(
                request_id, -32602, f"Missing parameter: {e}"
            )
        except Exception as e:
            return self._create_error_response(
                request_id, -32603, f"Error publishing message: {e}"
            )

    def _subscribe_channel(
        self, request_id: Union[str, int, None], arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Subscribe to a channel."""
        try:
            channel = arguments["channel"]
            agent_id = arguments["agent_id"]
            filters = arguments.get("filters")

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
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result,
            }

        except KeyError as e:
            return self._create_error_response(
                request_id, -32602, f"Missing parameter: {e}"
            )
        except Exception as e:
            return self._create_error_response(
                request_id, -32603, f"Error subscribing: {e}"
            )

    def _unsubscribe_channel(
        self, request_id: Union[str, int, None], arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Unsubscribe from a channel."""
        try:
            channel = arguments["channel"]
            agent_id = arguments["agent_id"]

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
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "channel": channel,
                    "agent_id": agent_id,
                    "unsubscribed": True,
                },
            }

        except KeyError as e:
            return self._create_error_response(
                request_id, -32602, f"Missing parameter: {e}"
            )
        except Exception as e:
            return self._create_error_response(
                request_id, -32603, f"Error unsubscribing: {e}"
            )

    def _get_messages(
        self, request_id: Union[str, int, None], arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get pending messages for an agent."""
        try:
            agent_id = arguments["agent_id"]
            channel_filter = arguments.get("channel")
            limit = arguments.get("limit", 10)

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
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "agent_id": agent_id,
                    "messages": messages,
                    "count": len(messages),
                },
            }

        except KeyError as e:
            return self._create_error_response(
                request_id, -32602, f"Missing parameter: {e}"
            )
        except Exception as e:
            return self._create_error_response(
                request_id, -32603, f"Error getting messages: {e}"
            )

    def _acknowledge_message(
        self, request_id: Union[str, int, None], arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Acknowledge message delivery."""
        try:
            message_id = arguments["message_id"]
            agent_id = arguments["agent_id"]

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
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "message_id": message_id,
                        "agent_id": agent_id,
                        "acknowledged": True,
                    },
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "message_id": message_id,
                        "agent_id": agent_id,
                        "acknowledged": False,
                        "reason": "Message not found",
                    },
                }

        except KeyError as e:
            return self._create_error_response(
                request_id, -32602, f"Missing parameter: {e}"
            )
        except Exception as e:
            return self._create_error_response(
                request_id, -32603, f"Error acknowledging message: {e}"
            )

    def _get_performance_metrics(
        self, request_id: Union[str, int, None], arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
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

            return {"jsonrpc": "2.0", "id": request_id, "result": metrics_dict}

        except Exception as e:
            return self._create_error_response(
                request_id, -32603, f"Error getting metrics: {e}"
            )

    def _list_channels(
        self, request_id: Union[str, int, None], arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
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

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"channels": channels, "total_channels": len(channels)},
            }

        except Exception as e:
            return self._create_error_response(
                request_id, -32603, f"Error listing channels: {e}"
            )

    def _handle_resource_read(
        self, request_id: Union[str, int, None], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle resource read requests."""
        uri = params.get("uri", "")

        try:
            if uri == "queue://metrics":
                metrics_dict = asdict(self.metrics)
                metrics_dict["timestamp"] = time.time()
                content = json.dumps(metrics_dict, indent=2)

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "contents": [
                            {
                                "uri": uri,
                                "mimeType": "application/json",
                                "text": content,
                            }
                        ]
                    },
                }

            elif uri == "queue://channels":
                channels_data = {}
                # Include all channels with either messages or subscriptions
                all_channels = set(self.messages.keys()) | set(
                    self.subscriptions.keys()
                )
                for channel_name in all_channels:
                    channels_data[channel_name] = {
                        "subscribers": [
                            sub.agent_id
                            for sub in self.subscriptions.get(channel_name, [])
                        ],
                        "message_count": len(self.messages.get(channel_name, [])),
                    }

                content = json.dumps(channels_data, indent=2)

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "contents": [
                            {
                                "uri": uri,
                                "mimeType": "application/json",
                                "text": content,
                            }
                        ]
                    },
                }

            else:
                return self._create_error_response(
                    request_id, -32602, f"Unknown resource: {uri}"
                )

        except Exception as e:
            return self._create_error_response(
                request_id, -32603, f"Error reading resource: {e}"
            )

    def _handle_resource_list(
        self, request_id: Union[str, int, None]
    ) -> Dict[str, Any]:
        """Handle resource list requests."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"resources": self.capabilities["resources"]},
        }

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

    def _create_error_response(
        self, request_id: Union[str, int, None], code: int, message: str
    ) -> Dict[str, Any]:
        """Create a JSON-RPC error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message},
        }


async def main():
    """Main entry point for standalone server."""
    server = MessageQueueServer()
    await server.start()

    try:
        # Read from stdin, write to stdout (MCP protocol)
        while True:
            line = await asyncio.get_event_loop().run_in_executor(
                None, sys.stdin.readline
            )
            if not line:
                break

            try:
                request = json.loads(line.strip())
                response = server.handle_request(request)
                print(json.dumps(response), flush=True)
            except json.JSONDecodeError:
                error_response = server._create_error_response(
                    None, -32700, "Parse error"
                )
                print(json.dumps(error_response), flush=True)

    except KeyboardInterrupt:
        pass
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
