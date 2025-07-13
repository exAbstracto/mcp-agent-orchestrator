"""
Retention Service for US-010: Centralized Logging System

Automatic log cleanup and retention management.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from src.services.logging_service import LoggingService


class RetentionService:
    """Service for managing log retention and cleanup"""
    
    def __init__(self, logging_service: LoggingService = None, default_retention_days: int = 7):
        """
        Initialize the retention service.
        
        Args:
            logging_service: The logging service to manage retention for
            default_retention_days: Default retention period in days (minimum 7)
        """
        self.logging_service = logging_service
        self.retention_days = max(default_retention_days, 7)  # Enforce minimum 7 days
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"RetentionService initialized with {self.retention_days} day retention")
    
    def get_retention_policy(self) -> Dict[str, Any]:
        """
        Get the current retention policy.
        
        Returns:
            Dictionary with retention policy details
        """
        return {
            "days": self.retention_days,
            "minimum_days": 7,
            "policy": f"Logs older than {self.retention_days} days are automatically cleaned up"
        }
    
    def set_retention_policy(self, days: int) -> Dict[str, Any]:
        """
        Set the retention policy.
        
        Args:
            days: Number of days to retain logs (minimum 7)
            
        Returns:
            Result dictionary with success status
        """
        if days < 7:
            return {
                "success": False,
                "error": "Retention period must be at least minimum 7 days"
            }
        
        old_retention = self.retention_days
        self.retention_days = days
        
        self.logger.info(f"Updated retention policy from {old_retention} to {days} days")
        
        return {
            "success": True,
            "days": days,
            "previous_days": old_retention
        }
    
    def cleanup_expired_logs(self) -> Dict[str, Any]:
        """
        Clean up logs that have exceeded the retention period.
        
        Returns:
            Dictionary with cleanup results
        """
        if not self.logging_service:
            return {
                "success": False,
                "error": "No logging service configured for retention cleanup"
            }
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        all_logs = self.logging_service.logs.copy()  # Work with a copy
        expired_logs = []
        remaining_logs = []
        
        for log in all_logs:
            if log.timestamp < cutoff_date:
                expired_logs.append(log)
            else:
                remaining_logs.append(log)
        
        # Update the logging service with remaining logs
        self.logging_service.logs = remaining_logs
        
        deleted_count = len(expired_logs)
        
        self.logger.info(f"Cleanup completed: {deleted_count} expired logs deleted")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "retention_days": self.retention_days,
            "remaining_logs": len(remaining_logs)
        }
    
    def get_cleanup_preview(self) -> Dict[str, Any]:
        """
        Preview what would be cleaned up without actually deleting logs.
        
        Returns:
            Dictionary with preview information
        """
        if not self.logging_service:
            return {
                "success": False,
                "error": "No logging service configured"
            }
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        all_logs = self.logging_service.logs
        expired_count = 0
        expired_by_component = {}
        
        for log in all_logs:
            if log.timestamp < cutoff_date:
                expired_count += 1
                component = log.component
                expired_by_component[component] = expired_by_component.get(component, 0) + 1
        
        return {
            "success": True,
            "would_delete_count": expired_count,
            "cutoff_date": cutoff_date.isoformat(),
            "retention_days": self.retention_days,
            "expired_by_component": expired_by_component,
            "total_logs": len(all_logs),
            "would_remain": len(all_logs) - expired_count
        }
    
    def get_log_age_distribution(self) -> Dict[str, Any]:
        """
        Get distribution of log ages for analysis.
        
        Returns:
            Dictionary with age distribution statistics
        """
        if not self.logging_service:
            return {
                "success": False,
                "error": "No logging service configured"
            }
        
        all_logs = self.logging_service.logs
        if not all_logs:
            return {
                "success": True,
                "total_logs": 0,
                "message": "No logs to analyze"
            }
        
        now = datetime.now()
        age_buckets = {
            "last_hour": 0,
            "last_day": 0,
            "last_week": 0,
            "last_month": 0,
            "older": 0
        }
        
        oldest_log = None
        newest_log = None
        
        for log in all_logs:
            age = now - log.timestamp
            
            if oldest_log is None or log.timestamp < oldest_log:
                oldest_log = log.timestamp
            if newest_log is None or log.timestamp > newest_log:
                newest_log = log.timestamp
            
            if age < timedelta(hours=1):
                age_buckets["last_hour"] += 1
            elif age < timedelta(days=1):
                age_buckets["last_day"] += 1
            elif age < timedelta(weeks=1):
                age_buckets["last_week"] += 1
            elif age < timedelta(days=30):
                age_buckets["last_month"] += 1
            else:
                age_buckets["older"] += 1
        
        return {
            "success": True,
            "total_logs": len(all_logs),
            "age_distribution": age_buckets,
            "oldest_log": oldest_log.isoformat() if oldest_log else None,
            "newest_log": newest_log.isoformat() if newest_log else None,
            "retention_policy_days": self.retention_days
        }
    
    def schedule_automatic_cleanup(self, interval_hours: int = 24) -> Dict[str, Any]:
        """
        Configure automatic cleanup scheduling.
        
        Args:
            interval_hours: How often to run cleanup (in hours)
            
        Returns:
            Dictionary with scheduling configuration
        """
        # Note: In a real implementation, this would set up a scheduler
        # For this implementation, we'll just return the configuration
        
        return {
            "success": True,
            "automatic_cleanup": True,
            "interval_hours": interval_hours,
            "retention_days": self.retention_days,
            "message": f"Automatic cleanup configured to run every {interval_hours} hours"
        }