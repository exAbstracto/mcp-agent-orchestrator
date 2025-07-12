"""
Message Queue MCP Server using Official SDK - Standalone Implementation

This module provides a standalone MCP SDK-based message queue implementation
using the core business logic.
"""

import json
from typing import Any, Dict, List

from mcp.server import Server
from mcp.types import Tool, TextContent, Resource

# Import core business logic
from .core import MessageQueueCore


class MessageQueueServerSDK:
    """
    Message Queue MCP Server using the official MCP Python SDK.
    
    This server provides:
    - Official MCP SDK integration
    - Channel-based pub/sub messaging
    - Reliable delivery with retries
    - Performance monitoring
    - Message persistence and TTL
    """
    
    def __init__(self, name: str = "message-queue", version: str = "1.0.0"):
        """
        Initialize the MCP message queue server with official SDK.
        
        Args:
            name: The server name
            version: The server version
        """
        self.name = name
        self.version = version
        self.server = Server(name)
        
        # Initialize the core message queue logic
        self.message_queue = MessageQueueCore(name)
        
        # Register tools and resources
        self._register_tools()
        self._register_resources()
        
        self.message_queue.logger.info(f"Initialized {name} v{version} with MCP SDK")
    
    def _register_tools(self) -> None:
        """Register MCP tools using the official SDK"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available message queue tools"""
            return [
                Tool(
                    name="publish_message",
                    description="Publish a message to a channel",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "channel": {"type": "string", "description": "Channel name"},
                            "content": {"description": "Message content"},
                            "sender": {"type": "string", "description": "Sender agent ID"},
                            "priority": {"type": "integer", "default": 0, "description": "Message priority"},
                            "ttl_seconds": {"type": "number", "description": "Time to live in seconds"}
                        },
                        "required": ["channel", "content", "sender"]
                    }
                ),
                Tool(
                    name="subscribe_channel",
                    description="Subscribe to messages on a channel",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "channel": {"type": "string", "description": "Channel name"},
                            "agent_id": {"type": "string", "description": "Subscriber agent ID"},
                            "filters": {"type": "object", "description": "Optional message filters"}
                        },
                        "required": ["channel", "agent_id"]
                    }
                ),
                Tool(
                    name="unsubscribe_channel",
                    description="Unsubscribe from a channel",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "channel": {"type": "string", "description": "Channel name"},
                            "agent_id": {"type": "string", "description": "Agent ID"}
                        },
                        "required": ["channel", "agent_id"]
                    }
                ),
                Tool(
                    name="get_messages",
                    description="Get pending messages for an agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {"type": "string", "description": "Agent ID"},
                            "channel": {"type": "string", "description": "Optional channel filter"},
                            "limit": {"type": "integer", "default": 10, "description": "Maximum messages to return"}
                        },
                        "required": ["agent_id"]
                    }
                ),
                Tool(
                    name="acknowledge_message",
                    description="Acknowledge message delivery",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message_id": {"type": "string", "description": "Message ID"},
                            "agent_id": {"type": "string", "description": "Agent ID"}
                        },
                        "required": ["message_id", "agent_id"]
                    }
                ),
                Tool(
                    name="get_performance_metrics",
                    description="Get performance metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="list_channels",
                    description="List all active channels",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls using the MCP SDK"""
            try:
                # Route to the appropriate method using the core logic
                if name == "publish_message":
                    result = self._publish_message(arguments)
                elif name == "subscribe_channel":
                    result = self._subscribe_channel(arguments)
                elif name == "unsubscribe_channel":
                    result = self._unsubscribe_channel(arguments)
                elif name == "get_messages":
                    result = self._get_messages(arguments)
                elif name == "acknowledge_message":
                    result = self._acknowledge_message(arguments)
                elif name == "get_performance_metrics":
                    result = self._get_performance_metrics(arguments)
                elif name == "list_channels":
                    result = self._list_channels(arguments)
                else:
                    result = {"error": f"Unknown tool: {name}"}
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            except Exception as e:
                self.message_queue.logger.error(f"Error in tool {name}: {str(e)}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    def _register_resources(self) -> None:
        """Register MCP resources using the official SDK"""
        
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List available resources"""
            return [
                Resource(
                    uri="queue://metrics",
                    name="Performance Metrics",
                    description="Real-time performance metrics",
                    mimeType="application/json"
                ),
                Resource(
                    uri="queue://channels",
                    name="Channel List", 
                    description="List of active channels and subscribers",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read resource content"""
            if uri == "queue://metrics":
                metrics_data = self._get_performance_metrics({})
                return json.dumps(metrics_data, indent=2)
            elif uri == "queue://channels":
                channels_data = self._list_channels({})
                return json.dumps(channels_data, indent=2)
            else:
                raise ValueError(f"Unknown resource: {uri}")
    
    # Tool implementation methods that use the core business logic
    def _publish_message(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Publish a message using core logic"""
        try:
            return self.message_queue.publish_message(
                channel=arguments["channel"],
                content=arguments["content"],
                sender=arguments["sender"],
                priority=arguments.get("priority", 0),
                ttl_seconds=arguments.get("ttl_seconds")
            )
        except Exception as e:
            return {"error": str(e)}
    
    def _subscribe_channel(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Subscribe to channel using core logic"""
        try:
            return self.message_queue.subscribe_channel(
                channel=arguments["channel"],
                agent_id=arguments["agent_id"],
                filters=arguments.get("filters")
            )
        except Exception as e:
            return {"error": str(e)}
    
    def _unsubscribe_channel(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Unsubscribe from channel using core logic"""
        try:
            return self.message_queue.unsubscribe_channel(
                channel=arguments["channel"],
                agent_id=arguments["agent_id"]
            )
        except Exception as e:
            return {"error": str(e)}
    
    def _get_messages(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get messages using core logic"""
        try:
            return self.message_queue.get_messages(
                agent_id=arguments["agent_id"],
                channel_filter=arguments.get("channel"),
                limit=arguments.get("limit", 10)
            )
        except Exception as e:
            return {"error": str(e)}
    
    def _acknowledge_message(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Acknowledge message using core logic"""
        try:
            return self.message_queue.acknowledge_message(
                message_id=arguments["message_id"],
                agent_id=arguments["agent_id"]
            )
        except Exception as e:
            return {"error": str(e)}
    
    def _get_performance_metrics(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get performance metrics using core logic"""
        try:
            return self.message_queue.get_performance_metrics()
        except Exception as e:
            return {"error": str(e)}
    
    def _list_channels(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List channels using core logic"""
        try:
            return self.message_queue.list_channels()
        except Exception as e:
            return {"error": str(e)}
    
    async def start(self) -> None:
        """Start the message queue server background tasks"""
        await self.message_queue.start()
    
    async def stop(self) -> None:
        """Stop the message queue server background tasks"""
        await self.message_queue.stop()
    
    async def run(self) -> None:
        """Run the MCP server using the official SDK"""
        self.message_queue.logger.info(f"Starting {self.name} v{self.version} with MCP SDK")
        await self.start()
        try:
            await self.server.run()
        finally:
            await self.stop()


# Factory function for consistency
def create_message_queue_server(name: str = "message-queue", version: str = "1.0.0") -> MessageQueueServerSDK:
    """Factory function to create a message queue server instance"""
    return MessageQueueServerSDK(name, version)


# For backward compatibility during migration
MessageQueueServer = MessageQueueServerSDK