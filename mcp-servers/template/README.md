# MCP Server Template

A minimal Model Context Protocol (MCP) server implementation that provides a foundation for building MCP-compatible servers.

## Features

- ✅ JSON-RPC 2.0 protocol implementation
- ✅ Basic error handling and logging
- ✅ Capability registration system
- ✅ Initialize method support
- ✅ Comprehensive test coverage
- ✅ Type hints throughout

## Project Structure

```
mcp-servers/template/
├── src/
│   └── mcp_server.py      # Core MCP server implementation
├── tests/
│   └── test_server.py     # Unit tests
├── docs/                  # Additional documentation
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Navigate to the template directory:**
   ```bash
   cd mcp-servers/template
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```
   - Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running Tests

Run all tests with coverage:
```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

## Usage Example

```python
from mcp_server import MCPServer

# Create a server instance
server = MCPServer("my-server", "1.0.0")

# Register capabilities
server.register_capability("tools", {
    "supported": True,
    "listTools": True
})

# Handle a request
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "1.0.0",
        "clientInfo": {
            "name": "test-client",
            "version": "1.0.0"
        }
    }
}

response = server.handle_request(request)
print(response)
```

## Extending the Template

To create your own MCP server:

1. **Copy this template** to a new directory
2. **Extend the MCPServer class** with your custom methods
3. **Add new capabilities** as needed
4. **Implement additional JSON-RPC methods**

### Adding a New Method

```python
def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
    # ... existing code ...
    
    if method == "initialize":
        return self._handle_initialize(request_id, params)
    elif method == "your_custom_method":
        return self._handle_custom_method(request_id, params)
    # ... rest of the code ...
```

## MCP Protocol Compliance

This template follows the Model Context Protocol specification:

- **JSON-RPC 2.0**: All communication uses standard JSON-RPC 2.0
- **Error Codes**: Standard error codes (-32600, -32601, etc.)
- **Initialize Handshake**: Proper protocol version negotiation
- **Capabilities**: Extensible capability system

## Development Guidelines

1. **Always use virtual environments** for consistency
2. **Follow TDD approach**: Write tests first
3. **Maintain test coverage** above 85%
4. **Use type hints** for all functions
5. **Document all public methods**

## Common Error Codes

| Code | Message | Description |
|------|---------|-------------|
| -32600 | Invalid Request | The JSON sent is not a valid Request object |
| -32601 | Method not found | The method does not exist / is not available |
| -32602 | Invalid params | Invalid method parameter(s) |
| -32603 | Internal error | Internal JSON-RPC error |

## License

This template is part of the Multi-Agent Development System project. 