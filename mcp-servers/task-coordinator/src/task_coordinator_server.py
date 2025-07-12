"""
Task Coordinator MCP Server with dependency management
"""

import json
import logging
import sys
from typing import Dict, Any, Union, List
from .models.task import Task, TaskStatus
from .models.dependency import DependencyGraph, DependencyError
from .notification_system import NotificationSystem

# Import the base MCP server from template
import os
import importlib.util

template_path = os.path.join(os.path.dirname(__file__), '..', '..', 'template', 'src', 'mcp_server.py')
spec = importlib.util.spec_from_file_location("mcp_server", template_path)
if spec is None or spec.loader is None:
    raise ImportError("Could not load MCP server template")
mcp_server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp_server)

MCPServer = mcp_server.MCPServer


class TaskCoordinatorServer(MCPServer):
    """
    Task Coordinator MCP Server with dependency management capabilities
    """
    
    def __init__(self, name: str, version: str):
        """Initialize the task coordinator server"""
        super().__init__(name, version)
        
        # Initialize dependency management components
        self.dependency_graph = DependencyGraph()
        self.notification_system = NotificationSystem()
        
        # Set up notification system in dependency graph
        self.dependency_graph.set_notification_system(self.notification_system)
        
        # Register task coordinator capabilities
        self._register_task_coordinator_capabilities()
        
        self.logger.info("Task Coordinator Server initialized")
    
    def _register_task_coordinator_capabilities(self):
        """Register task coordinator specific capabilities"""
        tools = {
            "create_task": {
                "description": "Create a new task",
                "parameters": {
                    "task_id": {"type": "string", "description": "Unique task identifier"},
                    "title": {"type": "string", "description": "Task title"},
                    "description": {"type": "string", "description": "Task description"},
                    "priority": {"type": "integer", "description": "Task priority (1-10)"},
                    "dependencies": {"type": "array", "description": "List of dependent task IDs", "items": {"type": "string"}}
                }
            },
            "add_dependency": {
                "description": "Add a dependency between tasks",
                "parameters": {
                    "dependent_task_id": {"type": "string", "description": "Task that depends on another"},
                    "depends_on_task_id": {"type": "string", "description": "Task that is depended upon"}
                }
            },
            "get_blocked_tasks": {
                "description": "Get list of blocked tasks",
                "parameters": {}
            },
            "get_ready_tasks": {
                "description": "Get list of tasks ready to start",
                "parameters": {}
            },
            "resolve_dependencies": {
                "description": "Resolve dependencies when a task is completed",
                "parameters": {
                    "completed_task_id": {"type": "string", "description": "ID of the completed task"}
                }
            },
            "get_visualization_data": {
                "description": "Get dependency graph visualization data",
                "parameters": {}
            }
        }
        
        self.register_capability("tools", tools)
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP requests including task coordinator tools"""
        # Check if it's a tools/call request
        if request.get("method") == "tools/call":
            return self._handle_tool_call(request)
        else:
            # Delegate to parent class for other requests
            return super().handle_request(request)
    
    def _handle_tool_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call requests"""
        request_id = request.get("id")
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "create_task":
                result = self._handle_create_task(arguments)
            elif tool_name == "add_dependency":
                result = self._handle_add_dependency(arguments)
            elif tool_name == "get_blocked_tasks":
                result = self._handle_get_blocked_tasks(arguments)
            elif tool_name == "get_ready_tasks":
                result = self._handle_get_ready_tasks(arguments)
            elif tool_name == "resolve_dependencies":
                result = self._handle_resolve_dependencies(arguments)
            elif tool_name == "get_visualization_data":
                result = self._handle_get_visualization_data(arguments)
            else:
                return self._create_error_response(request_id, -32601, f"Unknown tool: {tool_name}")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except DependencyError as e:
            return self._create_error_response(request_id, -32000, str(e))
        except Exception as e:
            self.logger.error(f"Error handling tool call {tool_name}: {e}")
            return self._create_error_response(request_id, -32603, "Internal error")
    
    def _handle_create_task(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create_task tool call"""
        task_id = arguments.get("task_id")
        title = arguments.get("title")
        description = arguments.get("description")
        priority = arguments.get("priority", 1)
        dependencies = arguments.get("dependencies", [])
        
        if not task_id or not title:
            raise ValueError("task_id and title are required")
        
        # Create task
        task = Task(
            id=task_id,
            title=title,
            description=description,
            priority=priority,
            dependencies=dependencies
        )
        
        # Add to dependency graph
        self.dependency_graph.add_task(task)
        
        return {
            "success": True,
            "task_id": task_id,
            "message": f"Task {task_id} created successfully"
        }
    
    def _handle_add_dependency(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle add_dependency tool call"""
        dependent_task_id = arguments.get("dependent_task_id")
        depends_on_task_id = arguments.get("depends_on_task_id")
        
        if not dependent_task_id or not depends_on_task_id:
            raise ValueError("dependent_task_id and depends_on_task_id are required")
        
        # Add dependency (this will check for cycles)
        self.dependency_graph.add_dependency(dependent_task_id, depends_on_task_id)
        
        return {
            "success": True,
            "message": f"Dependency added: {dependent_task_id} depends on {depends_on_task_id}"
        }
    
    def _handle_get_blocked_tasks(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_blocked_tasks tool call"""
        blocked_tasks = self.dependency_graph.get_blocked_tasks()
        
        return {
            "blocked_tasks": blocked_tasks,
            "count": len(blocked_tasks)
        }
    
    def _handle_get_ready_tasks(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_ready_tasks tool call"""
        ready_tasks = self.dependency_graph.get_ready_tasks()
        
        return {
            "ready_tasks": ready_tasks,
            "count": len(ready_tasks)
        }
    
    def _handle_resolve_dependencies(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resolve_dependencies tool call"""
        completed_task_id = arguments.get("completed_task_id")
        
        if not completed_task_id:
            raise ValueError("completed_task_id is required")
        
        # Resolve dependencies
        newly_ready_tasks = self.dependency_graph.resolve_dependencies(completed_task_id)
        
        return {
            "success": True,
            "completed_task_id": completed_task_id,
            "newly_ready_tasks": newly_ready_tasks,
            "count": len(newly_ready_tasks)
        }
    
    def _handle_get_visualization_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_visualization_data tool call"""
        visualization_data = self.dependency_graph.get_visualization_data()
        
        return visualization_data 