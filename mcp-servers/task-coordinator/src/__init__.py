"""
Task Coordinator MCP Server

This package provides task coordination and dependency management capabilities
for the multi-agent development system.
"""

from .task_coordinator_server import TaskCoordinatorServer
from .models.task import Task, TaskStatus
from .models.dependency import Dependency, DependencyGraph

__all__ = [
    "TaskCoordinatorServer",
    "Task",
    "TaskStatus",
    "Dependency",
    "DependencyGraph",
]
