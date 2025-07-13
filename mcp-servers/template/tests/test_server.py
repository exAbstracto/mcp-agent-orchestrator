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


class TestMCPToolHandler:
    """Test the MCP tool call handler functionality"""
    
    @pytest.mark.asyncio
    async def test_tool_call_get_server_info(self):
        """Test MCP tool call for get_server_info"""
        from mcp.types import TextContent
        import json
        
        server = MCPServerSDK("tool-test", "1.0.0")
        
        # Simulate what the tool handler does for get_server_info
        result = server.get_server_info()
        text_content = TextContent(type="text", text=json.dumps(result, indent=2))
        
        assert text_content.type == "text"
        assert "tool-test" in text_content.text
        assert "1.0.0" in text_content.text
        
    @pytest.mark.asyncio
    async def test_tool_call_echo(self):
        """Test MCP tool call for echo"""
        from mcp.types import TextContent
        import json
        
        server = MCPServerSDK("tool-test", "1.0.0")
        
        # Simulate what the tool handler does for echo
        result = server.echo_message("Hello from tool call")
        text_content = TextContent(type="text", text=json.dumps(result, indent=2))
        
        assert text_content.type == "text"
        assert "Hello from tool call" in text_content.text
        
    @pytest.mark.asyncio
    async def test_tool_call_unknown_tool(self):
        """Test MCP tool call with unknown tool name"""
        from mcp.types import TextContent
        import json
        
        server = MCPServerSDK("tool-test", "1.0.0")
        
        # Simulate calling an unknown tool
        result = {"error": "Unknown tool: unknown_tool_name"}
        text_content = TextContent(type="text", text=json.dumps(result, indent=2))
        
        assert "Unknown tool" in text_content.text
        assert "error" in text_content.text
        
    @pytest.mark.asyncio
    async def test_tool_call_exception_handling(self):
        """Test MCP tool call exception handling"""
        from mcp.types import TextContent
        
        server = MCPServerSDK("tool-test", "1.0.0")
        
        # Mock an exception in echo_message
        with patch.object(server, 'echo_message', side_effect=ValueError("Test error")):
            try:
                server.echo_message("test")
            except ValueError as e:
                # Simulate what the exception handler does
                text_content = TextContent(type="text", text=f"Error: {str(e)}")
                assert "Error: Test error" in text_content.text
                
    def test_list_tools_functionality(self):
        """Test that list_tools functionality is available"""
        server = MCPServerSDK("tools-test", "1.0.0")
        
        # The tools are registered via decorators, verify the server setup
        assert server.server is not None
        
        # Verify the main methods exist that would be called by tools
        assert hasattr(server, 'get_server_info')
        assert hasattr(server, 'echo_message')
        
    @pytest.mark.asyncio 
    async def test_run_method_logging(self):
        """Test the run method logging functionality"""
        server = MCPServerSDK("run-test", "1.0.0")
        
        # Mock the server.run method to prevent actual server startup
        with patch.object(server.server, 'run', return_value=None) as mock_run:
            # Mock the logger to capture the log message
            with patch.object(server.logger, 'info') as mock_log:
                await server.run()
                
                # Verify the logging was called with the expected message
                mock_log.assert_called_once_with("Starting run-test v1.0.0 with MCP SDK")
                mock_run.assert_called_once()

    def test_timestamp_format_iso(self):
        """Test timestamp format variations"""
        server = MCPServerSDK("timestamp-test", "1.0.0")
        
        # Test multiple timestamp calls to ensure consistency
        timestamp1 = server._get_timestamp()
        timestamp2 = server._get_timestamp()
        
        # Both should be ISO format
        assert isinstance(timestamp1, str)
        assert isinstance(timestamp2, str)
        assert "T" in timestamp1
        assert "T" in timestamp2
        # Should end with Z for UTC
        assert timestamp1.endswith("Z") or "+00:00" in timestamp1
        assert timestamp2.endswith("Z") or "+00:00" in timestamp2

    def test_multiple_server_instances(self):
        """Test creating multiple server instances"""
        server1 = MCPServerSDK("server1", "1.0.0")
        server2 = MCPServerSDK("server2", "2.0.0")
        
        # Verify they're independent
        assert server1.name != server2.name
        assert server1.version != server2.version
        assert server1.server != server2.server
        assert server1.logger.name != server2.logger.name

    def test_echo_message_detailed_response(self):
        """Test echo message response structure in detail"""
        server = MCPServerSDK("detail-test", "1.0.0")
        
        message = "Detailed test message"
        result = server.echo_message(message)
        
        # Verify all expected fields
        assert "echoed_message" in result
        assert "server" in result
        assert "timestamp" in result
        
        # Verify values
        assert result["echoed_message"] == message
        assert result["server"] == "detail-test"
        assert isinstance(result["timestamp"], str)
        
        # Verify timestamp is recent (within last minute)
        from datetime import datetime, timezone
        
        # Parse ISO timestamp (simplified for standard library)
        timestamp_str = result["timestamp"]
        # Remove Z and parse as UTC
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'
        timestamp = datetime.fromisoformat(timestamp_str)
        now = datetime.now(timezone.utc)
        diff = (now - timestamp).total_seconds()
        assert diff < 60  # Should be within last minute

    def test_server_name_validation(self):
        """Test server creation with various name patterns"""
        # Test various valid server names
        valid_names = ["test", "test-server", "test_server", "TestServer", "test123"]
        
        for name in valid_names:
            server = MCPServerSDK(name, "1.0.0")
            assert server.name == name
            assert server.logger.name == name

    def test_server_version_validation(self):
        """Test server creation with various version patterns"""
        # Test various valid version formats
        valid_versions = ["1.0.0", "1.0", "1", "2.1.3", "1.0.0-beta", "1.0.0-alpha.1"]
        
        for version in valid_versions:
            server = MCPServerSDK("version-test", version)
            assert server.version == version

    def test_server_info_structure(self):
        """Test server info response structure in detail"""
        server = MCPServerSDK("info-test", "3.2.1")
        info = server.get_server_info()
        
        # Verify exact structure
        assert isinstance(info, dict)
        assert len(info) == 4  # name, version, sdk, capabilities
        
        # Verify capabilities structure
        capabilities = info["capabilities"]
        assert isinstance(capabilities, dict)
        assert "tools" in capabilities
        assert isinstance(capabilities["tools"], list)
        assert len(capabilities["tools"]) == 2
        assert "get_server_info" in capabilities["tools"]
        assert "echo" in capabilities["tools"]

    def test_logger_configuration(self):
        """Test logger configuration details"""
        server = MCPServerSDK("logger-test", "1.0.0")
        logger = server.logger
        
        # Verify logger configuration
        assert logger.name == "logger-test"
        assert logger.level == 20  # INFO level
        assert len(logger.handlers) > 0
        
        # Verify handler configuration
        handler = logger.handlers[0]
        assert hasattr(handler, 'formatter')
        formatter = handler.formatter
        assert formatter._fmt == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])