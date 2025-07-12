"""
Notification system for dependency resolution events
"""

from datetime import datetime, timezone
from typing import Dict, List, Callable, Any, Optional


class NotificationEvent:
    """Event object for notifications"""

    def __init__(
        self,
        event_type: str,
        task_id: str,
        newly_ready_tasks: List[str],
        timestamp: Optional[datetime] = None,
    ):
        self.event_type = event_type
        self.task_id = task_id
        self.newly_ready_tasks = newly_ready_tasks
        self.timestamp = timestamp or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            "event_type": self.event_type,
            "task_id": self.task_id,
            "newly_ready_tasks": self.newly_ready_tasks,
            "timestamp": self.timestamp.isoformat(),
        }

    def __eq__(self, other):
        if not isinstance(other, NotificationEvent):
            return False
        return (
            self.event_type == other.event_type
            and self.task_id == other.task_id
            and self.newly_ready_tasks == other.newly_ready_tasks
            and self.timestamp == other.timestamp
        )


# Type alias for callback functions
NotificationCallback = Callable[[NotificationEvent], None]


class NotificationSystem:
    """
    Notification system for handling dependency resolution events
    """

    def __init__(self):
        self.callbacks: Dict[str, List[NotificationCallback]] = {}
        self.event_history: List[NotificationEvent] = []

    def register_callback(
        self, event_type: str, callback: NotificationCallback
    ) -> None:
        """
        Register a callback for a specific event type

        Args:
            event_type: The type of event to listen for
            callback: The callback function to execute
        """
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []

        if callback not in self.callbacks[event_type]:
            self.callbacks[event_type].append(callback)

    def unregister_callback(
        self, event_type: str, callback: NotificationCallback
    ) -> None:
        """
        Unregister a callback for a specific event type

        Args:
            event_type: The type of event to stop listening for
            callback: The callback function to remove
        """
        if event_type in self.callbacks:
            if callback in self.callbacks[event_type]:
                self.callbacks[event_type].remove(callback)

    def notify(self, event_type: str, event: NotificationEvent) -> None:
        """
        Notify all registered callbacks for an event type

        Args:
            event_type: The type of event that occurred
            event: The event data
        """
        # Store event in history
        self.event_history.append(event)

        # Notify all registered callbacks
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    # Log error but don't stop other callbacks
                    print(f"Error in notification callback: {e}")

    def get_event_history(self) -> List[NotificationEvent]:
        """Get the event history"""
        return list(self.event_history)

    def clear_event_history(self) -> None:
        """Clear the event history"""
        self.event_history.clear()
