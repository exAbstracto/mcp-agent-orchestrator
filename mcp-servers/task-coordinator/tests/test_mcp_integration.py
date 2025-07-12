"""
Tests for MCP server integration with dependency management - TDD implementation
"""

import pytest
import json
from unittest.mock import Mock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.task_coordinator_server import TaskCoordinatorServer
from src.models.task import Task, TaskStatus
from src.models.dependency import DependencyGraph
from src.notification_system import NotificationSystem


class TestTaskCoordinatorMCP:
    """Test cases for TaskCoordinatorServer MCP integration"""

    def test_task_coordinator_server_initialization(self):
        """Test that the task coordinator server initializes properly"""
        server = TaskCoordinatorServer("task-coordinator", "1.0.0")
        
        assert server.name == "task-coordinator"
        assert server.version == "1.0.0"
        assert server.dependency_graph is not None
        assert server.notification_system is not None
        assert isinstance(server.dependency_graph, DependencyGraph)
        assert isinstance(server.notification_system, NotificationSystem)

    def test_register_task_coordinator_capabilities(self):
        """Test that task coordinator capabilities are registered"""
        server = TaskCoordinatorServer("task-coordinator", "1.0.0")
        
        capabilities = server.get_server_info()["capabilities"]
        
        assert "tools" in capabilities
        assert "create_task" in capabilities["tools"]
        assert "add_dependency" in capabilities["tools"]
        assert "get_blocked_tasks" in capabilities["tools"]
        assert "get_ready_tasks" in capabilities["tools"]
        assert "resolve_dependencies" in capabilities["tools"]
        assert "get_visualization_data" in capabilities["tools"]

    def test_handle_create_task_request(self):
        """Test handling create_task MCP request"""
        server = TaskCoordinatorServer("task-coordinator", "1.0.0")
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "create_task",
                "arguments": {
                    "task_id": "task-1",
                    "title": "Test Task",
                    "description": "A test task",
                    "priority": 1
                }
            }
        }
        
        response = server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["success"] is True
        assert response["result"]["task_id"] == "task-1"

    def test_handle_add_dependency_request(self):
        """Test handling add_dependency MCP request"""
        server = TaskCoordinatorServer("task-coordinator", "1.0.0")
        
        # First create tasks
        task1 = Task(id="task-1", title="Task 1", description="First task")
        task2 = Task(id="task-2", title="Task 2", description="Second task")
        
        server.dependency_graph.add_task(task1)
        server.dependency_graph.add_task(task2)
        
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "add_dependency",
                "arguments": {
                    "dependent_task_id": "task-2",
                    "depends_on_task_id": "task-1"
                }
            }
        }
        
        response = server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 2
        assert "result" in response
        assert response["result"]["success"] is True

    def test_handle_get_blocked_tasks_request(self):
        """Test handling get_blocked_tasks MCP request"""
        server = TaskCoordinatorServer("task-coordinator", "1.0.0")
        
        # Set up tasks with dependencies
        task1 = Task(id="task-1", title="Task 1", description="First task")
        task2 = Task(id="task-2", title="Task 2", description="Second task")
        
        server.dependency_graph.add_task(task1)
        server.dependency_graph.add_task(task2)
        server.dependency_graph.add_dependency("task-2", "task-1")
        
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_blocked_tasks",
                "arguments": {}
            }
        }
        
        response = server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 3
        assert "result" in response
        assert "task-2" in response["result"]["blocked_tasks"]

    def test_handle_get_ready_tasks_request(self):
        """Test handling get_ready_tasks MCP request"""
        server = TaskCoordinatorServer("task-coordinator", "1.0.0")
        
        # Set up tasks with dependencies
        task1 = Task(id="task-1", title="Task 1", description="First task")
        task2 = Task(id="task-2", title="Task 2", description="Second task")
        
        server.dependency_graph.add_task(task1)
        server.dependency_graph.add_task(task2)
        server.dependency_graph.add_dependency("task-2", "task-1")
        
        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "get_ready_tasks",
                "arguments": {}
            }
        }
        
        response = server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 4
        assert "result" in response
        assert "task-1" in response["result"]["ready_tasks"]

    def test_handle_resolve_dependencies_request(self):
        """Test handling resolve_dependencies MCP request"""
        server = TaskCoordinatorServer("task-coordinator", "1.0.0")
        
        # Set up tasks with dependencies
        task1 = Task(id="task-1", title="Task 1", description="First task")
        task2 = Task(id="task-2", title="Task 2", description="Second task")
        
        server.dependency_graph.add_task(task1)
        server.dependency_graph.add_task(task2)
        server.dependency_graph.add_dependency("task-2", "task-1")
        
        # Mark task-1 as completed
        task1.update_status(TaskStatus.COMPLETED)
        
        request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "resolve_dependencies",
                "arguments": {
                    "completed_task_id": "task-1"
                }
            }
        }
        
        response = server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 5
        assert "result" in response
        assert "task-2" in response["result"]["newly_ready_tasks"]

    def test_handle_get_visualization_data_request(self):
        """Test handling get_visualization_data MCP request"""
        server = TaskCoordinatorServer("task-coordinator", "1.0.0")
        
        # Set up tasks with dependencies
        task1 = Task(id="task-1", title="Task 1", description="First task")
        task2 = Task(id="task-2", title="Task 2", description="Second task")
        
        server.dependency_graph.add_task(task1)
        server.dependency_graph.add_task(task2)
        server.dependency_graph.add_dependency("task-2", "task-1")
        
        request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "get_visualization_data",
                "arguments": {}
            }
        }
        
        response = server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 6
        assert "result" in response
        assert "nodes" in response["result"]
        assert "edges" in response["result"]
        assert len(response["result"]["nodes"]) == 2
        assert len(response["result"]["edges"]) == 1

    def test_handle_circular_dependency_error(self):
        """Test handling circular dependency error via MCP"""
        server = TaskCoordinatorServer("task-coordinator", "1.0.0")
        
        # Set up tasks
        task1 = Task(id="task-1", title="Task 1", description="First task")
        task2 = Task(id="task-2", title="Task 2", description="Second task")
        
        server.dependency_graph.add_task(task1)
        server.dependency_graph.add_task(task2)
        server.dependency_graph.add_dependency("task-2", "task-1")
        
        # Try to create a circular dependency
        request = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "add_dependency",
                "arguments": {
                    "dependent_task_id": "task-1",
                    "depends_on_task_id": "task-2"
                }
            }
        }
        
        response = server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 7
        assert "error" in response
        assert "Circular dependency detected" in response["error"]["message"]

    def test_handle_unknown_tool_request(self):
        """Test handling unknown tool request"""
        server = TaskCoordinatorServer("task-coordinator", "1.0.0")
        
        request = {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "unknown_tool",
                "arguments": {}
            }
        }
        
        response = server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 8
        assert "error" in response
        assert response["error"]["code"] == -32601  # Method not found

    def test_notification_system_integration(self):
        """Test that notification system is properly integrated"""
        server = TaskCoordinatorServer("task-coordinator", "1.0.0")
        callback = Mock()
        
        # Register callback
        server.notification_system.register_callback("dependency_resolved", callback)
        
        # Set up tasks
        task1 = Task(id="task-1", title="Task 1", description="First task")
        task2 = Task(id="task-2", title="Task 2", description="Second task")
        
        server.dependency_graph.add_task(task1)
        server.dependency_graph.add_task(task2)
        server.dependency_graph.add_dependency("task-2", "task-1")
        
        # Complete task-1 via MCP
        task1.update_status(TaskStatus.COMPLETED)
        
        request = {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {
                "name": "resolve_dependencies",
                "arguments": {
                    "completed_task_id": "task-1"
                }
            }
        }
        
        response = server.handle_request(request)
        
        # Check that callback was called
        callback.assert_called_once()
        
        # Check response
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 9
        assert "result" in response 