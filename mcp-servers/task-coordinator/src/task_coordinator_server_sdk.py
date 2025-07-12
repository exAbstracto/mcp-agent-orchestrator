"""
Task Coordinator MCP Server using Official SDK - Standalone Implementation

This module provides a standalone MCP SDK-based task coordinator implementation
using the core business logic models.
"""

import json
import logging
import sys
from typing import Any, Dict, List

from mcp.server import Server
from mcp.types import Tool, TextContent, Resource

# Import core business logic models
from .models.task import Task, TaskStatus
from .models.dependency import DependencyGraph, DependencyError
from .notification_system import NotificationSystem


class TaskCoordinatorServerSDK:
    """
    Task Coordinator MCP Server using the official MCP Python SDK.
    
    This server provides:
    - Official MCP SDK integration
    - Task creation and dependency management
    - Dependency graph visualization
    - Task lifecycle coordination
    """
    
    def __init__(self, name: str = "task-coordinator", version: str = "1.0.0"):
        """
        Initialize the MCP task coordinator server with official SDK.
        
        Args:
            name: The server name
            version: The server version
        """
        self.name = name
        self.version = version
        self.server = Server(name)
        self.logger = self._setup_logging()
        
        # Initialize dependency management components
        self.dependency_graph = DependencyGraph()
        self.notification_system = NotificationSystem()
        
        # Set up notification system in dependency graph
        self.dependency_graph.set_notification_system(self.notification_system)
        
        # Register tools and resources
        self._register_tools()
        self._register_resources()
        
        self.logger.info(f"Initialized {name} v{version} with MCP SDK")

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
    
    def _register_tools(self) -> None:
        """Register MCP tools using the official SDK"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available task coordinator tools"""
            return [
                Tool(
                    name="create_task",
                    description="Create a new task",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string", "description": "Unique task identifier"},
                            "title": {"type": "string", "description": "Task title"},
                            "description": {"type": "string", "description": "Task description"},
                            "priority": {"type": "integer", "description": "Task priority (1-10)"},
                            "dependencies": {
                                "type": "array", 
                                "description": "List of dependent task IDs",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["task_id", "title"]
                    }
                ),
                Tool(
                    name="add_dependency",
                    description="Add a dependency between tasks",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "dependent_task_id": {"type": "string", "description": "Task that depends on another"},
                            "depends_on_task_id": {"type": "string", "description": "Task that is depended upon"}
                        },
                        "required": ["dependent_task_id", "depends_on_task_id"]
                    }
                ),
                Tool(
                    name="get_blocked_tasks",
                    description="Get list of blocked tasks",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_ready_tasks",
                    description="Get list of tasks ready to start",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="resolve_dependencies",
                    description="Resolve dependencies when a task is completed",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "completed_task_id": {"type": "string", "description": "ID of the completed task"}
                        },
                        "required": ["completed_task_id"]
                    }
                ),
                Tool(
                    name="get_visualization_data",
                    description="Get dependency graph visualization data",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls using the MCP SDK"""
            try:
                # Route to the appropriate method using the core logic
                if name == "create_task":
                    result = self._create_task(arguments)
                elif name == "add_dependency":
                    result = self._add_dependency(arguments)
                elif name == "get_blocked_tasks":
                    result = self._get_blocked_tasks(arguments)
                elif name == "get_ready_tasks":
                    result = self._get_ready_tasks(arguments)
                elif name == "resolve_dependencies":
                    result = self._resolve_dependencies(arguments)
                elif name == "get_visualization_data":
                    result = self._get_visualization_data(arguments)
                else:
                    result = {"error": f"Unknown tool: {name}"}
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            except DependencyError as e:
                self.logger.error(f"Dependency error in tool {name}: {str(e)}")
                return [TextContent(type="text", text=f"Dependency Error: {str(e)}")]
            except Exception as e:
                self.logger.error(f"Error in tool {name}: {str(e)}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    def _register_resources(self) -> None:
        """Register MCP resources using the official SDK"""
        
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List available resources"""
            return [
                Resource(
                    uri="tasks://blocked",
                    name="Blocked Tasks",
                    description="List of tasks that are blocked by dependencies",
                    mimeType="application/json"
                ),
                Resource(
                    uri="tasks://ready",
                    name="Ready Tasks", 
                    description="List of tasks that are ready to be executed",
                    mimeType="application/json"
                ),
                Resource(
                    uri="tasks://graph",
                    name="Dependency Graph",
                    description="Visualization data for the dependency graph",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read resource content"""
            if uri == "tasks://blocked":
                blocked_data = self._get_blocked_tasks({})
                return json.dumps(blocked_data, indent=2)
            elif uri == "tasks://ready":
                ready_data = self._get_ready_tasks({})
                return json.dumps(ready_data, indent=2)
            elif uri == "tasks://graph":
                graph_data = self._get_visualization_data({})
                return json.dumps(graph_data, indent=2)
            else:
                raise ValueError(f"Unknown resource: {uri}")
    
    # Tool implementation methods that use the core business logic
    def _create_task(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a task using core logic"""
        try:
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
                dependencies=dependencies,
            )

            # Add to dependency graph
            self.dependency_graph.add_task(task)

            return {
                "success": True,
                "task_id": task_id,
                "message": f"Task {task_id} created successfully",
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _add_dependency(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Add dependency using core logic"""
        try:
            dependent_task_id = arguments.get("dependent_task_id")
            depends_on_task_id = arguments.get("depends_on_task_id")

            if not dependent_task_id or not depends_on_task_id:
                raise ValueError("dependent_task_id and depends_on_task_id are required")

            # Add dependency (this will check for cycles)
            self.dependency_graph.add_dependency(dependent_task_id, depends_on_task_id)

            return {
                "success": True,
                "message": f"Dependency added: {dependent_task_id} depends on {depends_on_task_id}",
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_blocked_tasks(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get blocked tasks using core logic"""
        try:
            blocked_tasks = self.dependency_graph.get_blocked_tasks()
            return {"blocked_tasks": blocked_tasks, "count": len(blocked_tasks)}
        except Exception as e:
            return {"error": str(e)}
    
    def _get_ready_tasks(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get ready tasks using core logic"""
        try:
            ready_tasks = self.dependency_graph.get_ready_tasks()
            return {"ready_tasks": ready_tasks, "count": len(ready_tasks)}
        except Exception as e:
            return {"error": str(e)}
    
    def _resolve_dependencies(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve dependencies using core logic"""
        try:
            completed_task_id = arguments.get("completed_task_id")

            if not completed_task_id:
                raise ValueError("completed_task_id is required")

            # Resolve dependencies
            newly_ready_tasks = self.dependency_graph.resolve_dependencies(
                completed_task_id
            )

            return {
                "success": True,
                "completed_task_id": completed_task_id,
                "newly_ready_tasks": newly_ready_tasks,
                "count": len(newly_ready_tasks),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_visualization_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get visualization data using core logic"""
        try:
            visualization_data = self.dependency_graph.get_visualization_data()
            return visualization_data
        except Exception as e:
            return {"error": str(e)}
    
    async def run(self) -> None:
        """Run the MCP server using the official SDK"""
        self.logger.info(f"Starting {self.name} v{self.version} with MCP SDK")
        await self.server.run()


# Factory function for consistency
def create_task_coordinator_server(name: str = "task-coordinator", version: str = "1.0.0") -> TaskCoordinatorServerSDK:
    """Factory function to create a task coordinator server instance"""
    return TaskCoordinatorServerSDK(name, version)


# For backward compatibility
TaskCoordinatorServer = TaskCoordinatorServerSDK