"""
Tests for the basic MCP server template
"""

import pytest
import json
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import MCPServer


class TestMCPServer:
    """Test cases for the basic MCP server template"""
    
    def test_server_initialization(self):
        """Test that the server initializes with correct metadata"""
        server = MCPServer("test-server", "1.0.0")
        
        assert server.name == "test-server"
        assert server.version == "1.0.0"
        assert server.capabilities is not None
        
    def test_server_info_response(self):
        """Test the server info response format"""
        server = MCPServer("test-server", "1.0.0")
        info = server.get_server_info()
        
        assert info["name"] == "test-server"
        assert info["version"] == "1.0.0"
        assert "capabilities" in info
        
    def test_handle_initialize_request(self):
        """Test handling of initialize request"""
        server = MCPServer("test-server", "1.0.0")
        
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
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["protocolVersion"] == "1.0.0"
        assert response["result"]["serverInfo"]["name"] == "test-server"
        
    def test_handle_unknown_method(self):
        """Test handling of unknown method requests"""
        server = MCPServer("test-server", "1.0.0")
        
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "unknown_method",
            "params": {}
        }
        
        response = server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 2
        assert "error" in response
        assert response["error"]["code"] == -32601  # Method not found
        
    def test_logging_initialization(self):
        """Test that logging is properly configured"""
        server = MCPServer("test-server", "1.0.0")
        
        assert server.logger is not None
        assert server.logger.name == "test-server"
        
    def test_error_handling_for_invalid_request(self):
        """Test error handling for invalid JSON-RPC requests"""
        server = MCPServer("test-server", "1.0.0")
        
        # Missing required fields
        invalid_request = {
            "method": "test"
        }
        
        response = server.handle_request(invalid_request)
        
        assert "error" in response
        assert response["error"]["code"] == -32600  # Invalid Request
        
    def test_capability_registration(self):
        """Test that capabilities can be registered"""
        server = MCPServer("test-server", "1.0.0")
        
        # Register a tool capability
        server.register_capability("tools", {
            "supported": True
        })
        
        info = server.get_server_info()
        assert "tools" in info["capabilities"]
        assert info["capabilities"]["tools"]["supported"] is True 