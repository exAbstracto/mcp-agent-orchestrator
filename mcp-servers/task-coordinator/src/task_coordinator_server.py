"""
Task Coordinator MCP Server Implementation

Manages development tasks, assignments, and workflow coordination
for multi-agent development teams.
"""

import asyncio
import json
import logging
import sys
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Union, Set
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority enumeration."""
    LOW = 1
    MEDIUM = 3
    HIGH = 5
    CRITICAL = 8
    URGENT = 10


@dataclass
class Task:
    """Represents a development task."""
    id: str
    title: str
    description: str
    assignee: str
    priority: int
    status: str = TaskStatus.PENDING.value
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    due_date: Optional[float] = None
    estimated_hours: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    progress: int = 0  # 0-100 percentage
    notes: str = ""
    creator: str = ""


@dataclass
class TaskStats:
    """Task statistics for monitoring."""
    total_tasks: int = 0
    pending_tasks: int = 0
    in_progress_tasks: int = 0
    completed_tasks: int = 0
    blocked_tasks: int = 0
    average_completion_time: float = 0.0
    tasks_by_assignee: Dict[str, int] = field(default_factory=dict)
    tasks_by_priority: Dict[str, int] = field(default_factory=dict)


class TaskCoordinatorServer:
    """
    Task Coordinator MCP Server implementation.
    
    Provides task management capabilities:
    - Task creation with auto-generated IDs
    - Task persistence and retrieval
    - Assignment and notification
    - Status tracking and updates
    - Priority management
    - Dependency tracking
    """
    
    def __init__(self, name: str = "task-coordinator", version: str = "1.0.0"):
        """Initialize the task coordinator server."""
        self.name = name
        self.version = version
        self.logger = self._setup_logging()
        
        # Task storage and management
        self.tasks: Dict[str, Task] = {}  # task_id -> task
        self.assignee_tasks: Dict[str, Set[str]] = defaultdict(set)  # assignee -> task_ids
        self.completed_tasks: List[str] = []  # For completion time tracking
        self.task_completion_times: Dict[str, float] = {}  # task_id -> completion_time
        
        # Statistics
        self.stats = TaskStats()
        
        # Message queue integration for notifications
        self.message_queue_available = False
        self.message_queue_channel = "task-notifications"
        
        # MCP capabilities
        self.capabilities = {
            "tools": [
                {
                    "name": "create_task",
                    "description": "Create a new development task",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Task title",
                                "minLength": 1,
                                "maxLength": 200
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed task description",
                                "maxLength": 2000
                            },
                            "assignee": {
                                "type": "string",
                                "description": "Agent ID to assign the task to"
                            },
                            "priority": {
                                "type": "integer",
                                "description": "Task priority (1=low, 3=medium, 5=high, 8=critical, 10=urgent)",
                                "minimum": 1,
                                "maximum": 10,
                                "default": 3
                            },
                            "due_date": {
                                "type": "number",
                                "description": "Due date as Unix timestamp"
                            },
                            "estimated_hours": {
                                "type": "number",
                                "description": "Estimated hours to complete",
                                "minimum": 0
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Task tags for categorization"
                            },
                            "dependencies": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Task IDs this task depends on"
                            },
                            "creator": {
                                "type": "string",
                                "description": "ID of the agent/user creating the task"
                            }
                        },
                        "required": ["title", "description", "assignee"]
                    }
                },
                {
                    "name": "get_task",
                    "description": "Get a specific task by ID",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "Task ID to retrieve"
                            }
                        },
                        "required": ["task_id"]
                    }
                },
                {
                    "name": "list_tasks",
                    "description": "List tasks with optional filtering",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "assignee": {
                                "type": "string",
                                "description": "Filter by assignee"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["pending", "in_progress", "blocked", "review", "complete", "cancelled"],
                                "description": "Filter by status"
                            },
                            "priority": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 10,
                                "description": "Filter by minimum priority"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Filter by tags (must have all tags)"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 20,
                                "minimum": 1,
                                "maximum": 100,
                                "description": "Maximum number of tasks to return"
                            },
                            "sort_by": {
                                "type": "string",
                                "enum": ["created_at", "updated_at", "priority", "due_date"],
                                "default": "created_at",
                                "description": "Sort field"
                            },
                            "sort_order": {
                                "type": "string",
                                "enum": ["asc", "desc"],
                                "default": "desc",
                                "description": "Sort order"
                            }
                        }
                    }
                },
                {
                    "name": "update_task",
                    "description": "Update an existing task",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "Task ID to update"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["pending", "in_progress", "blocked", "review", "complete", "cancelled"],
                                "description": "New task status"
                            },
                            "progress": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 100,
                                "description": "Progress percentage"
                            },
                            "assignee": {
                                "type": "string",
                                "description": "Reassign to different agent"
                            },
                            "priority": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 10,
                                "description": "Update priority"
                            },
                            "notes": {
                                "type": "string",
                                "description": "Add progress notes"
                            },
                            "estimated_hours": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Update time estimate"
                            }
                        },
                        "required": ["task_id"]
                    }
                },
                {
                    "name": "delete_task",
                    "description": "Delete a task",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "Task ID to delete"
                            }
                        },
                        "required": ["task_id"]
                    }
                },
                {
                    "name": "get_task_stats",
                    "description": "Get task statistics and metrics",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "include_details": {
                                "type": "boolean",
                                "default": False,
                                "description": "Include detailed breakdowns"
                            }
                        }
                    }
                },
                {
                    "name": "notify_assignee",
                    "description": "Send notification to task assignee",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "Task ID"
                            },
                            "message": {
                                "type": "string",
                                "description": "Notification message"
                            },
                            "priority": {
                                "type": "integer",
                                "default": 5,
                                "description": "Notification priority"
                            }
                        },
                        "required": ["task_id", "message"]
                    }
                }
            ],
            "resources": [
                {
                    "uri": "tasks://all",
                    "name": "All Tasks",
                    "description": "Complete list of all tasks"
                },
                {
                    "uri": "tasks://pending",
                    "name": "Pending Tasks",
                    "description": "Tasks awaiting assignment or start"
                },
                {
                    "uri": "tasks://active",
                    "name": "Active Tasks",
                    "description": "Tasks currently in progress"
                },
                {
                    "uri": "tasks://stats",
                    "name": "Task Statistics",
                    "description": "Task metrics and analytics"
                }
            ]
        }
        
        self.logger.info(f"Initialized {name} v{version}")
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
        
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a JSON-RPC 2.0 request."""
        # Validate basic JSON-RPC structure
        if not isinstance(request, dict):
            return self._create_error_response(None, -32600, "Invalid Request")
            
        request_id = request.get("id")
        
        if "jsonrpc" not in request or "method" not in request:
            return self._create_error_response(request_id, -32600, "Invalid Request")
            
        method = request.get("method")
        params = request.get("params", {})
        
        self.logger.debug(f"Handling request: {method}")
        
        # Route to appropriate handler
        try:
            if method == "initialize":
                return self._handle_initialize(request_id, params)
            elif method == "tools/call":
                return self._handle_tool_call(request_id, params)
            elif method == "resources/read":
                return self._handle_resource_read(request_id, params)
            elif method == "resources/list":
                return self._handle_resource_list(request_id)
            else:
                return self._create_error_response(request_id, -32601, "Method not found")
                
        except Exception as e:
            self.logger.error(f"Error handling {method}: {e}")
            return self._create_error_response(request_id, -32603, f"Internal error: {str(e)}")
            
    def _handle_initialize(self, request_id: Union[str, int, None], 
                          params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the initialize method."""
        protocol_version = params.get("protocolVersion", "2024-11-05")
        client_info = params.get("clientInfo", {})
        
        self.logger.info(
            f"Client {client_info.get('name', 'unknown')} "
            f"v{client_info.get('version', 'unknown')} connected"
        )
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": protocol_version,
                "serverInfo": {
                    "name": self.name,
                    "version": self.version
                },
                "capabilities": self.capabilities
            }
        }
        
    def _handle_tool_call(self, request_id: Union[str, int, None], 
                         params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call requests."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "create_task":
            return self._create_task(request_id, arguments)
        elif tool_name == "get_task":
            return self._get_task(request_id, arguments)
        elif tool_name == "list_tasks":
            return self._list_tasks(request_id, arguments)
        elif tool_name == "update_task":
            return self._update_task(request_id, arguments)
        elif tool_name == "delete_task":
            return self._delete_task(request_id, arguments)
        elif tool_name == "get_task_stats":
            return self._get_task_stats(request_id, arguments)
        elif tool_name == "notify_assignee":
            return self._notify_assignee(request_id, arguments)
        else:
            return self._create_error_response(request_id, -32601, f"Unknown tool: {tool_name}")
            
    def _create_task(self, request_id: Union[str, int, None], 
                    arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task."""
        try:
            # Extract required fields
            title = arguments["title"].strip()
            description = arguments["description"].strip()
            assignee = arguments["assignee"].strip()
            
            # Validate required fields
            if not title:
                return self._create_error_response(request_id, -32602, "Title cannot be empty")
            if not description:
                return self._create_error_response(request_id, -32602, "Description cannot be empty")
            if not assignee:
                return self._create_error_response(request_id, -32602, "Assignee cannot be empty")
                
            # Extract optional fields with defaults
            priority = arguments.get("priority", TaskPriority.MEDIUM.value)
            due_date = arguments.get("due_date")
            estimated_hours = arguments.get("estimated_hours")
            tags = arguments.get("tags", [])
            dependencies = arguments.get("dependencies", [])
            creator = arguments.get("creator", "unknown")
            
            # Validate priority
            if priority < 1 or priority > 10:
                return self._create_error_response(request_id, -32602, "Priority must be between 1 and 10")
                
            # Validate dependencies exist
            for dep_id in dependencies:
                if dep_id not in self.tasks:
                    return self._create_error_response(
                        request_id, -32602, f"Dependency task {dep_id} does not exist"
                    )
                    
            # Generate task ID
            task_id = self._generate_task_id()
            
            # Create task
            task = Task(
                id=task_id,
                title=title,
                description=description,
                assignee=assignee,
                priority=priority,
                due_date=due_date,
                estimated_hours=estimated_hours,
                tags=tags,
                dependencies=dependencies,
                creator=creator
            )
            
            # Store task
            self.tasks[task_id] = task
            self.assignee_tasks[assignee].add(task_id)
            
            # Update statistics
            self._update_stats()
            
            # Send notification to assignee
            notification_sent = self._send_task_notification(task, "assigned")
            
            self.logger.info(f"Created task {task_id}: {title} (assigned to {assignee})")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "task_id": task_id,
                    "title": title,
                    "assignee": assignee,
                    "priority": priority,
                    "created_at": task.created_at,
                    "notification_sent": notification_sent,
                    "dependencies_count": len(dependencies)
                }
            }
            
        except KeyError as e:
            return self._create_error_response(request_id, -32602, f"Missing parameter: {e}")
        except Exception as e:
            return self._create_error_response(request_id, -32603, f"Error creating task: {e}")
            
    def _get_task(self, request_id: Union[str, int, None], 
                 arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific task by ID."""
        try:
            task_id = arguments["task_id"]
            
            if task_id not in self.tasks:
                return self._create_error_response(request_id, -32602, f"Task {task_id} not found")
                
            task = self.tasks[task_id]
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "task": asdict(task)
                }
            }
            
        except KeyError as e:
            return self._create_error_response(request_id, -32602, f"Missing parameter: {e}")
        except Exception as e:
            return self._create_error_response(request_id, -32603, f"Error getting task: {e}")
            
    def _list_tasks(self, request_id: Union[str, int, None], 
                   arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List tasks with filtering and sorting."""
        try:
            # Get filter parameters
            assignee_filter = arguments.get("assignee")
            status_filter = arguments.get("status")
            priority_filter = arguments.get("priority")
            tags_filter = arguments.get("tags", [])
            limit = arguments.get("limit", 20)
            sort_by = arguments.get("sort_by", "created_at")
            sort_order = arguments.get("sort_order", "desc")
            
            # Filter tasks
            filtered_tasks = []
            for task in self.tasks.values():
                # Apply filters
                if assignee_filter and task.assignee != assignee_filter:
                    continue
                if status_filter and task.status != status_filter:
                    continue
                if priority_filter and task.priority < priority_filter:
                    continue
                if tags_filter and not all(tag in task.tags for tag in tags_filter):
                    continue
                    
                filtered_tasks.append(task)
                
            # Sort tasks
            reverse = sort_order == "desc"
            if sort_by == "created_at":
                filtered_tasks.sort(key=lambda t: t.created_at, reverse=reverse)
            elif sort_by == "updated_at":
                filtered_tasks.sort(key=lambda t: t.updated_at, reverse=reverse)
            elif sort_by == "priority":
                filtered_tasks.sort(key=lambda t: t.priority, reverse=reverse)
            elif sort_by == "due_date":
                filtered_tasks.sort(key=lambda t: t.due_date or 0, reverse=reverse)
                
            # Apply limit
            limited_tasks = filtered_tasks[:limit]
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tasks": [asdict(task) for task in limited_tasks],
                    "total_count": len(filtered_tasks),
                    "returned_count": len(limited_tasks),
                    "filters_applied": {
                        "assignee": assignee_filter,
                        "status": status_filter,
                        "priority": priority_filter,
                        "tags": tags_filter
                    }
                }
            }
            
        except Exception as e:
            return self._create_error_response(request_id, -32603, f"Error listing tasks: {e}")
            
    def _update_task(self, request_id: Union[str, int, None], 
                    arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing task."""
        try:
            task_id = arguments["task_id"]
            
            if task_id not in self.tasks:
                return self._create_error_response(request_id, -32602, f"Task {task_id} not found")
                
            task = self.tasks[task_id]
            old_assignee = task.assignee
            old_status = task.status
            updated_fields = []
            
            # Update fields
            if "status" in arguments:
                task.status = arguments["status"]
                updated_fields.append("status")
                
                # Track completion
                if task.status == TaskStatus.COMPLETE.value and old_status != TaskStatus.COMPLETE.value:
                    completion_time = time.time() - task.created_at
                    self.task_completion_times[task_id] = completion_time
                    self.completed_tasks.append(task_id)
                    
            if "progress" in arguments:
                task.progress = arguments["progress"]
                updated_fields.append("progress")
                
            if "assignee" in arguments:
                new_assignee = arguments["assignee"]
                if new_assignee != task.assignee:
                    # Remove from old assignee
                    self.assignee_tasks[task.assignee].discard(task_id)
                    # Add to new assignee
                    task.assignee = new_assignee
                    self.assignee_tasks[new_assignee].add(task_id)
                    updated_fields.append("assignee")
                    
            if "priority" in arguments:
                task.priority = arguments["priority"]
                updated_fields.append("priority")
                
            if "notes" in arguments:
                task.notes = arguments["notes"]
                updated_fields.append("notes")
                
            if "estimated_hours" in arguments:
                task.estimated_hours = arguments["estimated_hours"]
                updated_fields.append("estimated_hours")
                
            # Update timestamp
            task.updated_at = time.time()
            
            # Update statistics
            self._update_stats()
            
            # Send notifications for significant changes
            notifications_sent = []
            if "status" in updated_fields:
                if self._send_task_notification(task, f"status_changed_to_{task.status}"):
                    notifications_sent.append(f"status_changed_to_{task.status}")
                    
            if "assignee" in updated_fields:
                if self._send_task_notification(task, "reassigned"):
                    notifications_sent.append("reassigned")
                    
            self.logger.info(f"Updated task {task_id}: {', '.join(updated_fields)}")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "task_id": task_id,
                    "updated_fields": updated_fields,
                    "new_status": task.status,
                    "new_assignee": task.assignee,
                    "progress": task.progress,
                    "updated_at": task.updated_at,
                    "notifications_sent": notifications_sent
                }
            }
            
        except KeyError as e:
            return self._create_error_response(request_id, -32602, f"Missing parameter: {e}")
        except Exception as e:
            return self._create_error_response(request_id, -32603, f"Error updating task: {e}")
            
    def _delete_task(self, request_id: Union[str, int, None], 
                    arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a task."""
        try:
            task_id = arguments["task_id"]
            
            if task_id not in self.tasks:
                return self._create_error_response(request_id, -32602, f"Task {task_id} not found")
                
            task = self.tasks[task_id]
            
            # Check for dependent tasks
            dependent_tasks = [
                t for t in self.tasks.values() 
                if task_id in t.dependencies
            ]
            
            if dependent_tasks:
                dependent_ids = [t.id for t in dependent_tasks]
                return self._create_error_response(
                    request_id, -32602, 
                    f"Cannot delete task {task_id}: it has dependencies in tasks {dependent_ids}"
                )
                
            # Remove task
            assignee = task.assignee
            del self.tasks[task_id]
            self.assignee_tasks[assignee].discard(task_id)
            
            # Update statistics
            self._update_stats()
            
            # Send deletion notification
            notification_sent = self._send_task_notification(task, "deleted")
            
            self.logger.info(f"Deleted task {task_id}: {task.title}")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "task_id": task_id,
                    "deleted": True,
                    "title": task.title,
                    "assignee": assignee,
                    "notification_sent": notification_sent
                }
            }
            
        except KeyError as e:
            return self._create_error_response(request_id, -32602, f"Missing parameter: {e}")
        except Exception as e:
            return self._create_error_response(request_id, -32603, f"Error deleting task: {e}")
            
    def _get_task_stats(self, request_id: Union[str, int, None], 
                       arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get task statistics."""
        try:
            include_details = arguments.get("include_details", False)
            
            # Update current statistics
            self._update_stats()
            
            result = {
                "total_tasks": self.stats.total_tasks,
                "pending_tasks": self.stats.pending_tasks,
                "in_progress_tasks": self.stats.in_progress_tasks,
                "completed_tasks": self.stats.completed_tasks,
                "blocked_tasks": self.stats.blocked_tasks,
                "average_completion_time_hours": self.stats.average_completion_time / 3600 if self.stats.average_completion_time else 0,
                "timestamp": time.time()
            }
            
            if include_details:
                result.update({
                    "tasks_by_assignee": dict(self.stats.tasks_by_assignee),
                    "tasks_by_priority": dict(self.stats.tasks_by_priority),
                    "completion_rate": (
                        self.stats.completed_tasks / self.stats.total_tasks * 100 
                        if self.stats.total_tasks > 0 else 0
                    ),
                    "active_assignees": len([a for a, count in self.stats.tasks_by_assignee.items() if count > 0])
                })
                
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except Exception as e:
            return self._create_error_response(request_id, -32603, f"Error getting stats: {e}")
            
    def _notify_assignee(self, request_id: Union[str, int, None], 
                        arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification to task assignee."""
        try:
            task_id = arguments["task_id"]
            message = arguments["message"]
            priority = arguments.get("priority", 5)
            
            if task_id not in self.tasks:
                return self._create_error_response(request_id, -32602, f"Task {task_id} not found")
                
            task = self.tasks[task_id]
            
            # Send custom notification
            notification_data = {
                "type": "custom_notification",
                "task_id": task_id,
                "task_title": task.title,
                "message": message,
                "sender": "task-coordinator",
                "timestamp": time.time()
            }
            
            success = self._send_notification(task.assignee, notification_data, priority)
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "task_id": task_id,
                    "assignee": task.assignee,
                    "message": message,
                    "notification_sent": success
                }
            }
            
        except KeyError as e:
            return self._create_error_response(request_id, -32602, f"Missing parameter: {e}")
        except Exception as e:
            return self._create_error_response(request_id, -32603, f"Error sending notification: {e}")
            
    def _handle_resource_read(self, request_id: Union[str, int, None], 
                             params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resource read requests."""
        uri = params.get("uri", "")
        
        try:
            if uri == "tasks://all":
                tasks_data = [asdict(task) for task in self.tasks.values()]
                content = json.dumps(tasks_data, indent=2)
                
            elif uri == "tasks://pending":
                pending_tasks = [
                    asdict(task) for task in self.tasks.values() 
                    if task.status == TaskStatus.PENDING.value
                ]
                content = json.dumps(pending_tasks, indent=2)
                
            elif uri == "tasks://active":
                active_tasks = [
                    asdict(task) for task in self.tasks.values() 
                    if task.status == TaskStatus.IN_PROGRESS.value
                ]
                content = json.dumps(active_tasks, indent=2)
                
            elif uri == "tasks://stats":
                self._update_stats()
                stats_data = asdict(self.stats)
                stats_data["timestamp"] = time.time()
                content = json.dumps(stats_data, indent=2)
                
            else:
                return self._create_error_response(request_id, -32602, f"Unknown resource: {uri}")
                
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": content
                        }
                    ]
                }
            }
            
        except Exception as e:
            return self._create_error_response(request_id, -32603, f"Error reading resource: {e}")
            
    def _handle_resource_list(self, request_id: Union[str, int, None]) -> Dict[str, Any]:
        """Handle resource list requests."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resources": self.capabilities["resources"]
            }
        }
        
    def _generate_task_id(self) -> str:
        """Generate a unique task ID."""
        timestamp = int(time.time() * 1000)  # Milliseconds for uniqueness
        random_part = str(uuid.uuid4())[:8]
        return f"TASK-{timestamp}-{random_part.upper()}"
        
    def _update_stats(self):
        """Update task statistics."""
        self.stats.total_tasks = len(self.tasks)
        self.stats.pending_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING.value)
        self.stats.in_progress_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS.value)
        self.stats.completed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETE.value)
        self.stats.blocked_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.BLOCKED.value)
        
        # Calculate average completion time
        if self.task_completion_times:
            self.stats.average_completion_time = sum(self.task_completion_times.values()) / len(self.task_completion_times)
        else:
            self.stats.average_completion_time = 0.0
            
        # Tasks by assignee
        self.stats.tasks_by_assignee.clear()
        for task in self.tasks.values():
            if task.status != TaskStatus.COMPLETE.value:  # Count active tasks only
                self.stats.tasks_by_assignee[task.assignee] = self.stats.tasks_by_assignee.get(task.assignee, 0) + 1
                
        # Tasks by priority
        self.stats.tasks_by_priority.clear()
        for task in self.tasks.values():
            if task.status != TaskStatus.COMPLETE.value:  # Count active tasks only
                priority_name = self._get_priority_name(task.priority)
                self.stats.tasks_by_priority[priority_name] = self.stats.tasks_by_priority.get(priority_name, 0) + 1
                
    def _get_priority_name(self, priority: int) -> str:
        """Get priority name from priority number."""
        if priority >= 10:
            return "urgent"
        elif priority >= 8:
            return "critical"
        elif priority >= 5:
            return "high"
        elif priority >= 3:
            return "medium"
        else:
            return "low"
            
    def _send_task_notification(self, task: Task, event_type: str) -> bool:
        """Send notification about task event to assignee."""
        notification_data = {
            "type": f"task_{event_type}",
            "task_id": task.id,
            "task_title": task.title,
            "assignee": task.assignee,
            "priority": task.priority,
            "status": task.status,
            "event_type": event_type,
            "timestamp": time.time()
        }
        
        return self._send_notification(task.assignee, notification_data, task.priority)
        
    def _send_notification(self, recipient: str, data: Dict[str, Any], priority: int = 5) -> bool:
        """Send notification via message queue (if available)."""
        try:
            # This would integrate with the message queue server from US-003
            # For now, we'll simulate the notification
            self.logger.info(
                f"Notification sent to {recipient}: {data.get('type', 'unknown')} "
                f"(Task: {data.get('task_id', 'N/A')})"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send notification to {recipient}: {e}")
            return False
            
    def _create_error_response(self, request_id: Union[str, int, None], 
                              code: int, message: str) -> Dict[str, Any]:
        """Create a JSON-RPC error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }


async def main():
    """Main entry point for standalone server."""
    server = TaskCoordinatorServer()
    
    try:
        # Read from stdin, write to stdout (MCP protocol)
        while True:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
                
            try:
                request = json.loads(line.strip())
                response = server.handle_request(request)
                print(json.dumps(response), flush=True)
            except json.JSONDecodeError:
                error_response = server._create_error_response(
                    None, -32700, "Parse error"
                )
                print(json.dumps(error_response), flush=True)
                
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    asyncio.run(main()) 