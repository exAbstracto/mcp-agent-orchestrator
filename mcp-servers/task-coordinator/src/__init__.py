"""
Task Coordinator MCP Server

This package provides task coordination and dependency management capabilities
for the multi-agent development system.
"""

# MCP Server implementation using official MCP SDK
from .task_coordinator_server_sdk import TaskCoordinatorServerSDK, create_task_coordinator_server

# Default implementation
TaskCoordinatorServer = TaskCoordinatorServerSDK

from .models.task import Task, TaskStatus
from .models.dependency import Dependency, DependencyGraph

__all__ = [
    "TaskCoordinatorServer",
    "TaskCoordinatorServerSDK", 
    "create_task_coordinator_server",
    "Task",
    "TaskStatus",
    "Dependency",
    "DependencyGraph",
]
