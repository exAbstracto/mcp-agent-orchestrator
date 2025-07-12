# Task Coordinator MCP Server

A Model Context Protocol (MCP) server for managing development tasks, assignments, and workflow coordination in multi-agent development teams. Provides comprehensive task management capabilities with automatic ID generation, persistence, and assignee notifications.

## 🎯 User Story: US-005

**As a BA/PM agent**  
**I want to create new development tasks**  
**So that work can be assigned to appropriate agents**

### ✅ Acceptance Criteria Met

- [x] **Task creation API endpoint works** - Full MCP tool implementation
- [x] **Tasks include title, description, assignee, priority** - Comprehensive task data model
- [x] **Task ID is generated automatically** - Unique timestamp-based IDs
- [x] **Created tasks are persisted** - In-memory storage with full CRUD operations
- [x] **Task creation triggers notification to assignee** - Integrated notification system

## 🚀 Features

### Core Task Management
- **Task Creation** - Create tasks with comprehensive metadata
- **Automatic ID Generation** - Unique, timestamp-based task identifiers
- **Task Persistence** - In-memory storage with full CRUD operations
- **Status Tracking** - Complete lifecycle management (pending → in_progress → complete)
- **Priority Management** - 10-level priority system (1=low, 10=urgent)
- **Assignment Tracking** - Agent assignment with reassignment capabilities

### Advanced Features
- **Dependency Management** - Task dependencies with validation
- **Progress Tracking** - 0-100% completion tracking
- **Due Date Management** - Due date tracking and monitoring
- **Time Estimation** - Estimated hours tracking
- **Tagging System** - Flexible categorization with tags
- **Statistics & Analytics** - Real-time task metrics and reporting

### Notifications & Communication
- **Assignee Notifications** - Automatic notifications on task events
- **Manual Notifications** - Custom notifications to assignees
- **Status Change Alerts** - Notifications on status updates
- **Reassignment Alerts** - Notifications on task reassignment

### MCP Integration
- **7 MCP Tools** - Complete task management API
- **4 MCP Resources** - Live task data access
- **Full JSON-RPC 2.0** - Standard protocol compliance
- **Error Handling** - Comprehensive validation and error responses

## 📦 Installation

### Prerequisites
- Python 3.8+
- No external dependencies (uses only Python standard library)

### Setup
```bash
# Navigate to task coordinator server
cd mcp-servers/task-coordinator

# Install development dependencies (optional)
pip install -r requirements.txt

# Run tests to validate installation
python tests/test_task_coordinator_server.py
```

## 🔧 Usage

### Standalone Server
```bash
# Run as standalone MCP server
python src/task_coordinator_server.py
```

### As MCP Server in Client Configuration

#### Cursor Configuration
```json
{
  "mcpServers": {
    "task-coordinator": {
      "command": "python",
      "args": ["./mcp-servers/task-coordinator/src/task_coordinator_server.py"],
      "env": {}
    }
  }
}
```

#### Claude Code Configuration
```json
{
  "mcpServers": {
    "task-coordinator": {
      "type": "stdio",
      "command": "python",
      "args": ["./mcp-servers/task-coordinator/src/task_coordinator_server.py"]
    }
  }
}
```

## 📚 API Reference

### Tools

#### `create_task`
Create a new development task with automatic ID generation and assignee notification.

**Parameters:**
- `title` (string, required) - Task title (1-200 characters)
- `description` (string, required) - Detailed task description (max 2000 characters)
- `assignee` (string, required) - Agent ID to assign the task to
- `priority` (integer, optional) - Priority 1-10 (default: 3=medium)
- `due_date` (number, optional) - Due date as Unix timestamp
- `estimated_hours` (number, optional) - Estimated hours to complete
- `tags` (array, optional) - Task tags for categorization
- `dependencies` (array, optional) - Task IDs this task depends on
- `creator` (string, optional) - ID of the agent/user creating the task

**Returns:**
```json
{
  "task_id": "TASK-1752327814798-9C766A0D",
  "title": "Implement user authentication",
  "assignee": "backend-agent",
  "priority": 8,
  "created_at": 1752327814.798,
  "notification_sent": true,
  "dependencies_count": 0
}
```

#### `get_task`
Retrieve a specific task by ID.

**Parameters:**
- `task_id` (string, required) - Task ID to retrieve

**Returns:**
```json
{
  "task": {
    "id": "TASK-1752327814798-9C766A0D",
    "title": "Implement user authentication",
    "description": "Create secure login system with JWT tokens",
    "assignee": "backend-agent",
    "priority": 8,
    "status": "pending",
    "created_at": 1752327814.798,
    "updated_at": 1752327814.798,
    "progress": 0,
    "tags": ["auth", "security"],
    "dependencies": [],
    "estimated_hours": 16.0
  }
}
```

#### `list_tasks`
List tasks with filtering and sorting options.

**Parameters:**
- `assignee` (string, optional) - Filter by assignee
- `status` (string, optional) - Filter by status (pending, in_progress, blocked, review, complete, cancelled)
- `priority` (integer, optional) - Filter by minimum priority
- `tags` (array, optional) - Filter by tags (must have all specified tags)
- `limit` (integer, optional) - Maximum tasks to return (1-100, default: 20)
- `sort_by` (string, optional) - Sort field (created_at, updated_at, priority, due_date)
- `sort_order` (string, optional) - Sort order (asc, desc, default: desc)

#### `update_task`
Update an existing task with status changes, progress updates, and reassignment.

**Parameters:**
- `task_id` (string, required) - Task ID to update
- `status` (string, optional) - New status
- `progress` (integer, optional) - Progress percentage (0-100)
- `assignee` (string, optional) - Reassign to different agent
- `priority` (integer, optional) - Update priority (1-10)
- `notes` (string, optional) - Add progress notes
- `estimated_hours` (number, optional) - Update time estimate

#### `delete_task`
Delete a task (with dependency validation).

**Parameters:**
- `task_id` (string, required) - Task ID to delete

#### `get_task_stats`
Get comprehensive task statistics and metrics.

**Parameters:**
- `include_details` (boolean, optional) - Include detailed breakdowns (default: false)

**Returns:**
```json
{
  "total_tasks": 15,
  "pending_tasks": 5,
  "in_progress_tasks": 7,
  "completed_tasks": 3,
  "blocked_tasks": 0,
  "average_completion_time_hours": 18.5,
  "timestamp": 1752327814.798,
  "tasks_by_assignee": {
    "backend-agent": 4,
    "frontend-agent": 3,
    "devops-agent": 1
  },
  "tasks_by_priority": {
    "high": 6,
    "medium": 7,
    "critical": 2
  }
}
```

#### `notify_assignee`
Send custom notification to task assignee.

**Parameters:**
- `task_id` (string, required) - Task ID
- `message` (string, required) - Notification message
- `priority` (integer, optional) - Notification priority (default: 5)

### Resources

#### `tasks://all`
Complete list of all tasks in JSON format.

#### `tasks://pending`
All tasks with status "pending".

#### `tasks://active`
All tasks with status "in_progress".

#### `tasks://stats`
Real-time task statistics and metrics.

## 🔄 Usage Examples

### Basic Task Creation

```json
// Create a new development task
{
  "jsonrpc": "2.0",
  "id": "create-auth-task",
  "method": "tools/call",
  "params": {
    "name": "create_task",
    "arguments": {
      "title": "Implement OAuth2 authentication",
      "description": "Add OAuth2 authentication with Google and GitHub providers, including user profile management and session handling",
      "assignee": "backend-lead",
      "priority": 8,
      "estimated_hours": 24.0,
      "due_date": 1752414214.798,
      "tags": ["auth", "oauth2", "security", "backend"],
      "creator": "product-manager"
    }
  }
}
```

### Task Management Workflow

```json
// 1. Create task
{
  "method": "tools/call",
  "params": {
    "name": "create_task",
    "arguments": {
      "title": "User dashboard implementation",
      "description": "Create responsive user dashboard with analytics widgets",
      "assignee": "frontend-lead",
      "priority": 6,
      "tags": ["frontend", "dashboard", "ui"]
    }
  }
}

// 2. Start working on task
{
  "method": "tools/call",
  "params": {
    "name": "update_task",
    "arguments": {
      "task_id": "TASK-1752327814798-9C766A0D",
      "status": "in_progress",
      "progress": 10,
      "notes": "Started working on wireframes and component architecture"
    }
  }
}

// 3. Update progress
{
  "method": "tools/call",
  "params": {
    "name": "update_task",
    "arguments": {
      "task_id": "TASK-1752327814798-9C766A0D",
      "progress": 75,
      "notes": "Dashboard components completed, working on data integration"
    }
  }
}

// 4. Complete task
{
  "method": "tools/call",
  "params": {
    "name": "update_task",
    "arguments": {
      "task_id": "TASK-1752327814798-9C766A0D",
      "status": "complete",
      "progress": 100,
      "notes": "Dashboard implementation complete, all tests passing"
    }
  }
}
```

### Team Coordination Patterns

```json
// BA/PM creates tasks for sprint
{
  "method": "tools/call",
  "params": {
    "name": "create_task",
    "arguments": {
      "title": "User registration API",
      "description": "Implement user registration with email verification",
      "assignee": "backend-agent",
      "priority": 8,
      "tags": ["api", "auth", "backend"]
    }
  }
}

{
  "method": "tools/call",
  "params": {
    "name": "create_task",
    "arguments": {
      "title": "Registration form UI",
      "description": "Create registration form with validation",
      "assignee": "frontend-agent",
      "priority": 6,
      "tags": ["ui", "forms", "frontend"],
      "dependencies": ["TASK-1752327814798-9C766A0D"]  // Depends on API
    }
  }
}

// Monitor team progress
{
  "method": "tools/call",
  "params": {
    "name": "get_task_stats",
    "arguments": {
      "include_details": true
    }
  }
}

// Get tasks for specific agent
{
  "method": "tools/call",
  "params": {
    "name": "list_tasks",
    "arguments": {
      "assignee": "backend-agent",
      "status": "in_progress",
      "sort_by": "priority",
      "sort_order": "desc"
    }
  }
}
```

### Custom Notifications

```json
// Send urgent notification to assignee
{
  "method": "tools/call",
  "params": {
    "name": "notify_assignee",
    "arguments": {
      "task_id": "TASK-1752327814798-9C766A0D",
      "message": "Client demo scheduled for tomorrow - please prioritize this task for completion today",
      "priority": 10
    }
  }
}
```

## 📊 Task ID Format

Task IDs are automatically generated with the format: `TASK-{timestamp}-{random}`

Example: `TASK-1752327814798-9C766A0D`

- **TASK-** - Fixed prefix for identification
- **1752327814798** - Unix timestamp in milliseconds (for uniqueness)
- **9C766A0D** - 8-character random uppercase hex string

This format ensures:
- **Uniqueness** across all tasks
- **Chronological ordering** by creation time
- **Human readability** with recognizable prefix
- **System compatibility** with various databases and APIs

## 📈 Task Status Lifecycle

```
pending → in_progress → review → complete
    ↓           ↓          ↓
  blocked   cancelled   cancelled
```

**Status Descriptions:**
- **pending** - Task created, awaiting start
- **in_progress** - Currently being worked on
- **blocked** - Cannot proceed due to external dependencies
- **review** - Work complete, awaiting review/approval
- **complete** - Task finished and approved
- **cancelled** - Task no longer needed or abandoned

## 🔢 Priority System

| Priority | Name | Use Case |
|----------|------|----------|
| 10 | Urgent | Production down, critical hotfixes |
| 8-9 | Critical | Security issues, major bugs |
| 5-7 | High | Important features, significant bugs |
| 3-4 | Medium | Standard features, minor improvements |
| 1-2 | Low | Nice-to-have features, documentation |

## 🧪 Testing

### Run Integration Test
```bash
# Run comprehensive US-005 validation
python tests/test_task_coordinator_server.py
```

### Expected Output
```
Testing US-005 Task Coordinator - Create Task
==================================================
✅ Task creation API endpoint works correctly
✅ Tasks include all required fields (title, description, assignee, priority)
✅ Task ID generated automatically: TASK-1752327814798-9C766A0D
✅ Created tasks are persisted and retrievable
✅ Task creation triggers notification to assignee
✅ Task updates work correctly
✅ Task statistics tracking works correctly

🎉 ALL US-005 ACCEPTANCE CRITERIA VALIDATED SUCCESSFULLY!
```

### Test Coverage
- **Task Creation API** - Complete endpoint functionality
- **Data Structure** - All required and optional fields
- **ID Generation** - Uniqueness and format validation
- **Persistence** - Storage and retrieval operations
- **Notifications** - Assignee notification system
- **Updates** - Status changes and progress tracking
- **Statistics** - Real-time metrics and analytics

## 🔍 Monitoring & Management

### Task Statistics
```python
# Get comprehensive task metrics
{
  "method": "tools/call",
  "params": {
    "name": "get_task_stats",
    "arguments": {"include_details": true}
  }
}
```

### Active Task Monitoring
```python
# Monitor in-progress tasks
{
  "method": "tools/call",
  "params": {
    "name": "list_tasks",
    "arguments": {
      "status": "in_progress",
      "sort_by": "updated_at",
      "sort_order": "asc"  # Oldest first (might need attention)
    }
  }
}
```

### Workload Distribution
```python
# Check agent workloads
stats = get_task_stats(include_details=True)
for agent, task_count in stats["tasks_by_assignee"].items():
    print(f"{agent}: {task_count} active tasks")
```

## 🔮 Integration Opportunities

### Message Queue Integration
Integrates with US-003 Message Queue for notifications:
```python
# Automatic integration with message queue server
# Notifications sent to "task-notifications" channel
# Contains task details, assignee, and event type
```

### Future Enhancements
- **Persistent Storage** - Database backend for durability
- **Real-time Updates** - WebSocket notifications
- **Advanced Analytics** - Productivity metrics and trends
- **Automated Assignment** - ML-based task assignment
- **Integration APIs** - Slack, Jira, GitHub integration
- **Time Tracking** - Actual vs estimated time analysis
- **Sprint Management** - Sprint planning and velocity tracking

## 📄 License

Part of the MCP Agent Orchestrator project. See root LICENSE file.

## 🤝 Contributing

1. Follow TDD approach - write tests first
2. Maintain comprehensive test coverage
3. Update documentation for new features
4. Validate all acceptance criteria
5. Test with realistic multi-agent scenarios

## 📞 Support

- **Issues**: GitHub Issues
- **Documentation**: This README + inline code docs
- **Tests**: Comprehensive test suite demonstrates usage
- **Integration**: Designed for multi-agent coordination workflows

---

**Ready for Phase 2 Agent Implementation!** This task coordinator provides the foundation for BA/PM agents (US-011) to create and manage development tasks across the multi-agent team. 