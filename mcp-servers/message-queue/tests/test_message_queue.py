"""
Tests for Message Queue MCP Server using Official SDK

Test the new MCP SDK-based implementation to ensure it provides
the same functionality as the legacy implementation.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch

from src.message_queue_server_sdk import MessageQueueServerSDK, create_message_queue_server


class TestMessageQueueServerSDK:
    """Test cases for the MCP SDK-based message queue server"""
    
    def test_server_initialization(self):
        """Test that the server initializes correctly"""
        server = MessageQueueServerSDK("test-queue", "1.0.0")
        
        assert server.name == "test-queue"
        assert server.version == "1.0.0"
        assert server.server is not None
        assert server.message_queue is not None
        
    def test_factory_function(self):
        """Test the factory function creates server correctly"""
        server = create_message_queue_server("factory-test", "2.0.0")
        
        assert isinstance(server, MessageQueueServerSDK)
        assert server.name == "factory-test"
        assert server.version == "2.0.0"
        
    def test_factory_function_defaults(self):
        """Test the factory function with default parameters"""
        server = create_message_queue_server()
        
        assert isinstance(server, MessageQueueServerSDK)
        assert server.name == "message-queue"
        assert server.version == "1.0.0"
    
    def test_publish_message_functionality(self):
        """Test the publish message functionality"""
        server = MessageQueueServerSDK("test-queue", "1.0.0")
        
        # Test publishing a message
        result = server._publish_message({
            "channel": "test-channel",
            "content": "Hello, World!",
            "sender": "test-agent"
        })
        
        assert "message_id" in result
        assert result["channel"] == "test-channel"
        assert "timestamp" in result
        assert "latency_ms" in result
    
    def test_subscribe_channel_functionality(self):
        """Test the channel subscription functionality"""
        server = MessageQueueServerSDK("test-queue", "1.0.0")
        
        # Test subscribing to a channel
        result = server._subscribe_channel({
            "channel": "test-channel",
            "agent_id": "test-agent"
        })
        
        assert result["subscribed"] is True
        assert result["channel"] == "test-channel"
        assert result["agent_id"] == "test-agent"
    
    def test_list_channels_functionality(self):
        """Test the list channels functionality"""
        server = MessageQueueServerSDK("test-queue", "1.0.0")
        
        # Subscribe to a channel first
        server._subscribe_channel({
            "channel": "test-channel",
            "agent_id": "test-agent"
        })
        
        # List channels
        result = server._list_channels({})
        
        assert "channels" in result
        # Should contain our test channel
        channel_names = [ch["name"] for ch in result["channels"]]
        assert "test-channel" in channel_names
    
    def test_get_performance_metrics_functionality(self):
        """Test the performance metrics functionality"""
        server = MessageQueueServerSDK("test-queue", "1.0.0")
        
        # Get metrics
        result = server._get_performance_metrics({})
        
        assert "messages_sent" in result
        assert "messages_delivered" in result  
        assert "channels_count" in result
    
    @pytest.mark.asyncio
    async def test_server_lifecycle(self):
        """Test server start and stop lifecycle"""
        server = MessageQueueServerSDK("test-queue", "1.0.0")
        
        # Test start
        await server.start()
        assert server.message_queue._running is True
        
        # Test stop
        await server.stop()
        assert server.message_queue._running is False
    
    def test_server_tools_registration(self):
        """Test that tools are registered correctly"""
        server = MessageQueueServerSDK("test-queue", "1.0.0")
        
        # Verify server has the MCP server instance
        assert server.server is not None
        
        # The tools are registered via decorators, so we can't easily test them
        # without actually running the server, but we can verify the methods exist
        assert hasattr(server, '_publish_message')
        assert hasattr(server, '_subscribe_channel')
        assert hasattr(server, '_unsubscribe_channel')
        assert hasattr(server, '_get_messages')
        assert hasattr(server, '_acknowledge_message')
        assert hasattr(server, '_get_performance_metrics')
        assert hasattr(server, '_list_channels')


class TestSDKMessageQueueIntegration:
    """Test integration between SDK wrapper and legacy message queue"""
    
    def test_message_publishing_and_retrieval(self):
        """Test complete message publishing and retrieval workflow"""
        server = MessageQueueServerSDK("integration-test", "1.0.0")
        
        # Subscribe to channel
        server._subscribe_channel({
            "channel": "integration-channel",
            "agent_id": "test-agent"
        })
        
        # Publish message
        publish_result = server._publish_message({
            "channel": "integration-channel",
            "content": "Integration test message",
            "sender": "test-sender"
        })
        
        assert "message_id" in publish_result
        message_id = publish_result["message_id"]
        
        # Get messages for subscriber
        messages_result = server._get_messages({
            "agent_id": "test-agent",
            "channel": "integration-channel"
        })
        
        assert "messages" in messages_result
        messages = messages_result["messages"]
        assert len(messages) > 0
        
        # Find our message
        our_message = None
        for msg in messages:
            if msg["id"] == message_id:
                our_message = msg
                break
        
        assert our_message is not None
        assert our_message["content"] == "Integration test message"
        assert our_message["sender"] == "test-sender"
        assert our_message["channel"] == "integration-channel"
    
    def test_subscription_and_unsubscription(self):
        """Test channel subscription and unsubscription"""
        server = MessageQueueServerSDK("subscription-test", "1.0.0")
        
        # Subscribe
        subscribe_result = server._subscribe_channel({
            "channel": "sub-test-channel",
            "agent_id": "sub-test-agent"
        })
        assert subscribe_result["subscribed"] is True
        
        # Verify subscription in channel list
        channels_result = server._list_channels({})
        channel_names = [ch["name"] for ch in channels_result["channels"]]
        assert "sub-test-channel" in channel_names
        
        # Unsubscribe
        unsubscribe_result = server._unsubscribe_channel({
            "channel": "sub-test-channel",
            "agent_id": "sub-test-agent"
        })
        assert unsubscribe_result["unsubscribed"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])