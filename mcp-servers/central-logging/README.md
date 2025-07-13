# Central Logging MCP Server - US-010: Centralized Logging System

A Model Context Protocol (MCP) server that provides centralized logging capabilities for multi-agent development environments.

## Features

- ✅ Central log aggregation from all MCP servers
- ✅ Correlation ID tracking for distributed tracing
- ✅ Configurable log levels and filtering
- ✅ Advanced log search and query capabilities
- ✅ Log retention policy with minimum 7-day storage

## Architecture

### Core Components

1. **LogEntry Model** - Structured log entry with correlation tracking
2. **LoggingService** - Core log aggregation and storage logic
3. **SearchService** - Advanced log search and filtering
4. **RetentionService** - Automatic log cleanup and archival
5. **CentralLoggingServer** - MCP server with logging tools
6. **LoggingClient** - Client library for other servers

### MCP Tools

1. `send_log` - Send log entry to central system
2. `search_logs` - Search logs by various criteria
3. `get_logs_by_correlation_id` - Trace related log entries
4. `list_log_levels` - Get available log levels
5. `set_log_level` - Configure logging level for components
6. `get_log_stats` - System statistics and health
7. `cleanup_old_logs` - Manual retention cleanup

## Acceptance Criteria Coverage

- ✅ **All MCP servers send logs to central location** - Via send_log tool
- ✅ **Logs include correlation IDs for tracing** - Built-in correlation system
- ✅ **Log levels are configurable** - Dynamic level configuration
- ✅ **Logs are searchable by various criteria** - Advanced search functionality
- ✅ **Log retention is at least 7 days** - Configurable retention policy

## Usage Example

```python
# Send a log entry
log_result = await server.send_log({
    "level": "INFO",
    "message": "Agent started successfully",
    "component": "agent-1",
    "correlation_id": "req-123",
    "metadata": {"startup_time": 1.5}
})

# Search logs by criteria
search_result = await server.search_logs({
    "component": "agent-1",
    "level": "ERROR",
    "time_range": {"start": "2024-01-01T00:00:00Z", "end": "2024-01-02T00:00:00Z"}
})
```

## Project Structure

```
mcp-servers/central-logging/
├── src/
│   ├── models/
│   │   ├── log_entry.py         # Log entry data models
│   │   └── search_criteria.py   # Search query models
│   ├── services/
│   │   ├── logging_service.py   # Core logging logic
│   │   ├── search_service.py    # Log search functionality
│   │   └── retention_service.py # Log cleanup and retention
│   ├── client/
│   │   └── logging_client.py    # Client library for other servers
│   └── central_logging_server.py # MCP server implementation
├── tests/
│   ├── test_central_logging.py  # Comprehensive TDD tests
│   └── test_integration.py      # Integration tests
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

## Story Points: 3
**Related Epic:** Core Infrastructure