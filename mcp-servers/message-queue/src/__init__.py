"""
Message Queue MCP Server

A Model Context Protocol server providing async pub/sub messaging
for multi-agent coordination.
"""

# MCP Server implementation using official MCP SDK
from .message_queue_server_sdk import MessageQueueServerSDK, create_message_queue_server

# Default implementation
MessageQueueServer = MessageQueueServerSDK

__version__ = "1.0.0"
__author__ = "MCP Agent Orchestrator Team"
__all__ = ["MessageQueueServer", "MessageQueueServerSDK", "create_message_queue_server"]
