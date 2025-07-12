"""
TDD Tests for US-009: Shared Workspace File Locking

Test all acceptance criteria using Test-Driven Development approach.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Import the modules we'll implement
from src.models.file_lock import FileLock, LockStatus
from src.services.locking_service import LockingService
from src.services.cleanup_service import CleanupService
from src.file_workspace_server import FileWorkspaceServer


@pytest.mark.us009
class TestFileLockAcquisitionAndRelease:
    """Test that file locks can be acquired and released"""
    
    def test_acquire_file_lock_success(self):
        """Test successful file lock acquisition"""
        service = LockingService()
        
        # Acquire a lock
        result = service.acquire_lock(
            file_path="/workspace/test.py",
            agent_id="agent-1",
            timeout_seconds=300
        )
        
        assert result["success"] is True
        assert result["lock_id"] is not None
        assert result["file_path"] == "/workspace/test.py"
        assert result["agent_id"] == "agent-1"
        assert result["expires_at"] is not None
    
    def test_release_file_lock_success(self):
        """Test successful file lock release"""
        service = LockingService()
        
        # First acquire a lock
        acquire_result = service.acquire_lock(
            file_path="/workspace/test.py",
            agent_id="agent-1",
            timeout_seconds=300
        )
        
        # Then release it
        release_result = service.release_lock(
            file_path="/workspace/test.py",
            agent_id="agent-1"
        )
        
        assert release_result["success"] is True
        assert release_result["file_path"] == "/workspace/test.py"
        assert release_result["agent_id"] == "agent-1"
    
    def test_acquire_already_locked_file_fails(self):
        """Test that acquiring an already locked file fails"""
        service = LockingService()
        
        # Agent 1 acquires lock
        service.acquire_lock(
            file_path="/workspace/test.py",
            agent_id="agent-1",
            timeout_seconds=300
        )
        
        # Agent 2 tries to acquire same file
        result = service.acquire_lock(
            file_path="/workspace/test.py",
            agent_id="agent-2",
            timeout_seconds=300
        )
        
        assert result["success"] is False
        assert "already locked" in result["error"].lower()
    
    def test_release_unlocked_file_fails(self):
        """Test that releasing an unlocked file fails"""
        service = LockingService()
        
        result = service.release_lock(
            file_path="/workspace/test.py",
            agent_id="agent-1"
        )
        
        assert result["success"] is False
        assert "not locked" in result["error"].lower()
    
    def test_release_lock_wrong_agent_fails(self):
        """Test that only the locking agent can release the lock"""
        service = LockingService()
        
        # Agent 1 acquires lock
        service.acquire_lock(
            file_path="/workspace/test.py",
            agent_id="agent-1",
            timeout_seconds=300
        )
        
        # Agent 2 tries to release it
        result = service.release_lock(
            file_path="/workspace/test.py",
            agent_id="agent-2"
        )
        
        assert result["success"] is False
        assert "permission denied" in result["error"].lower()


@pytest.mark.us009
class TestLockTimeout:
    """Test that lock requests include timeout duration"""
    
    def test_lock_with_custom_timeout(self):
        """Test acquiring lock with custom timeout"""
        service = LockingService()
        
        result = service.acquire_lock(
            file_path="/workspace/test.py",
            agent_id="agent-1",
            timeout_seconds=600  # 10 minutes
        )
        
        assert result["success"] is True
        
        # Check that timeout is approximately correct (within 5 seconds)
        expires_at = datetime.fromisoformat(result["expires_at"])
        expected_expiry = datetime.now() + timedelta(seconds=600)
        time_diff = abs((expires_at - expected_expiry).total_seconds())
        assert time_diff < 5
    
    def test_lock_with_default_timeout(self):
        """Test acquiring lock with default timeout"""
        service = LockingService()
        
        result = service.acquire_lock(
            file_path="/workspace/test.py",
            agent_id="agent-1"
            # No timeout specified, should use default
        )
        
        assert result["success"] is True
        assert result["expires_at"] is not None
    
    def test_lock_timeout_validation(self):
        """Test that invalid timeout values are rejected"""
        service = LockingService()
        
        # Negative timeout
        result = service.acquire_lock(
            file_path="/workspace/test.py",
            agent_id="agent-1",
            timeout_seconds=-100
        )
        
        assert result["success"] is False
        assert "invalid timeout" in result["error"].lower()
        
        # Zero timeout
        result = service.acquire_lock(
            file_path="/workspace/test.py",
            agent_id="agent-1",
            timeout_seconds=0
        )
        
        assert result["success"] is False
        assert "invalid timeout" in result["error"].lower()


@pytest.mark.us009
class TestConcurrentLockQueuing:
    """Test that concurrent lock attempts are queued"""
    
    @pytest.mark.asyncio
    async def test_lock_queue_fifo_order(self):
        """Test that queued lock requests are processed in FIFO order"""
        service = LockingService()
        
        # Agent 1 acquires lock
        result1 = service.acquire_lock(
            file_path="/workspace/test.py",
            agent_id="agent-1",
            timeout_seconds=1  # Short timeout for quick test
        )
        assert result1["success"] is True
        
        # Agents 2 and 3 queue for the same file
        queue_result2 = service.queue_lock_request(
            file_path="/workspace/test.py",
            agent_id="agent-2",
            timeout_seconds=300
        )
        
        queue_result3 = service.queue_lock_request(
            file_path="/workspace/test.py",
            agent_id="agent-3",
            timeout_seconds=300
        )
        
        assert queue_result2["queued"] is True
        assert queue_result3["queued"] is True
        assert queue_result2["position"] == 1
        assert queue_result3["position"] == 2
        
        # Wait for agent 1's lock to expire
        await asyncio.sleep(1.5)
        
        # Process the queue
        await service.process_lock_queue()
        
        # Agent 2 should get the lock next
        lock_status = service.get_lock_status("/workspace/test.py")
        assert lock_status["agent_id"] == "agent-2"
    
    def test_queue_lock_request(self):
        """Test adding requests to the lock queue"""
        service = LockingService()
        
        # File is already locked
        service.acquire_lock(
            file_path="/workspace/test.py",
            agent_id="agent-1",
            timeout_seconds=300
        )
        
        # Queue a request
        result = service.queue_lock_request(
            file_path="/workspace/test.py",
            agent_id="agent-2",
            timeout_seconds=300
        )
        
        assert result["queued"] is True
        assert result["position"] == 1
        assert result["estimated_wait_time"] > 0
    
    def test_cancel_queued_request(self):
        """Test canceling a queued lock request"""
        service = LockingService()
        
        # File is locked
        service.acquire_lock(
            file_path="/workspace/test.py",
            agent_id="agent-1",
            timeout_seconds=300
        )
        
        # Queue a request
        queue_result = service.queue_lock_request(
            file_path="/workspace/test.py",
            agent_id="agent-2",
            timeout_seconds=300
        )
        
        # Cancel the queued request
        cancel_result = service.cancel_queued_request(
            file_path="/workspace/test.py",
            agent_id="agent-2"
        )
        
        assert cancel_result["success"] is True
        assert cancel_result["cancelled"] is True


@pytest.mark.us009
class TestStaleLockCleanup:
    """Test that stale locks are cleaned up automatically"""
    
    @pytest.mark.asyncio
    async def test_expired_lock_cleanup(self):
        """Test that expired locks are automatically cleaned up"""
        service = LockingService()
        cleanup_service = CleanupService(service)
        
        # Acquire lock with short timeout
        result = service.acquire_lock(
            file_path="/workspace/test.py",
            agent_id="agent-1",
            timeout_seconds=1  # 1 second timeout
        )
        assert result["success"] is True
        
        # Wait for lock to expire
        await asyncio.sleep(1.5)
        
        # Run cleanup
        cleanup_result = cleanup_service.cleanup_expired_locks()
        
        assert cleanup_result["cleaned_count"] == 1
        assert "/workspace/test.py" in cleanup_result["cleaned_files"]
        
        # Verify lock is removed
        status = service.get_lock_status("/workspace/test.py")
        assert status["status"] == "unlocked"
    
    @pytest.mark.asyncio
    async def test_automatic_cleanup_service(self):
        """Test that cleanup service runs automatically"""
        service = LockingService()
        cleanup_service = CleanupService(service)
        
        # Acquire multiple locks with short timeouts
        service.acquire_lock("/workspace/test1.py", "agent-1", timeout_seconds=1)
        service.acquire_lock("/workspace/test2.py", "agent-2", timeout_seconds=2)
        
        # Start automatic cleanup with short interval
        cleanup_task = asyncio.create_task(
            cleanup_service.start_automatic_cleanup(interval_seconds=0.5)
        )
        
        # Wait for cleanup to run
        await asyncio.sleep(3)
        
        # Stop cleanup
        cleanup_task.cancel()
        
        # Both locks should be cleaned up
        status1 = service.get_lock_status("/workspace/test1.py")
        status2 = service.get_lock_status("/workspace/test2.py")
        
        assert status1["status"] == "unlocked"
        assert status2["status"] == "unlocked"
    
    def test_cleanup_preserves_valid_locks(self):
        """Test that cleanup doesn't remove valid (non-expired) locks"""
        service = LockingService()
        cleanup_service = CleanupService(service)
        
        # Acquire lock with long timeout
        result = service.acquire_lock(
            file_path="/workspace/test.py",
            agent_id="agent-1",
            timeout_seconds=3600  # 1 hour
        )
        assert result["success"] is True
        
        # Run cleanup immediately
        cleanup_result = cleanup_service.cleanup_expired_locks()
        
        assert cleanup_result["cleaned_count"] == 0
        
        # Verify lock is still active
        status = service.get_lock_status("/workspace/test.py")
        assert status["status"] == "locked"
        assert status["agent_id"] == "agent-1"


@pytest.mark.us009
class TestLockStatusVisibility:
    """Test that lock status is visible to all agents"""
    
    def test_get_file_lock_status(self):
        """Test getting status of a specific file lock"""
        service = LockingService()
        
        # Test unlocked file
        status = service.get_lock_status("/workspace/test.py")
        assert status["status"] == "unlocked"
        assert status["file_path"] == "/workspace/test.py"
        
        # Acquire lock
        service.acquire_lock(
            file_path="/workspace/test.py",
            agent_id="agent-1",
            timeout_seconds=300
        )
        
        # Test locked file
        status = service.get_lock_status("/workspace/test.py")
        assert status["status"] == "locked"
        assert status["agent_id"] == "agent-1"
        assert status["file_path"] == "/workspace/test.py"
        assert status["acquired_at"] is not None
        assert status["expires_at"] is not None
    
    def test_list_all_locks(self):
        """Test listing all active locks in the system"""
        service = LockingService()
        
        # Initially no locks
        locks = service.list_all_locks()
        assert len(locks) == 0
        
        # Acquire multiple locks
        service.acquire_lock("/workspace/test1.py", "agent-1", timeout_seconds=300)
        service.acquire_lock("/workspace/test2.py", "agent-2", timeout_seconds=300)
        service.acquire_lock("/workspace/test3.py", "agent-1", timeout_seconds=300)
        
        # List all locks
        locks = service.list_all_locks()
        assert len(locks) == 3
        
        file_paths = [lock["file_path"] for lock in locks]
        assert "/workspace/test1.py" in file_paths
        assert "/workspace/test2.py" in file_paths
        assert "/workspace/test3.py" in file_paths
    
    def test_list_locks_by_agent(self):
        """Test listing locks filtered by agent"""
        service = LockingService()
        
        # Acquire locks by different agents
        service.acquire_lock("/workspace/test1.py", "agent-1", timeout_seconds=300)
        service.acquire_lock("/workspace/test2.py", "agent-2", timeout_seconds=300)
        service.acquire_lock("/workspace/test3.py", "agent-1", timeout_seconds=300)
        
        # List locks for agent-1
        agent1_locks = service.list_locks_by_agent("agent-1")
        assert len(agent1_locks) == 2
        
        file_paths = [lock["file_path"] for lock in agent1_locks]
        assert "/workspace/test1.py" in file_paths
        assert "/workspace/test3.py" in file_paths
        
        # List locks for agent-2
        agent2_locks = service.list_locks_by_agent("agent-2")
        assert len(agent2_locks) == 1
        assert agent2_locks[0]["file_path"] == "/workspace/test2.py"
    
    def test_get_queue_status(self):
        """Test getting queue status for a file"""
        service = LockingService()
        
        # Lock a file
        service.acquire_lock("/workspace/test.py", "agent-1", timeout_seconds=300)
        
        # Queue multiple requests
        service.queue_lock_request("/workspace/test.py", "agent-2", timeout_seconds=300)
        service.queue_lock_request("/workspace/test.py", "agent-3", timeout_seconds=300)
        
        # Get queue status
        queue_status = service.get_queue_status("/workspace/test.py")
        
        assert queue_status["queue_length"] == 2
        assert len(queue_status["queued_agents"]) == 2
        assert queue_status["queued_agents"][0]["agent_id"] == "agent-2"
        assert queue_status["queued_agents"][1]["agent_id"] == "agent-3"


@pytest.mark.us009
class TestMCPServerIntegration:
    """Test MCP server integration with file locking tools"""
    
    def test_server_initialization(self):
        """Test that the file workspace server initializes correctly"""
        server = FileWorkspaceServer("file-workspace", "1.0.0")
        
        assert server.name == "file-workspace"
        assert server.version == "1.0.0"
        assert server.locking_service is not None
        assert server.cleanup_service is not None
    
    @pytest.mark.asyncio
    async def test_acquire_file_lock_tool(self):
        """Test the acquire_file_lock MCP tool"""
        server = FileWorkspaceServer("file-workspace", "1.0.0")
        
        # Mock the MCP tool call
        arguments = {
            "file_path": "/workspace/test.py",
            "agent_id": "agent-1",
            "timeout_seconds": 300
        }
        
        result = server.acquire_file_lock(arguments)
        
        assert result["success"] is True
        assert result["file_path"] == "/workspace/test.py"
        assert result["agent_id"] == "agent-1"
    
    @pytest.mark.asyncio
    async def test_release_file_lock_tool(self):
        """Test the release_file_lock MCP tool"""
        server = FileWorkspaceServer("file-workspace", "1.0.0")
        
        # First acquire a lock
        acquire_args = {
            "file_path": "/workspace/test.py",
            "agent_id": "agent-1",
            "timeout_seconds": 300
        }
        server.acquire_file_lock(acquire_args)
        
        # Then release it
        release_args = {
            "file_path": "/workspace/test.py",
            "agent_id": "agent-1"
        }
        
        result = server.release_file_lock(release_args)
        
        assert result["success"] is True
        assert result["file_path"] == "/workspace/test.py"
    
    @pytest.mark.asyncio
    async def test_get_file_lock_status_tool(self):
        """Test the get_file_lock_status MCP tool"""
        server = FileWorkspaceServer("file-workspace", "1.0.0")
        
        # Test unlocked file
        result = server.get_file_lock_status({"file_path": "/workspace/test.py"})
        assert result["status"] == "unlocked"
        
        # Acquire lock and test again
        server.acquire_file_lock({
            "file_path": "/workspace/test.py",
            "agent_id": "agent-1",
            "timeout_seconds": 300
        })
        
        result = server.get_file_lock_status({"file_path": "/workspace/test.py"})
        assert result["status"] == "locked"
        assert result["agent_id"] == "agent-1"
    
    @pytest.mark.asyncio
    async def test_list_all_locks_tool(self):
        """Test the list_all_locks MCP tool"""
        server = FileWorkspaceServer("file-workspace", "1.0.0")
        
        # Acquire multiple locks
        server.acquire_file_lock({
            "file_path": "/workspace/test1.py",
            "agent_id": "agent-1",
            "timeout_seconds": 300
        })
        server.acquire_file_lock({
            "file_path": "/workspace/test2.py",
            "agent_id": "agent-2",
            "timeout_seconds": 300
        })
        
        result = server.list_all_locks({})
        
        assert len(result["locks"]) == 2
        file_paths = [lock["file_path"] for lock in result["locks"]]
        assert "/workspace/test1.py" in file_paths
        assert "/workspace/test2.py" in file_paths
    
    @pytest.mark.asyncio
    async def test_force_release_lock_tool(self):
        """Test the force_release_lock admin tool"""
        server = FileWorkspaceServer("file-workspace", "1.0.0")
        
        # Acquire a lock
        server.acquire_file_lock({
            "file_path": "/workspace/test.py",
            "agent_id": "agent-1",
            "timeout_seconds": 300
        })
        
        # Force release it (admin action)
        result = server.force_release_lock({
            "file_path": "/workspace/test.py",
            "admin_reason": "System maintenance"
        })
        
        assert result["success"] is True
        assert result["forced"] is True
        
        # Verify lock is released
        status = server.get_file_lock_status({"file_path": "/workspace/test.py"})
        assert status["status"] == "unlocked"


@pytest.mark.us009
class TestUS009Integration:
    """Integration tests to verify all US-009 acceptance criteria"""
    
    @pytest.mark.asyncio
    async def test_complete_file_locking_workflow(self):
        """Test complete workflow covering all acceptance criteria"""
        server = FileWorkspaceServer("file-workspace", "1.0.0")
        
        # ✅ File locks can be acquired and released
        acquire_result = server.acquire_file_lock({
            "file_path": "/workspace/main.py",
            "agent_id": "agent-1",
            "timeout_seconds": 300  # ✅ Lock requests include timeout duration
        })
        assert acquire_result["success"] is True
        
        # ✅ Lock status is visible to all agents
        status = server.get_file_lock_status({"file_path": "/workspace/main.py"})
        assert status["status"] == "locked"
        assert status["agent_id"] == "agent-1"
        
        # ✅ Concurrent lock attempts are queued
        queue_result = server.locking_service.queue_lock_request(
            file_path="/workspace/main.py",
            agent_id="agent-2",
            timeout_seconds=300
        )
        assert queue_result["queued"] is True
        assert queue_result["position"] == 1
        
        # Release the lock
        release_result = server.release_file_lock({
            "file_path": "/workspace/main.py",
            "agent_id": "agent-1"
        })
        assert release_result["success"] is True
        
        # ✅ Stale locks are cleaned up automatically (tested with short timeout)
        server.acquire_file_lock({
            "file_path": "/workspace/temp.py",
            "agent_id": "agent-3",
            "timeout_seconds": 1  # Short timeout for testing
        })
        
        await asyncio.sleep(1.5)  # Wait for expiry
        
        cleanup_result = server.cleanup_service.cleanup_expired_locks()
        assert cleanup_result["cleaned_count"] >= 1
        
        final_status = server.get_file_lock_status({"file_path": "/workspace/temp.py"})
        assert final_status["status"] == "unlocked"
        
        print("✅ All US-009 acceptance criteria verified!")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])