"""
Tests for Task Coordinator MCP Server using Official SDK

Test the new MCP SDK-based implementation to ensure it provides
the same functionality as the legacy implementation.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch

from src.task_coordinator_server_sdk import TaskCoordinatorServerSDK, create_task_coordinator_server


class TestTaskCoordinatorServerSDK:
    """Test cases for the MCP SDK-based task coordinator server"""
    
    def test_server_initialization(self):
        """Test that the server initializes correctly"""
        server = TaskCoordinatorServerSDK("test-coordinator", "1.0.0")
        
        assert server.name == "test-coordinator"
        assert server.version == "1.0.0"
        assert server.server is not None
        assert server.dependency_graph is not None
        
    def test_factory_function(self):
        """Test the factory function creates server correctly"""
        server = create_task_coordinator_server("factory-test", "2.0.0")
        
        assert isinstance(server, TaskCoordinatorServerSDK)
        assert server.name == "factory-test"
        assert server.version == "2.0.0"
        
    def test_factory_function_defaults(self):
        """Test the factory function with default parameters"""
        server = create_task_coordinator_server()
        
        assert isinstance(server, TaskCoordinatorServerSDK)
        assert server.name == "task-coordinator"
        assert server.version == "1.0.0"
    
    def test_create_task_functionality(self):
        """Test the create task functionality"""
        server = TaskCoordinatorServerSDK("test-coordinator", "1.0.0")
        
        # Test creating a task
        result = server._create_task({
            "task_id": "test-task-1",
            "title": "Test Task",
            "description": "A test task",
            "priority": 5,
            "dependencies": []
        })
        
        assert result["success"] is True
        assert result["task_id"] == "test-task-1"
        assert "message" in result
    
    def test_add_dependency_functionality(self):
        """Test the add dependency functionality"""
        server = TaskCoordinatorServerSDK("test-coordinator", "1.0.0")
        
        # Create two tasks first
        server._create_task({
            "task_id": "task-1",
            "title": "First Task",
            "description": "First task"
        })
        
        server._create_task({
            "task_id": "task-2", 
            "title": "Second Task",
            "description": "Second task"
        })
        
        # Add dependency
        result = server._add_dependency({
            "dependent_task_id": "task-2",
            "depends_on_task_id": "task-1"
        })
        
        assert result["success"] is True
        assert "message" in result
    
    def test_get_blocked_tasks_functionality(self):
        """Test the get blocked tasks functionality"""
        server = TaskCoordinatorServerSDK("test-coordinator", "1.0.0")
        
        # Create tasks with dependencies
        server._create_task({
            "task_id": "task-1",
            "title": "First Task",
            "description": "First task"
        })
        
        server._create_task({
            "task_id": "task-2",
            "title": "Second Task", 
            "description": "Second task"
        })
        
        server._add_dependency({
            "dependent_task_id": "task-2",
            "depends_on_task_id": "task-1"
        })
        
        # Get blocked tasks
        result = server._get_blocked_tasks({})
        
        assert "blocked_tasks" in result
        assert "count" in result
        assert isinstance(result["blocked_tasks"], list)
    
    def test_get_ready_tasks_functionality(self):
        """Test the get ready tasks functionality"""
        server = TaskCoordinatorServerSDK("test-coordinator", "1.0.0")
        
        # Create a task without dependencies
        server._create_task({
            "task_id": "ready-task",
            "title": "Ready Task",
            "description": "A task ready to run"
        })
        
        # Get ready tasks
        result = server._get_ready_tasks({})
        
        assert "ready_tasks" in result
        assert "count" in result
        assert isinstance(result["ready_tasks"], list)
        # Should have at least our ready task
        assert result["count"] >= 1
    
    def test_resolve_dependencies_functionality(self):
        """Test the resolve dependencies functionality"""
        server = TaskCoordinatorServerSDK("test-coordinator", "1.0.0")
        
        # Create tasks with dependencies
        server._create_task({
            "task_id": "task-1",
            "title": "First Task",
            "description": "First task"
        })
        
        server._create_task({
            "task_id": "task-2",
            "title": "Second Task",
            "description": "Second task"
        })
        
        server._add_dependency({
            "dependent_task_id": "task-2",
            "depends_on_task_id": "task-1"
        })
        
        # Resolve dependencies for task-1
        result = server._resolve_dependencies({
            "completed_task_id": "task-1"
        })
        
        assert result["success"] is True
        assert result["completed_task_id"] == "task-1"
        assert "newly_ready_tasks" in result
        assert "count" in result
    
    def test_get_visualization_data_functionality(self):
        """Test the get visualization data functionality"""
        server = TaskCoordinatorServerSDK("test-coordinator", "1.0.0")
        
        # Create some tasks to visualize
        server._create_task({
            "task_id": "vis-task-1",
            "title": "Visualization Task 1",
            "description": "First task for visualization"
        })
        
        # Get visualization data
        result = server._get_visualization_data({})
        
        # Should return some visualization data structure
        assert isinstance(result, dict)
    
    def test_server_has_run_method(self):
        """Test server has run method for MCP SDK"""
        server = TaskCoordinatorServerSDK("test-coordinator", "1.0.0")
        
        # Test that run method exists
        assert hasattr(server, 'run')
        assert callable(getattr(server, 'run'))
    
    def test_server_tools_registration(self):
        """Test that tools are registered correctly"""
        server = TaskCoordinatorServerSDK("test-coordinator", "1.0.0")
        
        # Verify server has the MCP server instance
        assert server.server is not None
        
        # The tools are registered via decorators, so we can't easily test them
        # without actually running the server, but we can verify the methods exist
        assert hasattr(server, '_create_task')
        assert hasattr(server, '_add_dependency')
        assert hasattr(server, '_get_blocked_tasks')
        assert hasattr(server, '_get_ready_tasks')
        assert hasattr(server, '_resolve_dependencies')
        assert hasattr(server, '_get_visualization_data')


class TestSDKTaskCoordinatorIntegration:
    """Test integration between SDK wrapper and legacy task coordinator"""
    
    def test_complete_task_workflow(self):
        """Test complete task coordination workflow"""
        server = TaskCoordinatorServerSDK("integration-test", "1.0.0")
        
        # Create multiple tasks with dependencies
        server._create_task({
            "task_id": "workflow-task-1",
            "title": "Workflow Task 1",
            "description": "First task in workflow",
            "priority": 10
        })
        
        server._create_task({
            "task_id": "workflow-task-2",
            "title": "Workflow Task 2", 
            "description": "Second task in workflow",
            "priority": 5
        })
        
        server._create_task({
            "task_id": "workflow-task-3",
            "title": "Workflow Task 3",
            "description": "Third task in workflow",
            "priority": 1
        })
        
        # Add dependencies: task-2 depends on task-1, task-3 depends on task-2
        server._add_dependency({
            "dependent_task_id": "workflow-task-2",
            "depends_on_task_id": "workflow-task-1"
        })
        
        server._add_dependency({
            "dependent_task_id": "workflow-task-3",
            "depends_on_task_id": "workflow-task-2"
        })
        
        # Initially, only task-1 should be ready
        ready_tasks = server._get_ready_tasks({})
        ready_task_ids = ready_tasks["ready_tasks"]  # These are strings, not objects
        assert "workflow-task-1" in ready_task_ids
        
        # Tasks 2 and 3 should be blocked
        blocked_tasks = server._get_blocked_tasks({})
        blocked_task_ids = blocked_tasks["blocked_tasks"]  # These are strings, not objects
        assert "workflow-task-2" in blocked_task_ids
        assert "workflow-task-3" in blocked_task_ids
        
        # Complete task-1
        resolve_result = server._resolve_dependencies({
            "completed_task_id": "workflow-task-1"
        })
        
        assert resolve_result["success"] is True
        newly_ready = resolve_result["newly_ready_tasks"]  # These are strings, not objects
        assert "workflow-task-2" in newly_ready
        
        # Now task-2 should be ready, but task-3 still blocked
        ready_tasks = server._get_ready_tasks({})
        ready_task_ids = ready_tasks["ready_tasks"]  # These are strings, not objects
        assert "workflow-task-2" in ready_task_ids
        
        blocked_tasks = server._get_blocked_tasks({})
        blocked_task_ids = blocked_tasks["blocked_tasks"]  # These are strings, not objects
        assert "workflow-task-3" in blocked_task_ids
    
    def test_error_handling(self):
        """Test error handling in the SDK wrapper"""
        server = TaskCoordinatorServerSDK("error-test", "1.0.0")
        
        # Test creating task with missing required fields
        result = server._create_task({
            # Missing task_id and title
            "description": "Task without required fields"
        })
        
        # Should return an error
        assert "error" in result
        
        # Test adding dependency for non-existent tasks
        result = server._add_dependency({
            "dependent_task_id": "non-existent-1",
            "depends_on_task_id": "non-existent-2"
        })
        
        # Should return an error
        assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])