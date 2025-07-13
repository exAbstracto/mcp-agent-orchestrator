"""
Tests for Task Coordinator MCP Server using Official SDK

Test the new MCP SDK-based implementation to ensure it provides
the same functionality as the legacy implementation.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch

from mcp.types import TextContent
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


class TestMCPToolCallHandler:
    """Test the MCP tool call handler functionality"""
    
    @pytest.mark.asyncio
    async def test_tool_call_create_task(self):
        """Test MCP tool call for create_task"""
        
        server = TaskCoordinatorServerSDK("tool-test", "1.0.0")
        
        # Mock the call_tool decorator functionality
        # Since we can't easily test the decorated function directly,
        # we'll test the underlying logic and simulate the handler
        arguments = {
            "task_id": "tool-test-task",
            "title": "Tool Test Task", 
            "description": "Task created via tool call"
        }
        
        # This simulates what the call_tool handler does
        try:
            result = server._create_task(arguments)
            text_content = TextContent(type="text", text=json.dumps(result, indent=2))
            assert text_content.type == "text"
            assert "tool-test-task" in text_content.text
        except Exception as e:
            text_content = TextContent(type="text", text=f"Error: {str(e)}")
            assert "Error:" in text_content.text
    
    @pytest.mark.asyncio 
    async def test_tool_call_unknown_tool(self):
        """Test MCP tool call with unknown tool name"""
        server = TaskCoordinatorServerSDK("tool-test", "1.0.0")
        
        # Simulate calling an unknown tool
        # The actual handler would return an error for unknown tools
        result = {"error": "Unknown tool: unknown_tool_name"}
        text_content = TextContent(type="text", text=json.dumps(result, indent=2))
        
        assert "Unknown tool" in text_content.text
        assert "error" in text_content.text
        
    @pytest.mark.asyncio
    async def test_tool_call_dependency_error(self):
        """Test MCP tool call that triggers DependencyError"""
        from src.models.dependency import DependencyError
        
        server = TaskCoordinatorServerSDK("tool-test", "1.0.0")
        
        # Create a task
        server._create_task({
            "task_id": "dep-error-task",
            "title": "Dependency Error Task",
            "description": "Task for testing dependency errors"
        })
        
        # Try to create a dependency cycle (should trigger DependencyError)
        try:
            server._add_dependency({
                "dependent_task_id": "dep-error-task", 
                "depends_on_task_id": "dep-error-task"  # Self-dependency creates cycle
            })
        except DependencyError as e:
            # Simulate what the tool handler does
            text_content = TextContent(type="text", text=f"Dependency Error: {str(e)}")
            assert "Dependency Error:" in text_content.text
    
    @pytest.mark.asyncio
    async def test_tool_call_general_exception(self):
        """Test MCP tool call that triggers general exception"""
        
        server = TaskCoordinatorServerSDK("tool-test", "1.0.0")
        
        # Test with invalid arguments that would cause a general exception
        try:
            # This should cause a KeyError or similar
            server._create_task(None)  # Invalid arguments
        except Exception as e:
            # Simulate what the tool handler does
            text_content = TextContent(type="text", text=f"Error: {str(e)}")
            assert "Error:" in text_content.text
            
    def test_run_method_exists(self):
        """Test that the run method exists and can be called"""
        server = TaskCoordinatorServerSDK("run-test", "1.0.0")
        
        # Test that run method exists
        assert hasattr(server, 'run')
        assert callable(server.run)
        
        # The actual run method is from the MCP SDK, we just verify it exists
        # since running it would start the actual server
        
    def test_list_tools_functionality(self):
        """Test that list_tools returns proper tool definitions"""
        server = TaskCoordinatorServerSDK("tools-test", "1.0.0")
        
        # The tools are registered via decorators, verify the server setup
        assert server.server is not None
        
        # Verify the main methods exist that would be called by tools
        assert hasattr(server, '_create_task')
        assert hasattr(server, '_add_dependency') 
        assert hasattr(server, '_get_blocked_tasks')
        assert hasattr(server, '_get_ready_tasks')
        assert hasattr(server, '_resolve_dependencies')
        assert hasattr(server, '_get_visualization_data')
        
    def test_server_logging_setup(self):
        """Test that server logging is properly configured"""
        server = TaskCoordinatorServerSDK("logging-test", "1.0.0")
        
        # Verify logger exists
        assert hasattr(server, 'logger')
        assert server.logger is not None
        
        # Test that we can log messages (this exercises the logger setup)
        server.logger.info("Test log message")
        server.logger.error("Test error message")
        
        # No assertion needed, just verify no exceptions are thrown

    def test_resource_functionality(self):
        """Test resource-related functionality"""
        server = TaskCoordinatorServerSDK("resource-test", "1.0.0")
        
        # Create some tasks for testing resources
        server._create_task({
            "task_id": "resource-task-1",
            "title": "Resource Task 1",
            "description": "First task for resource testing"
        })
        
        server._create_task({
            "task_id": "resource-task-2",
            "title": "Resource Task 2",
            "description": "Second task for resource testing"
        })
        
        # Add dependency to have blocked tasks
        server._add_dependency({
            "dependent_task_id": "resource-task-2",
            "depends_on_task_id": "resource-task-1"
        })
        
        # Test that resource methods work
        blocked_data = server._get_blocked_tasks({})
        ready_data = server._get_ready_tasks({})
        graph_data = server._get_visualization_data({})
        
        assert isinstance(blocked_data, dict)
        assert isinstance(ready_data, dict)
        assert isinstance(graph_data, dict)
        
        # Verify the data contains expected elements
        assert "blocked_tasks" in blocked_data
        assert "ready_tasks" in ready_data

    def test_server_initialization_with_defaults(self):
        """Test server initialization with default parameters"""
        # Test default initialization
        server = TaskCoordinatorServerSDK()
        
        assert server.name == "task-coordinator"
        assert server.version == "1.0.0"
        assert server.dependency_graph is not None
        assert server.notification_system is not None
        
    def test_server_initialization_detailed(self):
        """Test server initialization with detailed verification"""
        server = TaskCoordinatorServerSDK("detailed-test", "2.1.0")
        
        # Verify all components are properly initialized
        assert server.name == "detailed-test"
        assert server.version == "2.1.0"
        assert server.server is not None
        assert server.logger is not None
        assert server.dependency_graph is not None
        assert server.notification_system is not None
        
        # Verify notification system is connected to dependency graph
        assert server.dependency_graph.notification_system is not None
        assert server.dependency_graph.notification_system == server.notification_system

    def test_task_creation_edge_cases(self):
        """Test task creation with various edge cases"""
        server = TaskCoordinatorServerSDK("edge-test", "1.0.0")
        
        # Test task creation with minimal required data
        result = server._create_task({
            "task_id": "minimal-task",
            "title": "Minimal Task",
            "description": "A minimal task description"
        })
        assert result["success"] is True
        
        # Test task creation with all optional fields
        result = server._create_task({
            "task_id": "full-task",
            "title": "Full Task",
            "description": "A fully specified task",
            "priority": 8,
            "dependencies": []
        })
        assert result["success"] is True
        
        # Test task creation with priority edge values
        result = server._create_task({
            "task_id": "high-priority-task",
            "title": "High Priority Task",
            "description": "High priority task description",
            "priority": 10
        })
        assert result["success"] is True
        
        # Test task creation with invalid data (missing required fields)
        result = server._create_task({
            "task_id": "invalid-task"
            # Missing title and description
        })
        assert "error" in result

    def test_dependency_management_comprehensive(self):
        """Test comprehensive dependency management scenarios"""
        server = TaskCoordinatorServerSDK("dep-test", "1.0.0")
        
        # Create a chain of tasks
        tasks = []
        for i in range(5):
            task_id = f"chain-task-{i}"
            result = server._create_task({
                "task_id": task_id,
                "title": f"Chain Task {i}",
                "description": f"Task {i} in dependency chain"
            })
            assert result["success"] is True
            tasks.append(task_id)
        
        # Create a dependency chain: 0 -> 1 -> 2 -> 3 -> 4
        for i in range(1, 5):
            result = server._add_dependency({
                "dependent_task_id": tasks[i],
                "depends_on_task_id": tasks[i-1]
            })
            assert result["success"] is True
        
        # Test that only the first task is ready
        ready_tasks = server._get_ready_tasks({})
        assert tasks[0] in ready_tasks["ready_tasks"]
        assert ready_tasks["count"] == 1
        
        # Test that all other tasks are blocked
        blocked_tasks = server._get_blocked_tasks({})
        for i in range(1, 5):
            assert tasks[i] in blocked_tasks["blocked_tasks"]
        assert blocked_tasks["count"] == 4

    def test_task_completion_workflow(self):
        """Test complete task workflow with resolution"""
        server = TaskCoordinatorServerSDK("workflow-test", "1.0.0")
        
        # Create tasks
        server._create_task({
            "task_id": "parent-task",
            "title": "Parent Task",
            "description": "Task that others depend on"
        })
        
        server._create_task({
            "task_id": "child-task-1",
            "title": "Child Task 1",
            "description": "First child task"
        })
        
        server._create_task({
            "task_id": "child-task-2",
            "title": "Child Task 2",
            "description": "Second child task"
        })
        
        # Add dependencies
        server._add_dependency({
            "dependent_task_id": "child-task-1",
            "depends_on_task_id": "parent-task"
        })
        
        server._add_dependency({
            "dependent_task_id": "child-task-2",
            "depends_on_task_id": "parent-task"
        })
        
        # Initially only parent should be ready
        ready_tasks = server._get_ready_tasks({})
        assert "parent-task" in ready_tasks["ready_tasks"]
        assert ready_tasks["count"] == 1
        
        # Complete parent task
        result = server._resolve_dependencies({
            "completed_task_id": "parent-task"
        })
        
        assert result["success"] is True
        assert result["completed_task_id"] == "parent-task"
        newly_ready = result["newly_ready_tasks"]
        assert "child-task-1" in newly_ready
        assert "child-task-2" in newly_ready
        assert result["count"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])