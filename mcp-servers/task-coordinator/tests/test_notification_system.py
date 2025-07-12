"""
Tests for notification system when dependencies are resolved - TDD implementation
"""

import pytest
from typing import List, Dict, Any, Callable
from unittest.mock import Mock, call

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.task import Task, TaskStatus
from src.models.dependency import DependencyGraph
from src.notification_system import NotificationSystem, NotificationEvent, NotificationCallback


class TestNotificationSystem:
    """Test cases for the notification system"""

    def test_notification_system_creation(self):
        """Test creating a notification system"""
        notification_system = NotificationSystem()
        
        assert notification_system.callbacks == {}
        assert notification_system.event_history == []

    def test_register_callback(self):
        """Test registering a callback for dependency resolution"""
        notification_system = NotificationSystem()
        callback = Mock()
        
        notification_system.register_callback("dependency_resolved", callback)
        
        assert "dependency_resolved" in notification_system.callbacks
        assert callback in notification_system.callbacks["dependency_resolved"]

    def test_register_multiple_callbacks(self):
        """Test registering multiple callbacks for the same event"""
        notification_system = NotificationSystem()
        callback1 = Mock()
        callback2 = Mock()
        
        notification_system.register_callback("dependency_resolved", callback1)
        notification_system.register_callback("dependency_resolved", callback2)
        
        assert len(notification_system.callbacks["dependency_resolved"]) == 2
        assert callback1 in notification_system.callbacks["dependency_resolved"]
        assert callback2 in notification_system.callbacks["dependency_resolved"]

    def test_unregister_callback(self):
        """Test unregistering a callback"""
        notification_system = NotificationSystem()
        callback = Mock()
        
        notification_system.register_callback("dependency_resolved", callback)
        notification_system.unregister_callback("dependency_resolved", callback)
        
        assert callback not in notification_system.callbacks.get("dependency_resolved", [])

    def test_notify_dependency_resolved(self):
        """Test notifying when a dependency is resolved"""
        notification_system = NotificationSystem()
        callback = Mock()
        
        notification_system.register_callback("dependency_resolved", callback)
        
        event = NotificationEvent(
            event_type="dependency_resolved",
            task_id="task-1",
            newly_ready_tasks=["task-2", "task-3"],
            timestamp=None
        )
        
        notification_system.notify("dependency_resolved", event)
        
        callback.assert_called_once_with(event)

    def test_notify_multiple_callbacks(self):
        """Test that all registered callbacks are notified"""
        notification_system = NotificationSystem()
        callback1 = Mock()
        callback2 = Mock()
        
        notification_system.register_callback("dependency_resolved", callback1)
        notification_system.register_callback("dependency_resolved", callback2)
        
        event = NotificationEvent(
            event_type="dependency_resolved",
            task_id="task-1",
            newly_ready_tasks=["task-2"],
            timestamp=None
        )
        
        notification_system.notify("dependency_resolved", event)
        
        callback1.assert_called_once_with(event)
        callback2.assert_called_once_with(event)

    def test_notify_with_no_callbacks(self):
        """Test that notify works even when no callbacks are registered"""
        notification_system = NotificationSystem()
        
        event = NotificationEvent(
            event_type="dependency_resolved",
            task_id="task-1",
            newly_ready_tasks=["task-2"],
            timestamp=None
        )
        
        # Should not raise an exception
        notification_system.notify("dependency_resolved", event)

    def test_event_history_tracking(self):
        """Test that notification events are stored in history"""
        notification_system = NotificationSystem()
        callback = Mock()
        
        notification_system.register_callback("dependency_resolved", callback)
        
        event = NotificationEvent(
            event_type="dependency_resolved",
            task_id="task-1",
            newly_ready_tasks=["task-2"],
            timestamp=None
        )
        
        notification_system.notify("dependency_resolved", event)
        
        assert len(notification_system.event_history) == 1
        assert notification_system.event_history[0] == event

    def test_get_event_history(self):
        """Test getting event history"""
        notification_system = NotificationSystem()
        
        event1 = NotificationEvent(
            event_type="dependency_resolved",
            task_id="task-1",
            newly_ready_tasks=["task-2"],
            timestamp=None
        )
        
        event2 = NotificationEvent(
            event_type="dependency_resolved",
            task_id="task-2",
            newly_ready_tasks=["task-3"],
            timestamp=None
        )
        
        notification_system.notify("dependency_resolved", event1)
        notification_system.notify("dependency_resolved", event2)
        
        history = notification_system.get_event_history()
        
        assert len(history) == 2
        assert event1 in history
        assert event2 in history

    def test_clear_event_history(self):
        """Test clearing event history"""
        notification_system = NotificationSystem()
        
        event = NotificationEvent(
            event_type="dependency_resolved",
            task_id="task-1",
            newly_ready_tasks=["task-2"],
            timestamp=None
        )
        
        notification_system.notify("dependency_resolved", event)
        assert len(notification_system.event_history) == 1
        
        notification_system.clear_event_history()
        assert len(notification_system.event_history) == 0


class TestNotificationEvent:
    """Test cases for NotificationEvent"""

    def test_notification_event_creation(self):
        """Test creating a notification event"""
        event = NotificationEvent(
            event_type="dependency_resolved",
            task_id="task-1",
            newly_ready_tasks=["task-2", "task-3"],
            timestamp=None
        )
        
        assert event.event_type == "dependency_resolved"
        assert event.task_id == "task-1"
        assert event.newly_ready_tasks == ["task-2", "task-3"]
        assert event.timestamp is not None

    def test_notification_event_with_custom_timestamp(self):
        """Test creating a notification event with custom timestamp"""
        from datetime import datetime, timezone
        
        custom_timestamp = datetime.now(timezone.utc)
        event = NotificationEvent(
            event_type="dependency_resolved",
            task_id="task-1",
            newly_ready_tasks=["task-2"],
            timestamp=custom_timestamp
        )
        
        assert event.timestamp == custom_timestamp

    def test_notification_event_to_dict(self):
        """Test converting notification event to dictionary"""
        event = NotificationEvent(
            event_type="dependency_resolved",
            task_id="task-1",
            newly_ready_tasks=["task-2", "task-3"],
            timestamp=None
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["event_type"] == "dependency_resolved"
        assert event_dict["task_id"] == "task-1"
        assert event_dict["newly_ready_tasks"] == ["task-2", "task-3"]
        assert "timestamp" in event_dict


class TestIntegratedNotificationSystem:
    """Test integration between DependencyGraph and NotificationSystem"""

    def test_dependency_graph_with_notification_system(self):
        """Test that dependency graph can work with notification system"""
        graph = DependencyGraph()
        notification_system = NotificationSystem()
        callback = Mock()
        
        notification_system.register_callback("dependency_resolved", callback)
        
        # Set up notification system in graph
        graph.set_notification_system(notification_system)
        
        # Create tasks
        task1 = Task(id="task-1", title="Task 1", description="First task")
        task2 = Task(id="task-2", title="Task 2", description="Second task")
        
        graph.add_task(task1)
        graph.add_task(task2)
        graph.add_dependency("task-2", "task-1")
        
        # Complete task-1 - should trigger notification
        task1.update_status(TaskStatus.COMPLETED)
        newly_ready = graph.resolve_dependencies("task-1")
        
        # Check that callback was called
        callback.assert_called_once()
        
        # Check the event details
        call_args = callback.call_args[0][0]
        assert call_args.event_type == "dependency_resolved"
        assert call_args.task_id == "task-1"
        assert "task-2" in call_args.newly_ready_tasks

    def test_notification_system_callback_signature(self):
        """Test that notification callback receives correct information"""
        def test_callback(event: NotificationEvent):
            assert event.event_type == "dependency_resolved"
            assert event.task_id == "task-1"
            assert len(event.newly_ready_tasks) > 0
            assert event.timestamp is not None
        
        graph = DependencyGraph()
        notification_system = NotificationSystem()
        
        notification_system.register_callback("dependency_resolved", test_callback)
        graph.set_notification_system(notification_system)
        
        # Create tasks
        task1 = Task(id="task-1", title="Task 1", description="First task")
        task2 = Task(id="task-2", title="Task 2", description="Second task")
        
        graph.add_task(task1)
        graph.add_task(task2)
        graph.add_dependency("task-2", "task-1")
        
        # Complete task-1 - should trigger notification
        task1.update_status(TaskStatus.COMPLETED)
        graph.resolve_dependencies("task-1")
        
        # If we get here without assertion errors, the callback received correct data 