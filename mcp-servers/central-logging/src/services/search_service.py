"""
Search Service for US-010: Centralized Logging System

Advanced search and filtering functionality for logs.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

from src.models.log_entry import LogEntry, LogLevel
from src.models.search_criteria import SearchCriteria, TimeRange
from src.services.logging_service import LoggingService


class SearchService:
    """Service for searching and filtering log entries"""
    
    def __init__(self, logging_service: LoggingService):
        """
        Initialize the search service.
        
        Args:
            logging_service: The logging service to search within
        """
        self.logging_service = logging_service
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("SearchService initialized")
    
    def search_logs(self, criteria: SearchCriteria) -> List[LogEntry]:
        """
        Search logs based on the provided criteria.
        
        Args:
            criteria: The search criteria to apply
            
        Returns:
            List of matching log entries sorted by timestamp
        """
        all_logs = self.logging_service.get_all_logs()
        matching_logs = []
        
        for log in all_logs:
            if criteria.matches(log):
                matching_logs.append(log)
        
        self.logger.debug(f"Search found {len(matching_logs)} matching logs")
        
        return sorted(matching_logs, key=lambda log: log.timestamp)
    
    def search_by_component(self, component: str) -> List[LogEntry]:
        """
        Search logs by component name.
        
        Args:
            component: The component name to search for
            
        Returns:
            List of matching log entries
        """
        criteria = SearchCriteria(component=component)
        return self.search_logs(criteria)
    
    def search_by_level(self, level: LogLevel) -> List[LogEntry]:
        """
        Search logs by log level.
        
        Args:
            level: The log level to search for
            
        Returns:
            List of matching log entries
        """
        criteria = SearchCriteria(level=level)
        return self.search_logs(criteria)
    
    def search_by_correlation_id(self, correlation_id: str) -> List[LogEntry]:
        """
        Search logs by correlation ID.
        
        Args:
            correlation_id: The correlation ID to search for
            
        Returns:
            List of matching log entries
        """
        criteria = SearchCriteria(correlation_id=correlation_id)
        return self.search_logs(criteria)
    
    def search_by_message_content(self, search_text: str) -> List[LogEntry]:
        """
        Search logs by message content.
        
        Args:
            search_text: The text to search for in messages
            
        Returns:
            List of matching log entries
        """
        criteria = SearchCriteria(message_contains=search_text)
        return self.search_logs(criteria)
    
    def search_by_time_range(self, start: datetime, end: datetime) -> List[LogEntry]:
        """
        Search logs within a time range.
        
        Args:
            start: Start of the time range
            end: End of the time range
            
        Returns:
            List of matching log entries
        """
        time_range = TimeRange(start=start, end=end)
        criteria = SearchCriteria(time_range=time_range)
        return self.search_logs(criteria)
    
    def search_recent_logs(self, hours: int = 24) -> List[LogEntry]:
        """
        Search for recent logs within the specified number of hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent log entries
        """
        from datetime import timedelta
        
        now = datetime.now()
        start_time = now - timedelta(hours=hours)
        
        return self.search_by_time_range(start_time, now)
    
    def search_errors_and_above(self, component: str = None) -> List[LogEntry]:
        """
        Search for ERROR and CRITICAL level logs.
        
        Args:
            component: Optional component filter
            
        Returns:
            List of error-level log entries
        """
        all_logs = self.logging_service.get_all_logs()
        error_logs = []
        
        for log in all_logs:
            if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                if component is None or log.component == component:
                    error_logs.append(log)
        
        return sorted(error_logs, key=lambda log: log.timestamp)
    
    def get_component_activity_summary(self) -> Dict[str, Any]:
        """
        Get a summary of activity by component.
        
        Returns:
            Dictionary with component activity statistics
        """
        all_logs = self.logging_service.get_all_logs()
        component_stats = {}
        
        for log in all_logs:
            if log.component not in component_stats:
                component_stats[log.component] = {
                    "total_logs": 0,
                    "levels": {},
                    "earliest": log.timestamp,
                    "latest": log.timestamp
                }
            
            stats = component_stats[log.component]
            stats["total_logs"] += 1
            
            # Count by level
            level_name = log.level.value
            stats["levels"][level_name] = stats["levels"].get(level_name, 0) + 1
            
            # Update time range
            if log.timestamp < stats["earliest"]:
                stats["earliest"] = log.timestamp
            if log.timestamp > stats["latest"]:
                stats["latest"] = log.timestamp
        
        # Convert timestamps to ISO strings
        for component, stats in component_stats.items():
            stats["earliest"] = stats["earliest"].isoformat()
            stats["latest"] = stats["latest"].isoformat()
        
        return component_stats
    
    def trace_correlation_flow(self, correlation_id: str) -> Dict[str, Any]:
        """
        Trace the flow of a correlation ID through components.
        
        Args:
            correlation_id: The correlation ID to trace
            
        Returns:
            Dictionary with trace flow information
        """
        matching_logs = self.search_by_correlation_id(correlation_id)
        
        if not matching_logs:
            return {
                "correlation_id": correlation_id,
                "found": False,
                "message": "No logs found for this correlation ID"
            }
        
        # Build flow information
        components = []
        seen_components = set()
        
        for log in matching_logs:
            if log.component not in seen_components:
                components.append(log.component)
                seen_components.add(log.component)
        
        return {
            "correlation_id": correlation_id,
            "found": True,
            "log_count": len(matching_logs),
            "components_involved": components,
            "flow_start": matching_logs[0].timestamp.isoformat(),
            "flow_end": matching_logs[-1].timestamp.isoformat(),
            "flow_duration_seconds": (matching_logs[-1].timestamp - matching_logs[0].timestamp).total_seconds(),
            "logs": [log.to_dict() for log in matching_logs]
        }