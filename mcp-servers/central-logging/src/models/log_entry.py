"""
Log Entry Models for US-010: Centralized Logging System

Defines data structures for log entries and related components.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import uuid


class LogLevel(Enum):
    """Enumeration of possible log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """Represents a log entry with correlation tracking"""
    level: LogLevel
    message: str
    component: str
    correlation_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validate log entry data after initialization"""
        if not self.message:
            raise ValueError("message cannot be empty")
        if not self.component:
            raise ValueError("component cannot be empty")
        if not self.correlation_id:
            raise ValueError("correlation_id cannot be empty")
    
    @classmethod
    def create(cls, level: LogLevel, message: str, component: str, 
               correlation_id: str, metadata: Optional[Dict[str, Any]] = None) -> 'LogEntry':
        """Factory method to create a new log entry"""
        return cls(
            level=level,
            message=message,
            component=component,
            correlation_id=correlation_id,
            metadata=metadata or {}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "log_id": self.log_id,
            "level": self.level.value,
            "message": self.message,
            "component": self.component,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Create LogEntry from dictionary"""
        entry = cls(
            level=LogLevel(data["level"]),
            message=data["message"],
            component=data["component"],
            correlation_id=data["correlation_id"],
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            log_id=data.get("log_id", str(uuid.uuid4()))
        )
        return entry