"""MCP Server Template Package"""

# MCP Server implementation using official MCP SDK
from .mcp_server_sdk import MCPServerSDK, create_mcp_server

# Default implementation
MCPServer = MCPServerSDK

__version__ = "1.0.0"
__all__ = ["MCPServer", "MCPServerSDK", "create_mcp_server"]
