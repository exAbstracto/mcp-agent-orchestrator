"""
Cleanup Service for US-009: Shared Workspace File Locking

Automatic cleanup of expired locks and maintenance tasks.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any

from src.services.locking_service import LockingService


class CleanupService:
    """Service for automatic cleanup of expired locks"""
    
    def __init__(self, locking_service: LockingService):
        """
        Initialize the cleanup service.
        
        Args:
            locking_service: The locking service to clean up
        """
        self.locking_service = locking_service
        self.logger = logging.getLogger(__name__)
        self._cleanup_task: asyncio.Task = None
        self._running = False
        
        self.logger.info("CleanupService initialized")
    
    def cleanup_expired_locks(self) -> Dict[str, Any]:
        """
        Clean up all expired locks immediately.
        
        Returns:
            Dictionary with cleanup results
        """
        cleaned_files = []
        cleaned_count = 0
        
        # Find expired locks
        expired_files = []
        for file_path, lock in self.locking_service.active_locks.items():
            if lock.is_expired():
                expired_files.append(file_path)
                cleaned_files.append(file_path)
        
        # Remove expired locks
        for file_path in expired_files:
            original_agent = self.locking_service.active_locks[file_path].agent_id
            del self.locking_service.active_locks[file_path]
            cleaned_count += 1
            
            self.logger.info(f"Cleaned expired lock: {file_path} (was locked by {original_agent})")
            
            # Process any queued requests for this file (if event loop is running)
            try:
                asyncio.create_task(self.locking_service._process_queue_for_file(file_path))
            except RuntimeError:
                # No event loop running, skip async processing
                pass
        
        self.logger.info(f"Cleanup completed: {cleaned_count} expired locks removed")
        
        return {
            "cleaned_count": cleaned_count,
            "cleaned_files": cleaned_files,
            "cleanup_time": datetime.now().isoformat()
        }
    
    async def start_automatic_cleanup(self, interval_seconds: int = 60):
        """
        Start automatic cleanup with specified interval.
        
        Args:
            interval_seconds: Cleanup interval in seconds
        """
        if self._running:
            self.logger.warning("Automatic cleanup is already running")
            return
        
        self._running = True
        self.logger.info(f"Starting automatic cleanup with {interval_seconds}s interval")
        
        try:
            while self._running:
                await asyncio.sleep(interval_seconds)
                if self._running:  # Check again in case we were stopped during sleep
                    cleanup_result = self.cleanup_expired_locks()
                    if cleanup_result["cleaned_count"] > 0:
                        self.logger.info(f"Automatic cleanup: {cleanup_result['cleaned_count']} locks cleaned")
        except asyncio.CancelledError:
            self.logger.info("Automatic cleanup cancelled")
        finally:
            self._running = False
    
    def stop_automatic_cleanup(self):
        """Stop the automatic cleanup process"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            self.logger.info("Stopping automatic cleanup")
        
        self._running = False
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current state that might need cleanup.
        
        Returns:
            Dictionary with cleanup statistics
        """
        total_locks = len(self.locking_service.active_locks)
        expired_locks = 0
        
        for lock in self.locking_service.active_locks.values():
            if lock.is_expired():
                expired_locks += 1
        
        total_queued = sum(len(queue) for queue in self.locking_service.lock_queues.values())
        
        return {
            "total_active_locks": total_locks,
            "expired_locks": expired_locks,
            "valid_locks": total_locks - expired_locks,
            "total_queued_requests": total_queued,
            "cleanup_running": self._running,
            "stats_time": datetime.now().isoformat()
        }
    
    async def cleanup_stale_queues(self) -> Dict[str, Any]:
        """
        Clean up stale queue entries and empty queues.
        
        Returns:
            Dictionary with queue cleanup results
        """
        cleaned_queues = []
        cleaned_requests = 0
        
        # Clean up empty queues
        empty_queues = [
            file_path for file_path, queue in self.locking_service.lock_queues.items()
            if len(queue) == 0
        ]
        
        for file_path in empty_queues:
            del self.locking_service.lock_queues[file_path]
            cleaned_queues.append(file_path)
        
        # TODO: Could add logic to clean up very old queue requests
        # For now, we rely on agents to cancel their own requests
        
        self.logger.info(f"Queue cleanup completed: {len(cleaned_queues)} empty queues removed")
        
        return {
            "cleaned_queues": cleaned_queues,
            "cleaned_requests": cleaned_requests,
            "cleanup_time": datetime.now().isoformat()
        }
    
    async def full_maintenance(self) -> Dict[str, Any]:
        """
        Perform full maintenance including locks and queues.
        
        Returns:
            Dictionary with complete maintenance results
        """
        self.logger.info("Starting full maintenance")
        
        # Clean up expired locks
        lock_cleanup = self.cleanup_expired_locks()
        
        # Clean up stale queues
        queue_cleanup = await self.cleanup_stale_queues()
        
        # Process all lock queues
        queue_processing = await self.locking_service.process_lock_queue()
        
        maintenance_result = {
            "lock_cleanup": lock_cleanup,
            "queue_cleanup": queue_cleanup,
            "queue_processing": queue_processing,
            "maintenance_time": datetime.now().isoformat()
        }
        
        self.logger.info("Full maintenance completed")
        
        return maintenance_result