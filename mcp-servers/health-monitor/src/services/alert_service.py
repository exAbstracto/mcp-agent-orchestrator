"""
Alert Service for US-008: Agent Health Monitoring

Manages alerts for unhealthy agents.
"""

from datetime import datetime
from typing import Dict, Any, List
import logging

from ..models.agent_health import AlertData


class AlertService:
    """Service for managing health-related alerts"""
    
    def __init__(self):
        """Initialize the alert service"""
        self._alerts: List[AlertData] = []
        self.logger = logging.getLogger(__name__)
    
    def send_alert(self, agent_id: str, reason: str, metadata: Dict[str, Any] = None) -> None:
        """Send an alert for an unhealthy agent"""
        if metadata is None:
            metadata = {}
        
        alert = AlertData(
            agent_id=agent_id,
            severity="critical",
            reason=reason,
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        self._alerts.append(alert)
        
        # Log the alert
        self.logger.warning(
            f"ALERT: Agent {agent_id} is unhealthy. Reason: {reason}. "
            f"Metadata: {metadata}"
        )
    
    def create_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an alert from alert data dictionary"""
        alert = AlertData(
            agent_id=alert_data["agent_id"],
            severity="critical",  # Default to critical for health alerts
            reason=alert_data["reason"],
            timestamp=datetime.now(),
            metadata=alert_data.get("metadata", {})
        )
        
        self._alerts.append(alert)
        return alert.to_dict()
    
    def get_alerts(self, agent_id: str = None) -> List[Dict[str, Any]]:
        """Get alerts, optionally filtered by agent ID"""
        alerts = self._alerts
        
        if agent_id:
            alerts = [alert for alert in alerts if alert.agent_id == agent_id]
        
        return [alert.to_dict() for alert in alerts]
    
    def clear_alerts(self, agent_id: str = None) -> None:
        """Clear alerts, optionally for a specific agent"""
        if agent_id:
            self._alerts = [alert for alert in self._alerts if alert.agent_id != agent_id]
        else:
            self._alerts.clear()