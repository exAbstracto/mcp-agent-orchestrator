#!/usr/bin/env python3
"""
Real MCP Server Implementation using Official MCP Python SDK
Demonstrates proper tool registration and coordination capabilities
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime

from mcp import StdioServerParameters, types
from mcp.server import Server
from mcp.server.stdio import stdio_server


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CoordinationMCPServer:
    """
    Real MCP Server for Agent Coordination
    Uses official MCP Python SDK for proper protocol compliance
    """
    
    def __init__(self, agent_id: str, role: str):
        self.agent_id = agent_id
        self.role = role
        self.server = Server(f"coordination-server-{agent_id}")
        self.messages = []
        self.artifacts = {}
        
        # Register tools
        self._register_tools()
        
    def _register_tools(self):
        """Register MCP tools for coordination"""
        
        # Tool: Send message to other agents
        @self.server.list_tools()
        async def list_tools() -> List[types.Tool]:
            return [
                types.Tool(
                    name="send_message",
                    description=f"Send a coordination message from {self.role} agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "to_agent": {"type": "string", "description": "Target agent ID"},
                            "message": {"type": "string", "description": "Message content"},
                            "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"}
                        },
                        "required": ["to_agent", "message"]
                    }
                ),
                types.Tool(
                    name="create_artifact",
                    description=f"Create a code artifact as {self.role}",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "name": {"type": "string", "description": "Artifact name"},
                            "type": {"type": "string", "enum": ["code", "docs", "test", "config"]},
                            "content": {"type": "string", "description": "Artifact content"},
                            "language": {"type": "string", "description": "Programming language"}
                        },
                        "required": ["name", "type", "content"]
                    }
                ),
                types.Tool(
                    name="get_coordination_status",
                    description="Get current coordination status and recent messages",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_history": {"type": "boolean", "default": True}
                        }
                    }
                )
            ]
            
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Handle tool calls"""
            
            if name == "send_message":
                return await self._send_message(arguments)
            elif name == "create_artifact":
                return await self._create_artifact(arguments)
            elif name == "get_coordination_status":
                return await self._get_coordination_status(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _send_message(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Send coordination message"""
        message = {
            "id": f"msg_{len(self.messages) + 1}",
            "timestamp": datetime.now().isoformat(),
            "from_agent": self.agent_id,
            "from_role": self.role,
            "to_agent": args["to_agent"],
            "content": args["message"],
            "priority": args.get("priority", "medium")
        }
        
        self.messages.append(message)
        
        # Save to coordination file
        coordination_file = f"coordination-demo/shared-workspace/messages_{self.agent_id}.json"
        try:
            with open(coordination_file, 'w') as f:
                json.dump(self.messages, f, indent=2)
            
            logger.info(f"📤 {self.role} sent message to {args['to_agent']}: {args['message']}")
            
            return [types.TextContent(
                type="text",
                text=f"✅ Message sent from {self.role} to {args['to_agent']}\n"
                     f"📄 Saved to: {coordination_file}\n"
                     f"🕐 Timestamp: {message['timestamp']}"
            )]
            
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            return [types.TextContent(
                type="text", 
                text=f"❌ Failed to send message: {str(e)}"
            )]
    
    async def _create_artifact(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Create code artifact"""
        artifact = {
            "id": f"artifact_{len(self.artifacts) + 1}",
            "name": args["name"],
            "type": args["type"],
            "content": args["content"],
            "language": args.get("language", "text"),
            "created_by": self.agent_id,
            "role": self.role,
            "timestamp": datetime.now().isoformat()
        }
        
        self.artifacts[artifact["id"]] = artifact
        
        # Save artifact file
        artifact_file = f"coordination-demo/shared-workspace/artifacts_{self.agent_id}.json"
        try:
            with open(artifact_file, 'w') as f:
                json.dump(self.artifacts, f, indent=2)
            
            logger.info(f"🎨 {self.role} created artifact: {args['name']} ({args['type']})")
            
            return [types.TextContent(
                type="text",
                text=f"✅ Artifact '{args['name']}' created by {self.role}\n"
                     f"📄 Type: {args['type']}\n"
                     f"💾 Saved to: {artifact_file}\n"
                     f"🕐 Timestamp: {artifact['timestamp']}"
            )]
            
        except Exception as e:
            logger.error(f"Failed to save artifact: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Failed to create artifact: {str(e)}"
            )]
    
    async def _get_coordination_status(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Get coordination status"""
        include_history = args.get("include_history", True)
        
        status = {
            "agent_id": self.agent_id,
            "role": self.role,
            "message_count": len(self.messages),
            "artifact_count": len(self.artifacts),
            "last_activity": datetime.now().isoformat()
        }
        
        response = f"📊 Coordination Status for {self.role} Agent ({self.agent_id})\n"
        response += f"📨 Messages: {status['message_count']}\n"
        response += f"🎨 Artifacts: {status['artifact_count']}\n"
        response += f"🕐 Last Activity: {status['last_activity']}\n"
        
        if include_history and self.messages:
            response += "\n📋 Recent Messages:\n"
            for msg in self.messages[-3:]:  # Last 3 messages
                response += f"  • To {msg['to_agent']}: {msg['content'][:50]}...\n"
        
        if include_history and self.artifacts:
            response += "\n🎨 Recent Artifacts:\n"
            for art_id, art in list(self.artifacts.items())[-3:]:  # Last 3 artifacts
                response += f"  • {art['name']} ({art['type']})\n"
        
        return [types.TextContent(type="text", text=response)]


async def main():
    """Main server entry point"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python real-mcp-server.py <agent_id> <role>")
        print("Example: python real-mcp-server.py agent-001 backend-dev")
        sys.exit(1)
    
    agent_id = sys.argv[1]
    role = sys.argv[2]
    
    # Create coordination server
    coord_server = CoordinationMCPServer(agent_id, role)
    
    logger.info(f"🚀 Starting MCP Coordination Server for {role} (ID: {agent_id})")
    
    # Run stdio server
    async with stdio_server() as (read, write):
        await coord_server.server.run(read, write, coord_server.server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main()) 