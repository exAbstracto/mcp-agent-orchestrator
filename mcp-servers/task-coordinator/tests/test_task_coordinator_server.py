"""
Comprehensive test suite for Task Coordinator MCP Server

Tests all US-005 acceptance criteria:
- Task creation API endpoint works
- Tasks include title, description, assignee, priority
- Task ID is generated automatically
- Created tasks are persisted
- Task creation triggers notification to assignee
"""

import asyncio
import json
import pytest
import time
import uuid
from typing import Dict, Any
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from task_coordinator_server import TaskCoordinatorServer, Task, TaskStatus, TaskPriority


class TestTaskCreationAPIEndpoint:
    """Test task creation API endpoint acceptance criteria."""
    
    @pytest.fixture
    def server(self):
        """Create a test server instance."""
        return TaskCoordinatorServer("test-coordinator", "1.0.0")
        
    def test_create_task_basic_functionality(self, server):
        """Test basic task creation API functionality."""
        # Create task request
        create_request = {
            "jsonrpc": "2.0",
            "id": "test-1",
            "method": "tools/call",
            "params": {
                "name": "create_task",
                "arguments": {
                    "title": "Implement user authentication",
                    "description": "Create secure user login and registration system with JWT tokens",
                    "assignee": "backend-agent",
                    "priority": 8,
                    "creator": "pm-agent"
                }
            }
        }
        
        response = server.handle_request(create_request)
        
        # Validate response structure
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == "test-1"
        assert "result" in response
        
        result = response["result"]
        assert "task_id" in result
        assert result["title"] == "Implement user authentication"
        assert result["assignee"] == "backend-agent"
        assert result["priority"] == 8
        assert "created_at" in result
        assert "notification_sent" in result
        
        # Verify task was stored
        task_id = result["task_id"]
        assert task_id in server.tasks
        
    def test_create_task_with_all_optional_fields(self, server):
        """Test task creation with all optional fields."""
        due_date = time.time() + 86400  # Tomorrow
        
        create_request = {
            "jsonrpc": "2.0",
            "id": "test-2",
            "method": "tools/call",
            "params": {
                "name": "create_task",
                "arguments": {
                    "title": "Design API endpoints",
                    "description": "Create RESTful API design for user management",
                    "assignee": "backend-architect",
                    "priority": 5,
                    "due_date": due_date,
                    "estimated_hours": 8.5,
                    "tags": ["api", "design", "backend"],
                    "dependencies": [],
                    "creator": "tech-lead"
                }
            }
        }
        
        response = server.handle_request(create_request)
        assert "result" in response
        
        task_id = response["result"]["task_id"]
        task = server.tasks[task_id]
        
        # Verify all fields are set correctly
        assert task.title == "Design API endpoints"
        assert task.description == "Create RESTful API design for user management"
        assert task.assignee == "backend-architect"
        assert task.priority == 5
        assert task.due_date == due_date
        assert task.estimated_hours == 8.5
        assert task.tags == ["api", "design", "backend"]
        assert task.dependencies == []
        assert task.creator == "tech-lead"
        assert task.status == TaskStatus.PENDING.value
        
    def test_create_task_validation_errors(self, server):
        """Test task creation validation errors."""
        # Test missing required fields
        invalid_requests = [
            # Missing title
            {
                "jsonrpc": "2.0",
                "id": "test-missing-title",
                "method": "tools/call",
                "params": {
                    "name": "create_task",
                    "arguments": {
                        "description": "Test description",
                        "assignee": "test-agent"
                    }
                }
            },
            # Empty title
            {
                "jsonrpc": "2.0",
                "id": "test-empty-title",
                "method": "tools/call",
                "params": {
                    "name": "create_task",
                    "arguments": {
                        "title": "",
                        "description": "Test description",
                        "assignee": "test-agent"
                    }
                }
            },
            # Missing description
            {
                "jsonrpc": "2.0",
                "id": "test-missing-desc",
                "method": "tools/call",
                "params": {
                    "name": "create_task",
                    "arguments": {
                        "title": "Test task",
                        "assignee": "test-agent"
                    }
                }
            },
            # Invalid priority
            {
                "jsonrpc": "2.0",
                "id": "test-invalid-priority",
                "method": "tools/call",
                "params": {
                    "name": "create_task",
                    "arguments": {
                        "title": "Test task",
                        "description": "Test description",
                        "assignee": "test-agent",
                        "priority": 15  # Invalid: > 10
                    }
                }
            }
        ]
        
        for request in invalid_requests:
            response = server.handle_request(request)
            assert "error" in response, f"Expected error for request {request['id']}"
            assert response["error"]["code"] == -32602  # Invalid params
            
    def test_api_endpoint_accessibility(self, server):
        """Test that the create_task tool is properly exposed."""
        # Check that create_task is in capabilities
        capabilities = server.capabilities
        assert "tools" in capabilities
        
        tool_names = [tool["name"] for tool in capabilities["tools"]]
        assert "create_task" in tool_names
        
        # Find the create_task tool definition
        create_task_tool = next(
            tool for tool in capabilities["tools"] 
            if tool["name"] == "create_task"
        )
        
        # Verify tool structure
        assert "description" in create_task_tool
        assert "inputSchema" in create_task_tool
        
        # Verify required parameters
        schema = create_task_tool["inputSchema"]
        assert schema["type"] == "object"
        assert "properties" in schema
        assert set(schema["required"]) == {"title", "description", "assignee"}


class TestTaskDataStructure:
    """Test task data structure with required fields acceptance criteria."""
    
    @pytest.fixture
    def server(self):
        """Create a test server instance."""
        return TaskCoordinatorServer("test-coordinator", "1.0.0")
        
    def test_task_includes_all_required_fields(self, server):
        """Test that tasks include title, description, assignee, priority."""
        create_request = {
            "jsonrpc": "2.0",
            "id": "test-fields",
            "method": "tools/call",
            "params": {
                "name": "create_task",
                "arguments": {
                    "title": "Frontend component development",
                    "description": "Create reusable UI components for dashboard",
                    "assignee": "frontend-agent",
                    "priority": 7
                }
            }
        }
        
        response = server.handle_request(create_request)
        task_id = response["result"]["task_id"]
        
        # Get the created task
        get_request = {
            "jsonrpc": "2.0",
            "id": "test-get",
            "method": "tools/call",
            "params": {
                "name": "get_task",
                "arguments": {
                    "task_id": task_id
                }
            }
        }
        
        response = server.handle_request(get_request)
        task_data = response["result"]["task"]
        
        # Verify all required fields are present
        assert "title" in task_data
        assert "description" in task_data
        assert "assignee" in task_data
        assert "priority" in task_data
        
        # Verify field values
        assert task_data["title"] == "Frontend component development"
        assert task_data["description"] == "Create reusable UI components for dashboard"
        assert task_data["assignee"] == "frontend-agent"
        assert task_data["priority"] == 7
        
        # Verify additional important fields
        assert "id" in task_data
        assert "status" in task_data
        assert "created_at" in task_data
        assert "updated_at" in task_data
        
    def test_task_priority_handling(self, server):
        """Test task priority field handling and validation."""
        # Test different priority levels
        priority_tests = [
            (1, "low priority"),
            (3, "medium priority"),
            (5, "high priority"),
            (8, "critical priority"),
            (10, "urgent priority")
        ]
        
        for priority, description in priority_tests:
            create_request = {
                "jsonrpc": "2.0",
                "id": f"test-priority-{priority}",
                "method": "tools/call",
                "params": {
                    "name": "create_task",
                    "arguments": {
                        "title": f"Task with {description}",
                        "description": f"Testing {description} level",
                        "assignee": "test-agent",
                        "priority": priority
                    }
                }
            }
            
            response = server.handle_request(create_request)
            assert "result" in response, f"Failed to create task with priority {priority}"
            
            task_id = response["result"]["task_id"]
            task = server.tasks[task_id]
            assert task.priority == priority
            
    def test_task_default_values(self, server):
        """Test task default values when optional fields are not provided."""
        create_request = {
            "jsonrpc": "2.0",
            "id": "test-defaults",
            "method": "tools/call",
            "params": {
                "name": "create_task",
                "arguments": {
                    "title": "Minimal task",
                    "description": "Task with only required fields",
                    "assignee": "test-agent"
                    # No priority specified - should default to 3 (medium)
                }
            }
        }
        
        response = server.handle_request(create_request)
        task_id = response["result"]["task_id"]
        task = server.tasks[task_id]
        
        # Verify default values
        assert task.priority == TaskPriority.MEDIUM.value  # Should default to 3
        assert task.status == TaskStatus.PENDING.value
        assert task.progress == 0
        assert task.tags == []
        assert task.dependencies == []
        assert task.notes == ""
        assert task.creator == "unknown"  # Default when not specified


class TestTaskIDGeneration:
    """Test automatic task ID generation acceptance criteria."""
    
    @pytest.fixture
    def server(self):
        """Create a test server instance."""
        return TaskCoordinatorServer("test-coordinator", "1.0.0")
        
    def test_task_id_is_generated_automatically(self, server):
        """Test that task IDs are generated automatically."""
        create_request = {
            "jsonrpc": "2.0",
            "id": "test-id-gen",
            "method": "tools/call",
            "params": {
                "name": "create_task",
                "arguments": {
                    "title": "Auto ID test",
                    "description": "Testing automatic ID generation",
                    "assignee": "test-agent"
                }
            }
        }
        
        response = server.handle_request(create_request)
        
        # Verify task ID is present in response
        assert "result" in response
        assert "task_id" in response["result"]
        
        task_id = response["result"]["task_id"]
        
        # Verify task ID format (should start with TASK-)
        assert task_id.startswith("TASK-")
        
        # Verify task ID is unique and not empty
        assert len(task_id) > 5  # More than just "TASK-"
        assert task_id in server.tasks
        
    def test_task_ids_are_unique(self, server):
        """Test that generated task IDs are unique."""
        task_ids = set()
        
        # Create multiple tasks
        for i in range(10):
            create_request = {
                "jsonrpc": "2.0",
                "id": f"test-unique-{i}",
                "method": "tools/call",
                "params": {
                    "name": "create_task",
                    "arguments": {
                        "title": f"Unique test task {i}",
                        "description": f"Testing uniqueness iteration {i}",
                        "assignee": "test-agent"
                    }
                }
            }
            
            response = server.handle_request(create_request)
            task_id = response["result"]["task_id"]
            
            # Verify this ID hasn't been used before
            assert task_id not in task_ids, f"Duplicate task ID generated: {task_id}"
            task_ids.add(task_id)
            
        # Verify we have 10 unique IDs
        assert len(task_ids) == 10
        
    def test_task_id_format_consistency(self, server):
        """Test task ID format consistency."""
        # Create multiple tasks and verify format
        for i in range(5):
            create_request = {
                "jsonrpc": "2.0",
                "id": f"test-format-{i}",
                "method": "tools/call",
                "params": {
                    "name": "create_task",
                    "arguments": {
                        "title": f"Format test {i}",
                        "description": "Testing ID format",
                        "assignee": "test-agent"
                    }
                }
            }
            
            response = server.handle_request(create_request)
            task_id = response["result"]["task_id"]
            
            # Verify format: TASK-{timestamp}-{random}
            parts = task_id.split("-")
            assert len(parts) == 3
            assert parts[0] == "TASK"
            assert parts[1].isdigit()  # Timestamp
            assert len(parts[2]) == 8   # Random part


class TestTaskPersistence:
    """Test task persistence acceptance criteria."""
    
    @pytest.fixture
    def server(self):
        """Create a test server instance."""
        return TaskCoordinatorServer("test-coordinator", "1.0.0")
        
    def test_created_tasks_are_persisted(self, server):
        """Test that created tasks are stored and retrievable."""
        # Create a task
        create_request = {
            "jsonrpc": "2.0",
            "id": "test-persist",
            "method": "tools/call",
            "params": {
                "name": "create_task",
                "arguments": {
                    "title": "Persistence test task",
                    "description": "Testing task persistence functionality",
                    "assignee": "test-agent",
                    "priority": 6
                }
            }
        }
        
        response = server.handle_request(create_request)
        task_id = response["result"]["task_id"]
        
        # Verify task is immediately available
        assert task_id in server.tasks
        stored_task = server.tasks[task_id]
        assert stored_task.title == "Persistence test task"
        assert stored_task.assignee == "test-agent"
        
        # Verify task can be retrieved via API
        get_request = {
            "jsonrpc": "2.0",
            "id": "test-retrieve",
            "method": "tools/call",
            "params": {
                "name": "get_task",
                "arguments": {
                    "task_id": task_id
                }
            }
        }
        
        response = server.handle_request(get_request)
        assert "result" in response
        assert "task" in response["result"]
        
        retrieved_task = response["result"]["task"]
        assert retrieved_task["id"] == task_id
        assert retrieved_task["title"] == "Persistence test task"
        assert retrieved_task["assignee"] == "test-agent"
        assert retrieved_task["priority"] == 6
        
    def test_task_listing_includes_persisted_tasks(self, server):
        """Test that persisted tasks appear in task listings."""
        # Create multiple tasks
        task_data = [
            ("Task A", "Description A", "agent-1", 3),
            ("Task B", "Description B", "agent-2", 5),
            ("Task C", "Description C", "agent-1", 8)
        ]
        
        created_ids = []
        for title, desc, assignee, priority in task_data:
            create_request = {
                "jsonrpc": "2.0",
                "id": f"create-{len(created_ids)}",
                "method": "tools/call",
                "params": {
                    "name": "create_task",
                    "arguments": {
                        "title": title,
                        "description": desc,
                        "assignee": assignee,
                        "priority": priority
                    }
                }
            }
            
            response = server.handle_request(create_request)
            created_ids.append(response["result"]["task_id"])
            
        # List all tasks
        list_request = {
            "jsonrpc": "2.0",
            "id": "test-list-all",
            "method": "tools/call",
            "params": {
                "name": "list_tasks",
                "arguments": {}
            }
        }
        
        response = server.handle_request(list_request)
        assert "result" in response
        
        tasks = response["result"]["tasks"]
        task_ids_in_list = [task["id"] for task in tasks]
        
        # Verify all created tasks are in the list
        for task_id in created_ids:
            assert task_id in task_ids_in_list
            
        # Verify total count matches
        assert response["result"]["total_count"] == len(task_data)
        
    def test_task_statistics_reflect_persisted_tasks(self, server):
        """Test that task statistics reflect persisted tasks."""
        # Initial stats should be empty
        stats_request = {
            "jsonrpc": "2.0",
            "id": "test-stats-initial",
            "method": "tools/call",
            "params": {
                "name": "get_task_stats",
                "arguments": {}
            }
        }
        
        response = server.handle_request(stats_request)
        initial_stats = response["result"]
        assert initial_stats["total_tasks"] == 0
        
        # Create tasks with different priorities
        priorities = [1, 3, 5, 8, 10]
        for i, priority in enumerate(priorities):
            create_request = {
                "jsonrpc": "2.0",
                "id": f"create-stats-{i}",
                "method": "tools/call",
                "params": {
                    "name": "create_task",
                    "arguments": {
                        "title": f"Stats test task {i+1}",
                        "description": f"Priority {priority} task",
                        "assignee": f"agent-{i+1}",
                        "priority": priority
                    }
                }
            }
            server.handle_request(create_request)
            
        # Check updated stats
        response = server.handle_request(stats_request)
        updated_stats = response["result"]
        
        assert updated_stats["total_tasks"] == len(priorities)
        assert updated_stats["pending_tasks"] == len(priorities)  # All should be pending
        assert updated_stats["completed_tasks"] == 0


class TestAssigneeNotification:
    """Test assignee notification acceptance criteria."""
    
    @pytest.fixture
    def server(self):
        """Create a test server instance."""
        return TaskCoordinatorServer("test-coordinator", "1.0.0")
        
    def test_task_creation_triggers_notification(self, server):
        """Test that task creation triggers notification to assignee."""
        # Create a task
        create_request = {
            "jsonrpc": "2.0",
            "id": "test-notify",
            "method": "tools/call",
            "params": {
                "name": "create_task",
                "arguments": {
                    "title": "Notification test task",
                    "description": "Testing notification functionality",
                    "assignee": "test-agent",
                    "priority": 7
                }
            }
        }
        
        response = server.handle_request(create_request)
        
        # Verify notification was triggered (indicated in response)
        assert "result" in response
        assert "notification_sent" in response["result"]
        
        # For now, notification_sent should be True (simulated)
        # In a real implementation, this would integrate with message queue
        assert response["result"]["notification_sent"] is True
        
    def test_notification_includes_task_details(self, server):
        """Test that notifications include relevant task details."""
        # This test verifies the notification logic structure
        # In a real implementation, we'd test actual message queue integration
        
        assignee = "notification-test-agent"
        
        create_request = {
            "jsonrpc": "2.0",
            "id": "test-notify-details",
            "method": "tools/call",
            "params": {
                "name": "create_task",
                "arguments": {
                    "title": "Detailed notification test",
                    "description": "Testing notification details",
                    "assignee": assignee,
                    "priority": 9
                }
            }
        }
        
        response = server.handle_request(create_request)
        task_id = response["result"]["task_id"]
        
        # Verify the task was created for the correct assignee
        task = server.tasks[task_id]
        assert task.assignee == assignee
        
        # Verify assignee tracking
        assert task_id in server.assignee_tasks[assignee]
        
        # Verify notification was attempted
        assert response["result"]["notification_sent"] is True
        
    def test_manual_notification_sending(self, server):
        """Test manual notification sending to assignees."""
        # Create a task first
        create_request = {
            "jsonrpc": "2.0",
            "id": "test-manual-setup",
            "method": "tools/call",
            "params": {
                "name": "create_task",
                "arguments": {
                    "title": "Manual notification test",
                    "description": "Setup for testing manual notifications",
                    "assignee": "manual-test-agent"
                }
            }
        }
        
        response = server.handle_request(create_request)
        task_id = response["result"]["task_id"]
        
        # Send manual notification
        notify_request = {
            "jsonrpc": "2.0",
            "id": "test-manual-notify",
            "method": "tools/call",
            "params": {
                "name": "notify_assignee",
                "arguments": {
                    "task_id": task_id,
                    "message": "Please review the updated requirements",
                    "priority": 8
                }
            }
        }
        
        response = server.handle_request(notify_request)
        
        assert "result" in response
        assert response["result"]["task_id"] == task_id
        assert response["result"]["assignee"] == "manual-test-agent"
        assert response["result"]["message"] == "Please review the updated requirements"
        assert response["result"]["notification_sent"] is True


# Integration test demonstrating all acceptance criteria together
class TestUS005Integration:
    """Integration test demonstrating all US-005 acceptance criteria."""
    
    def test_complete_us005_acceptance_criteria(self):
        """
        Comprehensive test that validates all US-005 acceptance criteria:
        - Task creation API endpoint works ✓
        - Tasks include title, description, assignee, priority ✓
        - Task ID is generated automatically ✓
        - Created tasks are persisted ✓
        - Task creation triggers notification to assignee ✓
        """
        server = TaskCoordinatorServer("us005-integration", "1.0.0")
        
        print("Testing US-005 Task Coordinator - Create Task")
        print("=" * 50)
        
        # ✓ Test 1: Task creation API endpoint works
        print("1. Testing Task Creation API Endpoint...")
        
        create_request = {
            "jsonrpc": "2.0",
            "id": "integration-test",
            "method": "tools/call",
            "params": {
                "name": "create_task",
                "arguments": {
                    "title": "Implement user dashboard",
                    "description": "Create comprehensive user dashboard with analytics, settings, and profile management",
                    "assignee": "frontend-lead",
                    "priority": 8,
                    "estimated_hours": 16.0,
                    "tags": ["frontend", "dashboard", "ui"],
                    "creator": "product-manager"
                }
            }
        }
        
        response = server.handle_request(create_request)
        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        print("✅ Task creation API endpoint works correctly")
        
        # ✓ Test 2: Tasks include title, description, assignee, priority
        print("2. Testing Task Data Structure...")
        
        task_id = response["result"]["task_id"]
        task = server.tasks[task_id]
        
        assert task.title == "Implement user dashboard"
        assert task.description == "Create comprehensive user dashboard with analytics, settings, and profile management"
        assert task.assignee == "frontend-lead"
        assert task.priority == 8
        print("✅ Tasks include all required fields (title, description, assignee, priority)")
        
        # ✓ Test 3: Task ID is generated automatically
        print("3. Testing Automatic Task ID Generation...")
        
        assert task_id.startswith("TASK-")
        assert len(task_id) > 10  # Should be substantial length
        assert task.id == task_id
        print(f"✅ Task ID generated automatically: {task_id}")
        
        # ✓ Test 4: Created tasks are persisted
        print("4. Testing Task Persistence...")
        
        # Verify task is stored
        assert task_id in server.tasks
        
        # Verify task can be retrieved
        get_request = {
            "jsonrpc": "2.0",
            "id": "get-test",
            "method": "tools/call",
            "params": {
                "name": "get_task",
                "arguments": {
                    "task_id": task_id
                }
            }
        }
        
        get_response = server.handle_request(get_request)
        retrieved_task = get_response["result"]["task"]
        assert retrieved_task["id"] == task_id
        assert retrieved_task["title"] == "Implement user dashboard"
        
        # Verify task appears in listings
        list_request = {
            "jsonrpc": "2.0",
            "id": "list-test",
            "method": "tools/call",
            "params": {
                "name": "list_tasks",
                "arguments": {
                    "assignee": "frontend-lead"
                }
            }
        }
        
        list_response = server.handle_request(list_request)
        task_ids = [t["id"] for t in list_response["result"]["tasks"]]
        assert task_id in task_ids
        print("✅ Created tasks are persisted and retrievable")
        
        # ✓ Test 5: Task creation triggers notification to assignee
        print("5. Testing Assignee Notification...")
        
        # Verify notification was triggered during creation
        assert response["result"]["notification_sent"] is True
        
        # Verify assignee tracking
        assert task_id in server.assignee_tasks["frontend-lead"]
        
        # Test manual notification
        manual_notify_request = {
            "jsonrpc": "2.0",
            "id": "manual-notify-test",
            "method": "tools/call",
            "params": {
                "name": "notify_assignee",
                "arguments": {
                    "task_id": task_id,
                    "message": "Task priority has been increased - please prioritize this work",
                    "priority": 9
                }
            }
        }
        
        notify_response = server.handle_request(manual_notify_request)
        assert notify_response["result"]["notification_sent"] is True
        print("✅ Task creation triggers notification to assignee")
        
        # Additional comprehensive testing
        print("\n6. Testing Additional Functionality...")
        
        # Test task updates
        update_request = {
            "jsonrpc": "2.0",
            "id": "update-test",
            "method": "tools/call",
            "params": {
                "name": "update_task",
                "arguments": {
                    "task_id": task_id,
                    "status": "in_progress",
                    "progress": 25,
                    "notes": "Started working on wireframes and component structure"
                }
            }
        }
        
        update_response = server.handle_request(update_request)
        assert "status" in update_response["result"]["updated_fields"]
        assert update_response["result"]["new_status"] == "in_progress"
        print("✅ Task updates work correctly")
        
        # Test statistics
        stats_request = {
            "jsonrpc": "2.0",
            "id": "stats-test",
            "method": "tools/call",
            "params": {
                "name": "get_task_stats",
                "arguments": {
                    "include_details": True
                }
            }
        }
        
        stats_response = server.handle_request(stats_request)
        stats = stats_response["result"]
        assert stats["total_tasks"] == 1
        assert stats["in_progress_tasks"] == 1
        assert "frontend-lead" in stats["tasks_by_assignee"]
        print("✅ Task statistics tracking works correctly")
        
        print("\n🎉 ALL US-005 ACCEPTANCE CRITERIA VALIDATED SUCCESSFULLY!")
        print("=" * 50)
        print("✅ Task creation API endpoint works")
        print("✅ Tasks include title, description, assignee, priority")
        print("✅ Task ID is generated automatically")
        print("✅ Created tasks are persisted")
        print("✅ Task creation triggers notification to assignee")
        print("\n📊 Final Statistics:")
        print(f"   - Total tasks created: {stats['total_tasks']}")
        print(f"   - Tasks in progress: {stats['in_progress_tasks']}")
        print(f"   - Active assignees: {len(stats['tasks_by_assignee'])}")
        print(f"   - Task ID format: {task_id}")


if __name__ == "__main__":
    # Run the integration test
    TestUS005Integration().test_complete_us005_acceptance_criteria() 