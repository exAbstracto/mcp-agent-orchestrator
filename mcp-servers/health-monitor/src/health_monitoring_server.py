"""
Health Monitoring Server for US-008: Agent Health Monitoring

MCP server that provides health monitoring capabilities for AI agents.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent

from .models.agent_health import AgentHealth, HealthStatus
from .services.heartbeat_service import HeartbeatService
from .services.alert_service import AlertService


class HealthMonitoringServer:
    """MCP server for agent health monitoring using official MCP SDK"""
    
    def __init__(self, name: str, version: str):
        """Initialize the health monitoring server"""
        self.name = name
        self.version = version
        self.server = Server(name)
        
        # Initialize services
        self.heartbeat_service = HeartbeatService()
        self.alert_service = AlertService()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self) -> None:
        """Register MCP tools for health monitoring"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available health monitoring tools"""
            return [
                Tool(
                    name="send_heartbeat",
                    description="Send a heartbeat signal from an agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {"type": "string", "description": "Unique identifier for the agent"},
                            "timestamp": {"type": "string", "description": "ISO timestamp of the heartbeat"},
                            "status": {"type": "string", "enum": ["healthy", "unhealthy", "unknown"], "description": "Current agent status"},
                            "metadata": {"type": "object", "description": "Additional agent metadata (CPU, memory, etc.)"}
                        },
                        "required": ["agent_id", "timestamp", "status"]
                    }
                ),
                Tool(
                    name="get_agent_status",
                    description="Get the current status of a specific agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {"type": "string", "description": "Unique identifier for the agent"}
                        },
                        "required": ["agent_id"]
                    }
                ),
                Tool(
                    name="get_all_agents_status",
                    description="Get the status of all known agents",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_agent_health_history",
                    description="Get health history for an agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {"type": "string", "description": "Unique identifier for the agent"},
                            "hours": {"type": "integer", "default": 24, "description": "Number of hours of history to retrieve"}
                        },
                        "required": ["agent_id"]
                    }
                ),
                Tool(
                    name="get_unhealthy_agents",
                    description="Get list of agents that are currently unhealthy",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "timeout_seconds": {"type": "integer", "default": 30, "description": "Heartbeat timeout in seconds"}
                        },
                        "additionalProperties": False
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                if name == "send_heartbeat":
                    result = self.send_heartbeat(arguments)
                elif name == "get_agent_status":
                    result = self.get_agent_status(arguments["agent_id"])
                elif name == "get_all_agents_status":
                    result = self.get_all_agents_status()
                elif name == "get_agent_health_history":
                    agent_id = arguments["agent_id"]
                    hours = arguments.get("hours", 24)
                    result = self.get_agent_health_history(agent_id, hours)
                elif name == "get_unhealthy_agents":
                    timeout = arguments.get("timeout_seconds", 30)
                    result = self.get_unhealthy_agents(timeout)
                else:
                    result = {"error": f"Unknown tool: {name}"}
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            except Exception as e:
                self.logger.error(f"Error in tool {name}: {str(e)}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    def send_heartbeat(self, heartbeat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a heartbeat from an agent"""
        # Validate required fields
        required_fields = ["agent_id", "timestamp", "status"]
        missing_fields = [field for field in required_fields if field not in heartbeat_data]
        
        if missing_fields:
            raise ValueError(f"Missing required heartbeat fields: {missing_fields}")
        
        # Create AgentHealth object
        try:
            heartbeat = AgentHealth(
                agent_id=heartbeat_data["agent_id"],
                timestamp=datetime.fromisoformat(heartbeat_data["timestamp"]),
                status=HealthStatus(heartbeat_data["status"]),
                metadata=heartbeat_data.get("metadata", {})
            )
        except ValueError as e:
            raise ValueError(f"Invalid heartbeat data: {str(e)}")
        
        # Record the heartbeat
        self.heartbeat_service.record_heartbeat(heartbeat)
        
        self.logger.info(f"Heartbeat received from agent {heartbeat.agent_id}")
        
        return {
            "success": True,
            "agent_id": heartbeat.agent_id,
            "timestamp": heartbeat.timestamp.isoformat(),
            "status": heartbeat.status.value
        }
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get the current status of a specific agent"""
        heartbeat = self.heartbeat_service.get_latest_heartbeat(agent_id)
        
        if not heartbeat:
            return {
                "status": "not_found",
                "error": f"Agent {agent_id} not found"
            }
        
        # Check if agent is unhealthy due to timeout
        unhealthy_agents = self.heartbeat_service.get_unhealthy_agents(timeout_seconds=30)
        is_unhealthy = any(agent.agent_id == agent_id for agent in unhealthy_agents)
        
        status = "unhealthy" if is_unhealthy else heartbeat.status.value
        
        return {
            "agent_id": agent_id,
            "status": status,
            "last_heartbeat": heartbeat.timestamp.isoformat(),
            "metadata": heartbeat.metadata
        }
    
    def get_all_agents_status(self) -> List[Dict[str, Any]]:
        """Get the status of all known agents"""
        all_agents = self.heartbeat_service.get_all_agents()
        return [self.get_agent_status(agent_id) for agent_id in all_agents]
    
    def get_agent_health_history(self, agent_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health history for an agent"""
        history = self.heartbeat_service.get_health_history(agent_id, hours)
        return [heartbeat.to_dict() for heartbeat in history]
    
    def get_unhealthy_agents(self, timeout_seconds: int = 30) -> List[Dict[str, Any]]:
        """Get list of agents that are currently unhealthy"""
        unhealthy_agents = self.heartbeat_service.get_unhealthy_agents(timeout_seconds)
        return [agent.to_dict() for agent in unhealthy_agents]
    
    def mark_agent_unhealthy(self, agent_id: str, reason: str) -> None:
        """Mark an agent as unhealthy and trigger alerts"""
        # Send alert
        self.alert_service.send_alert(
            agent_id=agent_id,
            reason=reason,
            metadata={"marked_unhealthy_at": datetime.now().isoformat()}
        )
        
        self.logger.warning(f"Agent {agent_id} marked as unhealthy: {reason}")
    
    async def run(self) -> None:
        """Run the health monitoring server"""
        self.logger.info(f"Starting {self.name} v{self.version}")
        await self.server.run()


# For compatibility with existing tests
def create_health_monitoring_server(name: str = "health-monitor", version: str = "1.0.0") -> HealthMonitoringServer:
    """Factory function to create health monitoring server"""
    return HealthMonitoringServer(name, version)