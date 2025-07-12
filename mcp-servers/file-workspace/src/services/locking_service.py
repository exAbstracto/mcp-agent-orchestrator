"""
Locking Service for US-009: Shared Workspace File Locking

Core business logic for file lock management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque

from src.models.file_lock import FileLock, LockStatus, QueuedLockRequest


class LockingService:
    """Service for managing file locks and queues"""
    
    def __init__(self, default_timeout_seconds: int = 300):
        """
        Initialize the locking service.
        
        Args:
            default_timeout_seconds: Default lock timeout in seconds
        """
        self.default_timeout_seconds = default_timeout_seconds
        self.active_locks: Dict[str, FileLock] = {}  # file_path -> FileLock
        self.lock_queues: Dict[str, deque] = defaultdict(deque)  # file_path -> queue of requests
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"LockingService initialized with default timeout: {default_timeout_seconds}s")
    
    def acquire_lock(self, file_path: str, agent_id: str, timeout_seconds: Optional[int] = None) -> Dict[str, Any]:
        """
        Attempt to acquire a file lock.
        
        Args:
            file_path: Path to the file to lock
            agent_id: ID of the agent requesting the lock
            timeout_seconds: Lock timeout duration (uses default if None)
            
        Returns:
            Result dictionary with success status and lock details
        """
        if timeout_seconds is None:
            timeout_seconds = self.default_timeout_seconds
        
        # Validate timeout
        if timeout_seconds <= 0:
            return {
                "success": False,
                "error": "Invalid timeout: must be positive"
            }
        
        # Check if file is already locked
        if file_path in self.active_locks:
            existing_lock = self.active_locks[file_path]
            if not existing_lock.is_expired():
                return {
                    "success": False,
                    "error": f"File already locked by agent {existing_lock.agent_id}"
                }
            else:
                # Remove expired lock
                del self.active_locks[file_path]
        
        try:
            # Create new lock
            lock = FileLock.create(file_path, agent_id, timeout_seconds)
            self.active_locks[file_path] = lock
            
            self.logger.info(f"Lock acquired: {file_path} by {agent_id}")
            
            return {
                "success": True,
                "lock_id": lock.lock_id,
                "file_path": file_path,
                "agent_id": agent_id,
                "acquired_at": lock.acquired_at.isoformat(),
                "expires_at": lock.expires_at.isoformat()
            }
            
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid lock request: {str(e)}"
            }
    
    def release_lock(self, file_path: str, agent_id: str) -> Dict[str, Any]:
        """
        Release a file lock.
        
        Args:
            file_path: Path to the file to unlock
            agent_id: ID of the agent releasing the lock
            
        Returns:
            Result dictionary with success status
        """
        if file_path not in self.active_locks:
            return {
                "success": False,
                "error": "File is not locked"
            }
        
        lock = self.active_locks[file_path]
        
        # Check if the requesting agent owns the lock
        if lock.agent_id != agent_id:
            return {
                "success": False,
                "error": "Permission denied: only the locking agent can release the lock"
            }
        
        # Remove the lock
        del self.active_locks[file_path]
        
        self.logger.info(f"Lock released: {file_path} by {agent_id}")
        
        # Process any queued requests for this file (if event loop is running)
        try:
            asyncio.create_task(self._process_queue_for_file(file_path))
        except RuntimeError:
            # No event loop running, skip async processing
            pass
        
        return {
            "success": True,
            "file_path": file_path,
            "agent_id": agent_id,
            "released_at": datetime.now().isoformat()
        }
    
    def get_lock_status(self, file_path: str) -> Dict[str, Any]:
        """
        Get the current lock status for a file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            Dictionary with lock status information
        """
        if file_path not in self.active_locks:
            return {
                "status": "unlocked",
                "file_path": file_path
            }
        
        lock = self.active_locks[file_path]
        
        # Check if lock has expired
        if lock.is_expired():
            del self.active_locks[file_path]
            return {
                "status": "unlocked",
                "file_path": file_path
            }
        
        return {
            "status": "locked",
            "file_path": file_path,
            "agent_id": lock.agent_id,
            "lock_id": lock.lock_id,
            "acquired_at": lock.acquired_at.isoformat(),
            "expires_at": lock.expires_at.isoformat(),
            "metadata": lock.metadata
        }
    
    def list_all_locks(self) -> List[Dict[str, Any]]:
        """
        List all active locks in the system.
        
        Returns:
            List of lock status dictionaries
        """
        locks = []
        expired_files = []
        
        for file_path, lock in self.active_locks.items():
            if lock.is_expired():
                expired_files.append(file_path)
            else:
                locks.append(self.get_lock_status(file_path))
        
        # Clean up expired locks
        for file_path in expired_files:
            del self.active_locks[file_path]
        
        return locks
    
    def list_locks_by_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        List all locks held by a specific agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List of lock status dictionaries for the agent
        """
        agent_locks = []
        
        for file_path, lock in self.active_locks.items():
            if lock.agent_id == agent_id and not lock.is_expired():
                agent_locks.append(self.get_lock_status(file_path))
        
        return agent_locks
    
    def queue_lock_request(self, file_path: str, agent_id: str, timeout_seconds: int) -> Dict[str, Any]:
        """
        Add a lock request to the queue for a file.
        
        Args:
            file_path: Path to the file to lock
            agent_id: ID of the agent requesting the lock
            timeout_seconds: Desired lock timeout duration
            
        Returns:
            Result dictionary with queue information
        """
        if timeout_seconds <= 0:
            return {
                "success": False,
                "error": "Invalid timeout: must be positive"
            }
        
        # Check if file is currently locked
        if file_path not in self.active_locks:
            # File is not locked, try to acquire immediately
            return self.acquire_lock(file_path, agent_id, timeout_seconds)
        
        # Add to queue
        queue = self.lock_queues[file_path]
        position = len(queue) + 1
        
        # Estimate wait time based on current lock expiry and queue
        current_lock = self.active_locks[file_path]
        estimated_wait = max(0, (current_lock.expires_at - datetime.now()).total_seconds())
        
        # Add estimated time for each request ahead in queue (assuming default timeout)
        estimated_wait += (position - 1) * self.default_timeout_seconds
        
        request = QueuedLockRequest.create(
            file_path=file_path,
            agent_id=agent_id,
            timeout_seconds=timeout_seconds,
            position=position,
            estimated_wait_time=estimated_wait
        )
        
        queue.append(request)
        
        self.logger.info(f"Lock request queued: {file_path} by {agent_id}, position {position}")
        
        return {
            "queued": True,
            "request_id": request.request_id,
            "file_path": file_path,
            "agent_id": agent_id,
            "position": position,
            "estimated_wait_time": estimated_wait
        }
    
    def cancel_queued_request(self, file_path: str, agent_id: str) -> Dict[str, Any]:
        """
        Cancel a queued lock request.
        
        Args:
            file_path: Path to the file
            agent_id: ID of the agent canceling the request
            
        Returns:
            Result dictionary with cancellation status
        """
        if file_path not in self.lock_queues:
            return {
                "success": False,
                "error": "No queue exists for this file"
            }
        
        queue = self.lock_queues[file_path]
        
        # Find and remove the request
        for i, request in enumerate(queue):
            if request.agent_id == agent_id:
                queue.remove(request)
                
                # Update positions for remaining requests
                for j, remaining_request in enumerate(queue):
                    remaining_request.position = j + 1
                
                self.logger.info(f"Queued request cancelled: {file_path} by {agent_id}")
                
                return {
                    "success": True,
                    "cancelled": True,
                    "file_path": file_path,
                    "agent_id": agent_id
                }
        
        return {
            "success": False,
            "error": "No queued request found for this agent"
        }
    
    def get_queue_status(self, file_path: str) -> Dict[str, Any]:
        """
        Get the queue status for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with queue information
        """
        if file_path not in self.lock_queues:
            return {
                "file_path": file_path,
                "queue_length": 0,
                "queued_agents": []
            }
        
        queue = self.lock_queues[file_path]
        
        return {
            "file_path": file_path,
            "queue_length": len(queue),
            "queued_agents": [request.to_dict() for request in queue]
        }
    
    async def process_lock_queue(self):
        """Process all lock queues to handle expired locks and promote queued requests"""
        processed_files = []
        
        for file_path in list(self.lock_queues.keys()):
            if await self._process_queue_for_file(file_path):
                processed_files.append(file_path)
        
        return {
            "processed_files": processed_files,
            "processed_count": len(processed_files)
        }
    
    async def _process_queue_for_file(self, file_path: str) -> bool:
        """
        Process the queue for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if a queued request was promoted to active lock
        """
        if file_path not in self.lock_queues or not self.lock_queues[file_path]:
            return False
        
        # Check if file is currently locked
        if file_path in self.active_locks:
            lock = self.active_locks[file_path]
            if not lock.is_expired():
                return False  # Still locked
            else:
                del self.active_locks[file_path]  # Remove expired lock
        
        # Promote next request in queue
        queue = self.lock_queues[file_path]
        if queue:
            next_request = queue.popleft()
            
            # Acquire lock for the next agent
            result = self.acquire_lock(
                file_path=next_request.file_path,
                agent_id=next_request.agent_id,
                timeout_seconds=next_request.timeout_seconds
            )
            
            if result["success"]:
                self.logger.info(f"Queued request promoted to active lock: {file_path} by {next_request.agent_id}")
                
                # Update positions for remaining requests
                for i, remaining_request in enumerate(queue):
                    remaining_request.position = i + 1
                
                return True
        
        return False
    
    def force_release_lock(self, file_path: str, admin_reason: str = "Admin action") -> Dict[str, Any]:
        """
        Forcibly release a lock (admin function).
        
        Args:
            file_path: Path to the file to unlock
            admin_reason: Reason for the forced release
            
        Returns:
            Result dictionary with release status
        """
        if file_path not in self.active_locks:
            return {
                "success": False,
                "error": "File is not locked"
            }
        
        lock = self.active_locks[file_path]
        original_agent = lock.agent_id
        
        # Remove the lock
        del self.active_locks[file_path]
        
        self.logger.warning(f"Lock forcibly released: {file_path} (was locked by {original_agent}) - Reason: {admin_reason}")
        
        # Process any queued requests for this file (if event loop is running)
        try:
            asyncio.create_task(self._process_queue_for_file(file_path))
        except RuntimeError:
            # No event loop running, skip async processing
            pass
        
        return {
            "success": True,
            "forced": True,
            "file_path": file_path,
            "original_agent": original_agent,
            "admin_reason": admin_reason,
            "released_at": datetime.now().isoformat()
        }