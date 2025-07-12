"""
Task model for dependency management
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class Task(BaseModel):
    """
    Task model with dependency management support
    """
    
    id: str = Field(..., description="Unique task identifier")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    priority: int = Field(default=1, description="Task priority (1-10)")
    dependencies: List[str] = Field(default_factory=list, description="List of dependent task IDs")
    dependent_tasks: List[str] = Field(default_factory=list, description="List of tasks that depend on this task")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    
    def add_dependency(self, task_id: str) -> None:
        """Add a dependency to this task"""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
            
    def remove_dependency(self, task_id: str) -> None:
        """Remove a dependency from this task"""
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)
            
    def has_dependency(self, task_id: str) -> bool:
        """Check if this task has a specific dependency"""
        return task_id in self.dependencies
        
    def add_dependent_task(self, task_id: str) -> None:
        """Add a task that depends on this task"""
        if task_id not in self.dependent_tasks:
            self.dependent_tasks.append(task_id)
            
    def is_blocked(self) -> bool:
        """Check if this task is blocked by dependencies"""
        return len(self.dependencies) > 0
        
    def can_start(self) -> bool:
        """Check if this task can start (no unresolved dependencies)"""
        return len(self.dependencies) == 0
        
    def update_status(self, new_status: TaskStatus) -> None:
        """Update task status and timestamp"""
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "dependent_tasks": self.dependent_tasks,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create task from dictionary"""
        # Convert string timestamps back to datetime objects
        created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
            
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            status=TaskStatus(data["status"]),
            priority=data["priority"],
            dependencies=data.get("dependencies", []),
            dependent_tasks=data.get("dependent_tasks", []),
            created_at=created_at,
            updated_at=updated_at
        ) 