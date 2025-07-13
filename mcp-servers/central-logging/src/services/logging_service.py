"""
Logging Service for US-010: Centralized Logging System

Core business logic for log aggregation and management.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

from src.models.log_entry import LogEntry, LogLevel


class LoggingService:
    """Service for managing centralized log storage and retrieval"""
    
    def __init__(self):
        """Initialize the logging service"""
        self.logs: List[LogEntry] = []
        self.component_log_levels: Dict[str, LogLevel] = {}
        self.global_log_level: LogLevel = LogLevel.INFO
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("LoggingService initialized")
    
    def add_log_entry(self, log_entry: LogEntry) -> Dict[str, Any]:
        """
        Add a log entry to the central store.
        
        Args:
            log_entry: The log entry to add
            
        Returns:
            Result dictionary with success status and log details
        """
        # Check if log should be filtered based on level
        if not self._should_log(log_entry):
            return {
                "success": False,
                "filtered": True,
                "reason": f"Log level {log_entry.level.value} below threshold"
            }
        
        # Store the log entry
        self.logs.append(log_entry)
        
        self.logger.debug(f"Added log entry: {log_entry.log_id} from {log_entry.component}")
        
        return {
            "success": True,
            "log_id": log_entry.log_id,
            "timestamp": log_entry.timestamp.isoformat(),
            "component": log_entry.component,
            "level": log_entry.level.value
        }
    
    def _should_log(self, log_entry: LogEntry) -> bool:
        """
        Check if a log entry should be stored based on configured levels.
        
        Args:
            log_entry: The log entry to check
            
        Returns:
            True if the log should be stored, False otherwise
        """
        # Get the effective log level for the component
        component_level = self.component_log_levels.get(log_entry.component, self.global_log_level)
        
        # Define level hierarchy for comparison
        level_values = {
            LogLevel.DEBUG: 1,
            LogLevel.INFO: 2,
            LogLevel.WARNING: 3,
            LogLevel.ERROR: 4,
            LogLevel.CRITICAL: 5
        }
        
        # Check if log level meets threshold
        return level_values[log_entry.level] >= level_values[component_level]
    
    def get_all_logs(self) -> List[LogEntry]:
        """
        Get all stored log entries.
        
        Returns:
            List of all log entries sorted by timestamp
        """
        return sorted(self.logs, key=lambda log: log.timestamp)
    
    def get_logs_by_correlation_id(self, correlation_id: str) -> List[LogEntry]:
        """
        Get all log entries with the specified correlation ID.
        
        Args:
            correlation_id: The correlation ID to search for
            
        Returns:
            List of log entries with matching correlation ID, sorted by timestamp
        """
        matching_logs = [log for log in self.logs if log.correlation_id == correlation_id]
        return sorted(matching_logs, key=lambda log: log.timestamp)
    
    def get_logs_by_component(self, component: str) -> List[LogEntry]:
        """
        Get all log entries from the specified component.
        
        Args:
            component: The component name to search for
            
        Returns:
            List of log entries from the component, sorted by timestamp
        """
        matching_logs = [log for log in self.logs if log.component == component]
        return sorted(matching_logs, key=lambda log: log.timestamp)
    
    def set_component_log_level(self, component: str, level: LogLevel) -> Dict[str, Any]:
        """
        Set the log level for a specific component.
        
        Args:
            component: The component name
            level: The log level to set
            
        Returns:
            Result dictionary with success status
        """
        self.component_log_levels[component] = level
        
        self.logger.info(f"Set log level for {component} to {level.value}")
        
        return {
            "success": True,
            "component": component,
            "level": level.value
        }
    
    def get_component_log_level(self, component: str) -> LogLevel:
        """
        Get the log level for a specific component.
        
        Args:
            component: The component name
            
        Returns:
            The log level for the component (or global level if not set)
        """
        return self.component_log_levels.get(component, self.global_log_level)
    
    def set_global_log_level(self, level: LogLevel) -> Dict[str, Any]:
        """
        Set the global default log level.
        
        Args:
            level: The log level to set globally
            
        Returns:
            Result dictionary with success status
        """
        self.global_log_level = level
        
        self.logger.info(f"Set global log level to {level.value}")
        
        return {
            "success": True,
            "level": level.value
        }
    
    def get_global_log_level(self) -> LogLevel:
        """
        Get the global default log level.
        
        Returns:
            The global log level
        """
        return self.global_log_level
    
    def list_log_levels(self) -> List[str]:
        """
        List all available log levels.
        
        Returns:
            List of log level names
        """
        return [level.value for level in LogLevel]
    
    def get_log_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the stored logs.
        
        Returns:
            Dictionary with log statistics
        """
        component_counts = defaultdict(int)
        level_counts = defaultdict(int)
        
        for log in self.logs:
            component_counts[log.component] += 1
            level_counts[log.level.value] += 1
        
        return {
            "total_logs": len(self.logs),
            "components": dict(component_counts),
            "log_levels": dict(level_counts),
            "earliest_log": self.logs[0].timestamp.isoformat() if self.logs else None,
            "latest_log": self.logs[-1].timestamp.isoformat() if self.logs else None
        }
    
    def clear_logs(self) -> Dict[str, Any]:
        """
        Clear all stored logs (for testing/maintenance).
        
        Returns:
            Result dictionary with count of cleared logs
        """
        count = len(self.logs)
        self.logs.clear()
        
        self.logger.info(f"Cleared {count} log entries")
        
        return {
            "success": True,
            "cleared_count": count
        }