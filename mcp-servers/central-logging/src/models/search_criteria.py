"""
Search Criteria Models for US-010: Centralized Logging System

Defines data structures for log search and filtering.
"""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from .log_entry import LogLevel


@dataclass
class TimeRange:
    """Represents a time range for log searches"""
    start: datetime
    end: datetime
    
    def __post_init__(self):
        """Validate time range"""
        if self.start >= self.end:
            raise ValueError("Start time must be before end time")
    
    def contains(self, timestamp: datetime) -> bool:
        """Check if timestamp falls within this range"""
        return self.start <= timestamp <= self.end


@dataclass
class SearchCriteria:
    """Represents search criteria for log queries"""
    component: Optional[str] = None
    level: Optional[LogLevel] = None
    correlation_id: Optional[str] = None
    message_contains: Optional[str] = None
    time_range: Optional[TimeRange] = None
    
    def matches(self, log_entry) -> bool:
        """Check if a log entry matches these criteria"""
        # Import here to avoid circular import
        from .log_entry import LogEntry
        
        if self.component and log_entry.component != self.component:
            return False
            
        if self.level and log_entry.level != self.level:
            return False
            
        if self.correlation_id and log_entry.correlation_id != self.correlation_id:
            return False
            
        if self.message_contains and self.message_contains.lower() not in log_entry.message.lower():
            return False
            
        if self.time_range and not self.time_range.contains(log_entry.timestamp):
            return False
            
        return True