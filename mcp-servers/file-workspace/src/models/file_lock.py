"""
File Lock Models for US-009: Shared Workspace File Locking

Defines data structures for file locking functionality.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
import uuid


class LockStatus(Enum):
    """Enumeration of possible file lock statuses"""
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    QUEUED = "queued"
    EXPIRED = "expired"


@dataclass
class FileLock:
    """Represents a file lock with metadata"""
    lock_id: str
    file_path: str
    agent_id: str
    acquired_at: datetime
    expires_at: datetime
    status: LockStatus
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        """Validate file lock data after initialization"""
        if not self.file_path:
            raise ValueError("File path cannot be empty")
        if not self.agent_id:
            raise ValueError("Agent ID cannot be empty")
        if self.expires_at <= self.acquired_at:
            raise ValueError("Expiry time must be after acquisition time")
    
    @classmethod
    def create(cls, file_path: str, agent_id: str, timeout_seconds: int) -> 'FileLock':
        """Factory method to create a new file lock"""
        if timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")
        
        now = datetime.now()
        expires_at = now + timedelta(seconds=timeout_seconds)
        
        return cls(
            lock_id=str(uuid.uuid4()),
            file_path=file_path,
            agent_id=agent_id,
            acquired_at=now,
            expires_at=expires_at,
            status=LockStatus.LOCKED,
            metadata={}
        )
    
    def is_expired(self) -> bool:
        """Check if the lock has expired"""
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "lock_id": self.lock_id,
            "file_path": self.file_path,
            "agent_id": self.agent_id,
            "acquired_at": self.acquired_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status.value,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileLock':
        """Create FileLock from dictionary"""
        return cls(
            lock_id=data["lock_id"],
            file_path=data["file_path"],
            agent_id=data["agent_id"],
            acquired_at=datetime.fromisoformat(data["acquired_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            status=LockStatus(data["status"]),
            metadata=data.get("metadata", {})
        )


@dataclass
class QueuedLockRequest:
    """Represents a queued lock request"""
    request_id: str
    file_path: str
    agent_id: str
    timeout_seconds: int
    requested_at: datetime
    position: int
    estimated_wait_time: float
    
    def __post_init__(self):
        """Validate queued request data"""
        if not self.file_path:
            raise ValueError("File path cannot be empty")
        if not self.agent_id:
            raise ValueError("Agent ID cannot be empty")
        if self.timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")
        if self.position < 1:
            raise ValueError("Queue position must be positive")
    
    @classmethod
    def create(cls, file_path: str, agent_id: str, timeout_seconds: int, position: int, estimated_wait_time: float = 0.0) -> 'QueuedLockRequest':
        """Factory method to create a new queued request"""
        return cls(
            request_id=str(uuid.uuid4()),
            file_path=file_path,
            agent_id=agent_id,
            timeout_seconds=timeout_seconds,
            requested_at=datetime.now(),
            position=position,
            estimated_wait_time=estimated_wait_time
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "request_id": self.request_id,
            "file_path": self.file_path,
            "agent_id": self.agent_id,
            "timeout_seconds": self.timeout_seconds,
            "requested_at": self.requested_at.isoformat(),
            "position": self.position,
            "estimated_wait_time": self.estimated_wait_time
        }


# Import timedelta here to avoid circular imports
from datetime import timedelta