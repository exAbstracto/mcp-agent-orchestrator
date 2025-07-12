"""
Agent Health Models for US-008: Agent Health Monitoring

Defines data structures for agent health tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass


class HealthStatus(Enum):
    """Enumeration of possible agent health statuses"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    OFFLINE = "offline"


@dataclass
class AgentHealth:
    """Represents the health status of an agent at a specific point in time"""
    agent_id: str
    timestamp: datetime
    status: HealthStatus
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentHealth":
        """Create AgentHealth from dictionary"""
        return cls(
            agent_id=data["agent_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            status=HealthStatus(data["status"]),
            metadata=data.get("metadata", {})
        )


@dataclass
class AlertData:
    """Represents an alert for an unhealthy agent"""
    agent_id: str
    severity: str
    reason: str
    timestamp: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "agent_id": self.agent_id,
            "severity": self.severity,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }