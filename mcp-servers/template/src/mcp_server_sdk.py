"""
MCP Server Template using Official SDK - Standalone Implementation

A simple template for creating MCP servers using the official MCP Python SDK.
"""

import json
import logging
import sys
from typing import Any, Dict, List

from mcp.server import Server
from mcp.types import Tool, TextContent


class MCPServerSDK:
    """
    MCP Server implementation using the official MCP Python SDK.

    This server provides:
    - Official MCP SDK integration
    - Basic server information tools
    - Echo functionality for testing
    - Proper logging and error handling
    """

    def __init__(self, name: str, version: str):
        """
        Initialize the MCP server with official SDK.

        Args:
            name: The server name
            version: The server version
        """
        self.name = name
        self.version = version
        self.server = Server(name)
        self.logger = self._setup_logging()

        # Register tools
        self._register_tools()

        self.logger.info(f"Initialized {name} v{version} with MCP SDK")

    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)

        # Create console handler if not already exists
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _register_tools(self) -> None:
        """Register MCP tools using the official SDK"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="get_server_info",
                    description="Get server information including capabilities",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="echo",
                    description="Echo back the provided message",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "The message to echo back",
                            }
                        },
                        "required": ["message"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls using the MCP SDK"""
            try:
                if name == "get_server_info":
                    result = self.get_server_info()
                elif name == "echo":
                    result = self.echo_message(arguments.get("message", ""))
                else:
                    result = {"error": f"Unknown tool: {name}"}

                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            except Exception as e:
                self.logger.error(f"Error in tool {name}: {str(e)}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    def get_server_info(self) -> Dict[str, Any]:
        """
        Get server information including capabilities.

        Returns:
            Dictionary containing server metadata
        """
        return {
            "name": self.name,
            "version": self.version,
            "sdk": "official-mcp-python",
            "capabilities": {
                "tools": ["get_server_info", "echo"],
            },
        }

    def echo_message(self, message: str) -> Dict[str, Any]:
        """
        Echo back a message.

        Args:
            message: The message to echo

        Returns:
            Dictionary containing the echoed message
        """
        self.logger.info(f"Echoing message: {message}")
        return {
            "echoed_message": message,
            "server": self.name,
            "timestamp": self._get_timestamp(),
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO string"""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()

    async def run(self) -> None:
        """Run the MCP server using the official SDK"""
        self.logger.info(f"Starting {self.name} v{self.version} with MCP SDK")
        await self.server.run()


# Factory function for consistency
def create_mcp_server(
    name: str = "template-server", version: str = "1.0.0"
) -> MCPServerSDK:
    """Factory function to create an MCP server instance"""
    return MCPServerSDK(name, version)


# For backward compatibility
MCPServer = MCPServerSDK
