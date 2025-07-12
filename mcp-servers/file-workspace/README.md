# File Workspace MCP Server - US-009: Shared Workspace File Locking

A Model Context Protocol (MCP) server that provides file locking capabilities for multi-agent development environments.

## Features

- ✅ File lock acquisition and release
- ✅ Configurable lock timeout duration
- ✅ Concurrent lock request queuing
- ✅ Automatic stale lock cleanup
- ✅ Global lock status visibility

## Architecture

### Core Components

1. **FileLock Model** - Represents a file lock with metadata
2. **LockingService** - Core business logic for lock management
3. **FileWorkspaceServer** - MCP server with file locking tools
4. **Lock Queue System** - Handles concurrent lock requests
5. **Cleanup Service** - Automatic stale lock removal

### MCP Tools

1. `acquire_file_lock` - Request a file lock with timeout
2. `release_file_lock` - Release an existing file lock
3. `get_file_lock_status` - Check status of a specific file lock
4. `list_all_locks` - View all active locks in the system
5. `force_release_lock` - Admin tool to forcibly release stale locks

## Acceptance Criteria Coverage

- ✅ **File locks can be acquired and released** - Via acquire/release tools
- ✅ **Lock requests include timeout duration** - Configurable timeout parameter
- ✅ **Concurrent lock attempts are queued** - Queue system with FIFO processing
- ✅ **Stale locks are cleaned up automatically** - Background cleanup service
- ✅ **Lock status is visible to all agents** - Status and listing tools

## Usage Example

```python
# Request a file lock
lock_result = await server.acquire_file_lock({
    "file_path": "/workspace/src/main.py",
    "agent_id": "agent-1",
    "timeout_seconds": 300
})

# Release the lock when done
await server.release_file_lock({
    "file_path": "/workspace/src/main.py",
    "agent_id": "agent-1"
})
```

## Project Structure

```
mcp-servers/file-workspace/
├── src/
│   ├── models/
│   │   └── file_lock.py          # File lock data models
│   ├── services/
│   │   ├── locking_service.py    # Core locking logic
│   │   └── cleanup_service.py    # Stale lock cleanup
│   └── file_workspace_server.py  # MCP server implementation
├── tests/
│   ├── test_file_locking.py      # Comprehensive tests
│   └── test_server.py            # Server tests
├── requirements.txt              # Dependencies
└── README.md                     # This file
```

## Story Points: 5
**Related Epic:** Core Infrastructure