"""
Heartbeat Service for US-008: Agent Health Monitoring

Manages agent heartbeats and health status tracking.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from ..models.agent_health import AgentHealth, HealthStatus


class HeartbeatService:
    """Service for managing agent heartbeats and health status"""
    
    def __init__(self):
        """Initialize the heartbeat service"""
        # Store latest heartbeat for each agent
        self._latest_heartbeats: Dict[str, AgentHealth] = {}
        
        # Store health history for each agent (last 24 hours)
        self._health_history: Dict[str, List[AgentHealth]] = defaultdict(list)
    
    def record_heartbeat(self, heartbeat: AgentHealth) -> None:
        """Record a heartbeat from an agent"""
        agent_id = heartbeat.agent_id
        
        # Update latest heartbeat
        self._latest_heartbeats[agent_id] = heartbeat
        
        # Add to health history
        self._health_history[agent_id].append(heartbeat)
        
        # Prune old history for this agent
        self._prune_agent_history(agent_id)
    
    def get_latest_heartbeat(self, agent_id: str) -> Optional[AgentHealth]:
        """Get the latest heartbeat for an agent"""
        return self._latest_heartbeats.get(agent_id)
    
    def get_unhealthy_agents(self, timeout_seconds: int = 30) -> List[AgentHealth]:
        """Get list of agents that haven't sent heartbeats within timeout"""
        unhealthy_agents = []
        cutoff_time = datetime.now() - timedelta(seconds=timeout_seconds)
        
        for agent_id, heartbeat in self._latest_heartbeats.items():
            if heartbeat.timestamp < cutoff_time:
                # Create an unhealthy status for this agent
                unhealthy_heartbeat = AgentHealth(
                    agent_id=agent_id,
                    timestamp=heartbeat.timestamp,
                    status=HealthStatus.UNHEALTHY,
                    metadata={"reason": "heartbeat_timeout", "last_seen": heartbeat.timestamp.isoformat()}
                )
                unhealthy_agents.append(unhealthy_heartbeat)
        
        return unhealthy_agents
    
    def get_health_history(self, agent_id: str, hours: int = 24) -> List[AgentHealth]:
        """Get health history for an agent within specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        if agent_id not in self._health_history:
            return []
        
        # Filter history by time and sort by timestamp (most recent first)
        filtered_history = [
            heartbeat for heartbeat in self._health_history[agent_id]
            if heartbeat.timestamp >= cutoff_time
        ]
        
        return sorted(filtered_history, key=lambda h: h.timestamp, reverse=True)
    
    def prune_old_history(self) -> None:
        """Remove health history older than 24 hours for all agents"""
        for agent_id in self._health_history:
            self._prune_agent_history(agent_id)
    
    def _prune_agent_history(self, agent_id: str) -> None:
        """Remove old history for a specific agent"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        if agent_id in self._health_history:
            self._health_history[agent_id] = [
                heartbeat for heartbeat in self._health_history[agent_id]
                if heartbeat.timestamp >= cutoff_time
            ]
    
    def get_all_agents(self) -> List[str]:
        """Get list of all known agent IDs"""
        return list(self._latest_heartbeats.keys())