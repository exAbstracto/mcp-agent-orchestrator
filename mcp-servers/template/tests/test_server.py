"""
Tests for MCP Server Template using Official SDK

Test the new MCP SDK-based implementation to ensure it provides
the same functionality as the legacy implementation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.mcp_server_sdk import MCPServerSDK, create_mcp_server


class TestMCPServerSDK:
    """Test cases for the MCP SDK-based server template"""
    
    def test_server_initialization(self):
        """Test that the server initializes with correct metadata"""
        server = MCPServerSDK("test-server", "1.0.0")
        
        assert server.name == "test-server"
        assert server.version == "1.0.0"
        assert server.server is not None
        assert server.logger is not None
        
    def test_server_info_response(self):
        """Test the server info response format"""
        server = MCPServerSDK("test-server", "1.0.0")
        info = server.get_server_info()
        
        assert info["name"] == "test-server"
        assert info["version"] == "1.0.0"
        assert info["sdk"] == "official-mcp-python"
        assert "capabilities" in info
        assert "tools" in info["capabilities"]
        
    def test_echo_message_functionality(self):
        """Test the echo message tool functionality"""
        server = MCPServerSDK("test-server", "1.0.0")
        
        result = server.echo_message("Hello, MCP SDK!")
        
        assert result["echoed_message"] == "Hello, MCP SDK!"
        assert result["server"] == "test-server"
        assert "timestamp" in result
        
    def test_factory_function(self):
        """Test the factory function creates server correctly"""
        server = create_mcp_server("factory-test", "2.0.0")
        
        assert isinstance(server, MCPServerSDK)
        assert server.name == "factory-test"
        assert server.version == "2.0.0"
        
    def test_factory_function_defaults(self):
        """Test the factory function with default parameters"""
        server = create_mcp_server()
        
        assert isinstance(server, MCPServerSDK)
        assert server.name == "template-server"
        assert server.version == "1.0.0"
        
    def test_logging_initialization(self):
        """Test that logging is properly configured"""
        server = MCPServerSDK("test-server", "1.0.0")
        
        assert server.logger is not None
        assert server.logger.name == "test-server"
        
    @pytest.mark.asyncio
    async def test_server_can_be_created_and_started(self):
        """Test that server can be created and has run method"""
        server = MCPServerSDK("test-server", "1.0.0")
        
        # Just verify the run method exists - we won't actually run it in tests
        assert hasattr(server, 'run')
        assert callable(server.run)
        
    def test_server_tools_registration(self):
        """Test that tools are registered correctly"""
        server = MCPServerSDK("test-server", "1.0.0")
        
        # Verify server has the MCP server instance
        assert server.server is not None
        
        # The tools are registered via decorators, so we can't easily test them
        # without actually running the server, but we can verify the methods exist
        assert hasattr(server, 'get_server_info')
        assert hasattr(server, 'echo_message')
        assert callable(server.get_server_info)
        assert callable(server.echo_message)


class TestSDKCompatibility:
    """Test that SDK implementation maintains compatibility with legacy interface"""
    
    def test_server_info_contains_expected_fields(self):
        """Test that server info contains all expected fields for compatibility"""
        server = MCPServerSDK("compat-test", "1.0.0")
        info = server.get_server_info()
        
        # Fields that should be present for compatibility
        required_fields = ["name", "version", "capabilities"]
        for field in required_fields:
            assert field in info, f"Missing required field: {field}"
            
    def test_echo_functionality_works(self):
        """Test that echo functionality works correctly"""
        server = MCPServerSDK("echo-test", "1.0.0")
        
        test_message = "Test message for echo"
        result = server.echo_message(test_message)
        
        assert "echoed_message" in result
        assert result["echoed_message"] == test_message
        
    def test_server_name_and_version_accessible(self):
        """Test that server name and version are accessible"""
        server = MCPServerSDK("access-test", "1.5.0")
        
        assert server.name == "access-test"
        assert server.version == "1.5.0"

    def test_echo_with_empty_message(self):
        """Test echo functionality with empty message"""
        server = MCPServerSDK("test-server", "1.0.0")
        
        result = server.echo_message("")
        assert result["echoed_message"] == ""
        assert result["server"] == "test-server"

    def test_get_timestamp_format(self):
        """Test timestamp generation"""
        server = MCPServerSDK("test-server", "1.0.0")
        
        timestamp = server._get_timestamp()
        assert isinstance(timestamp, str)
        # Should be ISO format
        assert "T" in timestamp
        assert timestamp.endswith("Z") or "+" in timestamp

    def test_server_has_mcp_server_instance(self):
        """Test that server has MCP server instance"""
        server = MCPServerSDK("test-server", "1.0.0")
        
        assert hasattr(server, 'server')
        assert server.server is not None

    @pytest.mark.asyncio
    async def test_server_run_method_exists(self):
        """Test that server run method exists and is callable"""
        server = MCPServerSDK("test-server", "1.0.0")
        
        assert hasattr(server, 'run')
        assert callable(server.run)
        # Note: We can't actually run it in tests as it would start the server

    def test_echo_with_special_characters(self):
        """Test echo functionality with special characters"""
        server = MCPServerSDK("test-server", "1.0.0")
        
        special_message = "Hello! @#$%^&*()_+ 🚀"
        result = server.echo_message(special_message)
        assert result["echoed_message"] == special_message

    def test_server_logging_setup(self):
        """Test that logging is properly set up"""
        server = MCPServerSDK("test-logger", "1.0.0")
        
        assert hasattr(server, 'logger')
        assert server.logger.name == "test-logger"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])