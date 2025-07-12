"""
Dependency management models with cycle detection
"""

import networkx as nx
from typing import Dict, List, Set, Any, Optional, TYPE_CHECKING
from .task import Task, TaskStatus

if TYPE_CHECKING:
    from ..notification_system import NotificationSystem, NotificationEvent


class DependencyError(Exception):
    """Exception raised for dependency-related errors"""
    pass


class Dependency:
    """Individual dependency relationship"""
    
    def __init__(self, dependent_task_id: str, depends_on_task_id: str):
        self.dependent_task_id = dependent_task_id
        self.depends_on_task_id = depends_on_task_id
    
    def __repr__(self):
        return f"Dependency({self.dependent_task_id} -> {self.depends_on_task_id})"


class DependencyGraph:
    """
    Dependency graph with cycle detection using NetworkX
    """
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.dependencies: Dict[str, List[str]] = {}
        self.graph = nx.DiGraph()
        self.notification_system: Optional['NotificationSystem'] = None
    
    def add_task(self, task: Task) -> None:
        """Add a task to the dependency graph"""
        self.tasks[task.id] = task
        self.dependencies[task.id] = list(task.dependencies)
        self.graph.add_node(task.id)
        
        # Add existing dependencies to the graph
        for dep_id in task.dependencies:
            if dep_id in self.tasks:
                self.graph.add_edge(dep_id, task.id)
    
    def add_dependency(self, dependent_task_id: str, depends_on_task_id: str) -> None:
        """
        Add a dependency between tasks with cycle detection
        
        Args:
            dependent_task_id: The task that depends on another
            depends_on_task_id: The task that is depended upon
        """
        if dependent_task_id not in self.tasks:
            raise DependencyError(f"Task {dependent_task_id} not found in graph")
        if depends_on_task_id not in self.tasks:
            raise DependencyError(f"Task {depends_on_task_id} not found in graph")
        
        # Check for cycles before adding
        self.graph.add_edge(depends_on_task_id, dependent_task_id)
        
        if not nx.is_directed_acyclic_graph(self.graph):
            # Remove the edge that creates the cycle
            self.graph.remove_edge(depends_on_task_id, dependent_task_id)
            raise DependencyError(f"Circular dependency detected: adding {depends_on_task_id} -> {dependent_task_id} would create a cycle")
        
        # Update task dependencies
        self.tasks[dependent_task_id].add_dependency(depends_on_task_id)
        self.tasks[depends_on_task_id].add_dependent_task(dependent_task_id)
        
        # Update internal dependencies tracking
        if depends_on_task_id not in self.dependencies[dependent_task_id]:
            self.dependencies[dependent_task_id].append(depends_on_task_id)
    
    def remove_task(self, task_id: str) -> None:
        """Remove a task from the dependency graph"""
        if task_id not in self.tasks:
            return
        
        # Remove dependencies from other tasks
        for other_task_id, other_task in self.tasks.items():
            if other_task_id != task_id:
                if other_task.has_dependency(task_id):
                    other_task.remove_dependency(task_id)
                    self.dependencies[other_task_id] = [
                        dep for dep in self.dependencies[other_task_id] if dep != task_id
                    ]
        
        # Remove from graph
        self.graph.remove_node(task_id)
        
        # Remove from internal structures
        del self.tasks[task_id]
        del self.dependencies[task_id]
    
    def has_cycles(self) -> bool:
        """Check if the graph has cycles"""
        return not nx.is_directed_acyclic_graph(self.graph)
    
    def get_blocked_tasks(self) -> List[str]:
        """Get list of tasks that are blocked by dependencies"""
        blocked = []
        for task_id, task in self.tasks.items():
            if task.is_blocked() and task.status != TaskStatus.COMPLETED:
                blocked.append(task_id)
        return blocked
    
    def get_ready_tasks(self) -> List[str]:
        """Get list of tasks that are ready to start (no dependencies)"""
        ready = []
        for task_id, task in self.tasks.items():
            if task.can_start() and task.status == TaskStatus.PENDING:
                ready.append(task_id)
        return ready
    
    def resolve_dependencies(self, completed_task_id: str) -> List[str]:
        """
        Resolve dependencies when a task is completed
        
        Args:
            completed_task_id: The ID of the task that was completed
            
        Returns:
            List of task IDs that became ready to start
        """
        newly_ready = []
        
        # Get tasks that depend on the completed task
        dependent_tasks = []
        for task_id, deps in self.dependencies.items():
            if completed_task_id in deps:
                dependent_tasks.append(task_id)
        
        # Remove the completed task from their dependencies
        for task_id in dependent_tasks:
            self.tasks[task_id].remove_dependency(completed_task_id)
            self.dependencies[task_id] = [
                dep for dep in self.dependencies[task_id] if dep != completed_task_id
            ]
            
            # Check if the task is now ready to start
            if self.tasks[task_id].can_start() and self.tasks[task_id].status == TaskStatus.PENDING:
                newly_ready.append(task_id)
        
        # Notify about resolved dependencies
        if self.notification_system and newly_ready:
            from ..notification_system import NotificationEvent
            event = NotificationEvent(
                event_type="dependency_resolved",
                task_id=completed_task_id,
                newly_ready_tasks=newly_ready
            )
            self.notification_system.notify("dependency_resolved", event)
        
        return newly_ready
    
    def topological_sort(self) -> List[str]:
        """Get topological sort of tasks (execution order)"""
        try:
            return list(nx.topological_sort(self.graph))
        except nx.NetworkXError:
            raise DependencyError("Cannot perform topological sort: graph contains cycles")
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks in the graph"""
        return list(self.tasks.values())
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """Get data for visualizing the dependency graph"""
        nodes = []
        edges = []
        
        # Create nodes
        for task_id, task in self.tasks.items():
            nodes.append({
                "id": task_id,
                "label": task.title,
                "status": task.status.value,
                "priority": task.priority
            })
        
        # Create edges
        for source, target in self.graph.edges():
            edges.append({
                "source": source,
                "target": target
            })
        
        return {
            "nodes": nodes,
            "edges": edges
        }
    
    def set_notification_system(self, notification_system: 'NotificationSystem') -> None:
        """Set the notification system for this dependency graph"""
        self.notification_system = notification_system 