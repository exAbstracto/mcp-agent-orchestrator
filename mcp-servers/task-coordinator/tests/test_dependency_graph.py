"""
Tests for Dependency Graph validation and cycle detection - TDD implementation
"""

import pytest
from typing import List, Dict, Set

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.dependency import DependencyGraph, Dependency, DependencyError
from src.models.task import Task, TaskStatus


class TestDependencyGraph:
    """Test cases for DependencyGraph with cycle detection"""

    def test_dependency_graph_creation(self):
        """Test creating an empty dependency graph"""
        graph = DependencyGraph()
        
        assert graph.tasks == {}
        assert graph.dependencies == {}
        assert len(graph.get_all_tasks()) == 0

    def test_add_task_to_graph(self):
        """Test adding a task to the dependency graph"""
        graph = DependencyGraph()
        task = Task(id="task-1", title="Test Task", description="Test")
        
        graph.add_task(task)
        
        assert "task-1" in graph.tasks
        assert graph.tasks["task-1"] == task
        assert "task-1" in graph.dependencies
        assert graph.dependencies["task-1"] == []

    def test_add_dependency_to_graph(self):
        """Test adding a dependency between tasks"""
        graph = DependencyGraph()
        task1 = Task(id="task-1", title="Task 1", description="First task")
        task2 = Task(id="task-2", title="Task 2", description="Second task")
        
        graph.add_task(task1)
        graph.add_task(task2)
        graph.add_dependency("task-2", "task-1")  # task-2 depends on task-1
        
        assert "task-1" in graph.dependencies["task-2"]
        assert task2.has_dependency("task-1")

    def test_simple_cycle_detection(self):
        """Test detection of simple cycles in dependency graph"""
        graph = DependencyGraph()
        task1 = Task(id="task-1", title="Task 1", description="First task")
        task2 = Task(id="task-2", title="Task 2", description="Second task")
        
        graph.add_task(task1)
        graph.add_task(task2)
        graph.add_dependency("task-2", "task-1")  # task-2 depends on task-1
        
        # This should create a cycle: task-1 -> task-2 -> task-1
        with pytest.raises(DependencyError, match="Circular dependency detected"):
            graph.add_dependency("task-1", "task-2")

    def test_complex_cycle_detection(self):
        """Test detection of complex cycles involving multiple tasks"""
        graph = DependencyGraph()
        
        # Create tasks: task-1 -> task-2 -> task-3 -> task-1 (cycle)
        tasks = []
        for i in range(1, 4):
            task = Task(id=f"task-{i}", title=f"Task {i}", description=f"Task {i}")
            tasks.append(task)
            graph.add_task(task)
        
        graph.add_dependency("task-2", "task-1")  # task-2 depends on task-1
        graph.add_dependency("task-3", "task-2")  # task-3 depends on task-2
        
        # This should create a cycle
        with pytest.raises(DependencyError, match="Circular dependency detected"):
            graph.add_dependency("task-1", "task-3")

    def test_valid_dependency_chain(self):
        """Test that valid dependency chains don't raise errors"""
        graph = DependencyGraph()
        
        # Create a valid chain: task-1 -> task-2 -> task-3 (no cycle)
        tasks = []
        for i in range(1, 4):
            task = Task(id=f"task-{i}", title=f"Task {i}", description=f"Task {i}")
            tasks.append(task)
            graph.add_task(task)
        
        graph.add_dependency("task-2", "task-1")  # task-2 depends on task-1
        graph.add_dependency("task-3", "task-2")  # task-3 depends on task-2
        
        # This should not raise an error
        assert graph.has_cycles() is False

    def test_get_blocked_tasks(self):
        """Test identifying blocked tasks"""
        graph = DependencyGraph()
        
        task1 = Task(id="task-1", title="Task 1", description="First task")
        task2 = Task(id="task-2", title="Task 2", description="Second task")
        task3 = Task(id="task-3", title="Task 3", description="Third task")
        
        graph.add_task(task1)
        graph.add_task(task2)
        graph.add_task(task3)
        
        graph.add_dependency("task-2", "task-1")  # task-2 depends on task-1
        graph.add_dependency("task-3", "task-1")  # task-3 depends on task-1
        
        blocked_tasks = graph.get_blocked_tasks()
        
        assert "task-2" in blocked_tasks
        assert "task-3" in blocked_tasks
        assert "task-1" not in blocked_tasks

    def test_get_ready_tasks(self):
        """Test identifying tasks that are ready to start"""
        graph = DependencyGraph()
        
        task1 = Task(id="task-1", title="Task 1", description="First task")
        task2 = Task(id="task-2", title="Task 2", description="Second task")
        task3 = Task(id="task-3", title="Task 3", description="Third task")
        
        graph.add_task(task1)
        graph.add_task(task2)
        graph.add_task(task3)
        
        graph.add_dependency("task-2", "task-1")  # task-2 depends on task-1
        graph.add_dependency("task-3", "task-1")  # task-3 depends on task-1
        
        ready_tasks = graph.get_ready_tasks()
        
        assert "task-1" in ready_tasks
        assert "task-2" not in ready_tasks
        assert "task-3" not in ready_tasks

    def test_resolve_dependencies(self):
        """Test resolving dependencies when a task is completed"""
        graph = DependencyGraph()
        
        task1 = Task(id="task-1", title="Task 1", description="First task")
        task2 = Task(id="task-2", title="Task 2", description="Second task")
        task3 = Task(id="task-3", title="Task 3", description="Third task")
        
        graph.add_task(task1)
        graph.add_task(task2)
        graph.add_task(task3)
        
        graph.add_dependency("task-2", "task-1")  # task-2 depends on task-1
        graph.add_dependency("task-3", "task-1")  # task-3 depends on task-1
        
        # Mark task-1 as completed
        task1.update_status(TaskStatus.COMPLETED)
        newly_ready = graph.resolve_dependencies("task-1")
        
        assert "task-2" in newly_ready
        assert "task-3" in newly_ready
        assert not graph.tasks["task-2"].has_dependency("task-1")
        assert not graph.tasks["task-3"].has_dependency("task-1")

    def test_topological_sort(self):
        """Test topological sorting of tasks"""
        graph = DependencyGraph()
        
        # Create tasks with dependencies: task-1 -> task-2 -> task-3
        task1 = Task(id="task-1", title="Task 1", description="First task")
        task2 = Task(id="task-2", title="Task 2", description="Second task")
        task3 = Task(id="task-3", title="Task 3", description="Third task")
        
        graph.add_task(task1)
        graph.add_task(task2)
        graph.add_task(task3)
        
        graph.add_dependency("task-2", "task-1")  # task-2 depends on task-1
        graph.add_dependency("task-3", "task-2")  # task-3 depends on task-2
        
        sorted_tasks = graph.topological_sort()
        
        # task-1 should come before task-2, task-2 before task-3
        task1_idx = sorted_tasks.index("task-1")
        task2_idx = sorted_tasks.index("task-2")
        task3_idx = sorted_tasks.index("task-3")
        
        assert task1_idx < task2_idx
        assert task2_idx < task3_idx

    def test_remove_task_from_graph(self):
        """Test removing a task from the dependency graph"""
        graph = DependencyGraph()
        
        task1 = Task(id="task-1", title="Task 1", description="First task")
        task2 = Task(id="task-2", title="Task 2", description="Second task")
        
        graph.add_task(task1)
        graph.add_task(task2)
        graph.add_dependency("task-2", "task-1")
        
        graph.remove_task("task-1")
        
        assert "task-1" not in graph.tasks
        assert "task-1" not in graph.dependencies
        assert not graph.tasks["task-2"].has_dependency("task-1")

    def test_graph_visualization_data(self):
        """Test getting visualization data for the dependency graph"""
        graph = DependencyGraph()
        
        task1 = Task(id="task-1", title="Task 1", description="First task")
        task2 = Task(id="task-2", title="Task 2", description="Second task")
        
        graph.add_task(task1)
        graph.add_task(task2)
        graph.add_dependency("task-2", "task-1")
        
        viz_data = graph.get_visualization_data()
        
        assert "nodes" in viz_data
        assert "edges" in viz_data
        assert len(viz_data["nodes"]) == 2
        assert len(viz_data["edges"]) == 1
        
        # Check node data
        node_ids = [node["id"] for node in viz_data["nodes"]]
        assert "task-1" in node_ids
        assert "task-2" in node_ids
        
        # Check edge data
        edge = viz_data["edges"][0]
        assert edge["source"] == "task-1"
        assert edge["target"] == "task-2"


class TestDependencyError:
    """Test cases for DependencyError exception"""

    def test_dependency_error_creation(self):
        """Test creating DependencyError"""
        error = DependencyError("Test error message")
        
        assert str(error) == "Test error message"
        assert isinstance(error, Exception) 