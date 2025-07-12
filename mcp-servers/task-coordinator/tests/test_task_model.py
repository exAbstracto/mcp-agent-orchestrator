"""
Tests for Task model - TDD implementation
"""

import pytest
from datetime import datetime, timezone
from typing import List, Set

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.task import Task, TaskStatus
from src.models.dependency import Dependency


class TestTask:
    """Test cases for Task model"""

    def test_task_creation_with_basic_attributes(self):
        """Test creating a task with basic attributes"""
        task = Task(
            id="task-1",
            title="Test Task",
            description="A test task",
            status=TaskStatus.PENDING,
            priority=1
        )
        
        assert task.id == "task-1"
        assert task.title == "Test Task"
        assert task.description == "A test task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == 1
        assert isinstance(task.created_at, datetime)
        assert task.dependencies == []
        assert task.dependent_tasks == []

    def test_task_creation_with_dependencies(self):
        """Test creating a task with dependencies"""
        dependencies = ["task-2", "task-3"]
        task = Task(
            id="task-1",
            title="Test Task",
            description="A test task",
            status=TaskStatus.PENDING,
            priority=1,
            dependencies=dependencies
        )
        
        assert task.dependencies == dependencies

    def test_task_status_enum(self):
        """Test TaskStatus enum values"""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.BLOCKED == "blocked"
        assert TaskStatus.CANCELLED == "cancelled"

    def test_task_add_dependency(self):
        """Test adding a dependency to a task"""
        task = Task(
            id="task-1",
            title="Test Task",
            description="A test task",
            status=TaskStatus.PENDING,
            priority=1
        )
        
        task.add_dependency("task-2")
        
        assert "task-2" in task.dependencies
        assert len(task.dependencies) == 1

    def test_task_remove_dependency(self):
        """Test removing a dependency from a task"""
        task = Task(
            id="task-1",
            title="Test Task",
            description="A test task",
            status=TaskStatus.PENDING,
            priority=1,
            dependencies=["task-2", "task-3"]
        )
        
        task.remove_dependency("task-2")
        
        assert "task-2" not in task.dependencies
        assert "task-3" in task.dependencies
        assert len(task.dependencies) == 1

    def test_task_has_dependency(self):
        """Test checking if a task has a specific dependency"""
        task = Task(
            id="task-1",
            title="Test Task",
            description="A test task",
            status=TaskStatus.PENDING,
            priority=1,
            dependencies=["task-2", "task-3"]
        )
        
        assert task.has_dependency("task-2")
        assert task.has_dependency("task-3")
        assert not task.has_dependency("task-4")

    def test_task_add_dependent_task(self):
        """Test adding a dependent task"""
        task = Task(
            id="task-1",
            title="Test Task",
            description="A test task",
            status=TaskStatus.PENDING,
            priority=1
        )
        
        task.add_dependent_task("task-2")
        
        assert "task-2" in task.dependent_tasks
        assert len(task.dependent_tasks) == 1

    def test_task_is_blocked(self):
        """Test checking if a task is blocked"""
        # Task with no dependencies should not be blocked
        task = Task(
            id="task-1",
            title="Test Task",
            description="A test task",
            status=TaskStatus.PENDING,
            priority=1
        )
        
        assert not task.is_blocked()

        # Task with dependencies should be blocked
        task.add_dependency("task-2")
        assert task.is_blocked()

    def test_task_can_start(self):
        """Test checking if a task can start (no unresolved dependencies)"""
        task = Task(
            id="task-1",
            title="Test Task",
            description="A test task",
            status=TaskStatus.PENDING,
            priority=1
        )
        
        # Task with no dependencies can start
        assert task.can_start()

        # Task with dependencies cannot start
        task.add_dependency("task-2")
        assert not task.can_start()

    def test_task_update_status(self):
        """Test updating task status"""
        task = Task(
            id="task-1",
            title="Test Task",
            description="A test task",
            status=TaskStatus.PENDING,
            priority=1
        )
        
        task.update_status(TaskStatus.IN_PROGRESS)
        
        assert task.status == TaskStatus.IN_PROGRESS
        assert isinstance(task.updated_at, datetime)

    def test_task_serialization(self):
        """Test task serialization to dictionary"""
        task = Task(
            id="task-1",
            title="Test Task",
            description="A test task",
            status=TaskStatus.PENDING,
            priority=1,
            dependencies=["task-2"]
        )
        
        task_dict = task.to_dict()
        
        assert task_dict["id"] == "task-1"
        assert task_dict["title"] == "Test Task"
        assert task_dict["description"] == "A test task"
        assert task_dict["status"] == "pending"
        assert task_dict["priority"] == 1
        assert task_dict["dependencies"] == ["task-2"]
        assert "created_at" in task_dict
        assert "updated_at" in task_dict

    def test_task_deserialization(self):
        """Test task deserialization from dictionary"""
        task_dict = {
            "id": "task-1",
            "title": "Test Task",
            "description": "A test task",
            "status": "pending",
            "priority": 1,
            "dependencies": ["task-2"],
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z"
        }
        
        task = Task.from_dict(task_dict)
        
        assert task.id == "task-1"
        assert task.title == "Test Task"
        assert task.description == "A test task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == 1
        assert task.dependencies == ["task-2"] 