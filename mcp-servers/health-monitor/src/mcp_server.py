"""
Basic MCP Server Template Implementation

This module provides a minimal MCP server implementation that follows
the Model Context Protocol specification.
"""

import json
import logging
import sys
from typing import Dict, Any, Optional, Union


class MCPServer:
    """
    Basic MCP Server implementation following the Model Context Protocol.

    This server provides a minimal implementation with:
    - JSON-RPC 2.0 protocol handling
    - Basic error handling and logging
    - Capability registration system
    - Initialize method support
    """

    def __init__(self, name: str, version: str):
        """
        Initialize the MCP server.

        Args:
            name: The server name
            version: The server version
        """
        self.name = name
        self.version = version
        self.capabilities: Dict[str, Any] = {}
        self.logger = self._setup_logging()
        self.logger.info(f"Initializing {name} v{version}")

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

    def get_server_info(self) -> Dict[str, Any]:
        """
        Get server information including capabilities.

        Returns:
            Dictionary containing server metadata
        """
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": self.capabilities,
        }

    def register_capability(self, name: str, config: Dict[str, Any]) -> None:
        """
        Register a capability with the server.

        Args:
            name: The capability name
            config: The capability configuration
        """
        self.capabilities[name] = config
        self.logger.info(f"Registered capability: {name}")

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a JSON-RPC 2.0 request.

        Args:
            request: The JSON-RPC request object

        Returns:
            The JSON-RPC response object
        """
        # Validate basic JSON-RPC structure
        if not isinstance(request, dict):
            return self._create_error_response(None, -32600, "Invalid Request")

        request_id = request.get("id")

        # Check required fields
        if "jsonrpc" not in request or "method" not in request:
            return self._create_error_response(request_id, -32600, "Invalid Request")

        method = request.get("method")
        params = request.get("params", {})

        self.logger.info(f"Handling request: {method}")

        # Route to appropriate handler
        if method == "initialize":
            return self._handle_initialize(request_id, params)
        else:
            return self._create_error_response(request_id, -32601, "Method not found")

    def _handle_initialize(
        self, request_id: Union[str, int, None], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle the initialize method.

        Args:
            request_id: The request ID
            params: The request parameters

        Returns:
            The initialize response
        """
        protocol_version = params.get("protocolVersion", "1.0.0")
        client_info = params.get("clientInfo", {})

        self.logger.info(
            f"Client {client_info.get('name', 'unknown')} "
            f"v{client_info.get('version', 'unknown')} connected"
        )

        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": protocol_version,
                "serverInfo": {"name": self.name, "version": self.version},
                "capabilities": self.capabilities,
            },
        }

        return response

    def _create_error_response(
        self, request_id: Union[str, int, None], code: int, message: str
    ) -> Dict[str, Any]:
        """
        Create a JSON-RPC error response.

        Args:
            request_id: The request ID (can be None)
            code: The error code
            message: The error message

        Returns:
            The error response object
        """
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message},
        }
