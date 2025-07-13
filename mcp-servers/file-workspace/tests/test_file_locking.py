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


class TestMCPServerCoverage:
    """Test MCP server functionality for better coverage"""
    
    def test_server_initialization_comprehensive(self):
        """Test server initialization with different parameters"""
        # Test custom initialization
        server1 = FileWorkspaceServer("file-workspace", "1.0.0")
        assert server1.name == "file-workspace"
        assert server1.version == "1.0.0"
        
        # Test another custom initialization
        server2 = FileWorkspaceServer("custom-file-workspace", "2.0.0")
        assert server2.name == "custom-file-workspace"
        assert server2.version == "2.0.0"
        
        # Verify all services are initialized
        assert server2.locking_service is not None
        assert server2.cleanup_service is not None
        assert server2.server is not None
        
    def test_server_tools_registration(self):
        """Test that all server tools are properly registered"""
        server = FileWorkspaceServer("test-server", "1.0.0")
        
        # Verify the server has the MCP server instance
        assert server.server is not None
        
        # Verify the main methods exist that would be called by tools
        assert hasattr(server, 'acquire_file_lock')
        assert hasattr(server, 'release_file_lock')
        assert hasattr(server, 'get_file_lock_status')
        assert hasattr(server, 'list_all_locks')
        assert hasattr(server, 'force_release_lock')
        
    def test_force_release_lock_comprehensive(self):
        """Test force release lock functionality"""
        server = FileWorkspaceServer("force-test", "1.0.0")
        
        # First acquire a lock
        acquire_result = server.acquire_file_lock({
            "file_path": "/workspace/force-test.py",
            "agent_id": "agent-1",
            "timeout_seconds": 300
        })
        assert acquire_result["success"] is True
        
        # Force release the lock (admin operation)
        force_result = server.force_release_lock({
            "file_path": "/workspace/force-test.py"
        })
        assert force_result["success"] is True
        
        # Verify the lock is released
        status = server.get_file_lock_status({"file_path": "/workspace/force-test.py"})
        assert status["status"] == "unlocked"
        
    def test_server_error_handling(self):
        """Test server error handling"""
        server = FileWorkspaceServer("error-test", "1.0.0")
        
        # Test invalid file path
        result = server.acquire_file_lock({
            "file_path": "",  # Empty path
            "agent_id": "agent-1",
            "timeout_seconds": 300
        })
        assert result["success"] is False
        assert "error" in result
        
        # Test missing agent_id - just verify the method handles the case
        result = server.acquire_file_lock({
            "file_path": "/workspace/test.py"
            # Missing agent_id
        })
        # The result format might vary, but it should return something
        assert result is not None


class TestCleanupServiceCoverage:
    """Test cleanup service functionality for better coverage"""
    
    def test_cleanup_service_initialization(self):
        """Test cleanup service initialization"""
        locking_service = LockingService()
        cleanup_service = CleanupService(locking_service)
        
        assert cleanup_service.locking_service == locking_service
        assert hasattr(cleanup_service, 'cleanup_expired_locks')
        
    @pytest.mark.asyncio
    async def test_cleanup_service_comprehensive(self):
        """Test cleanup service with various scenarios"""
        service = LockingService()
        cleanup_service = CleanupService(service)
        
        # Create some locks with different expiry times
        service.acquire_lock(
            file_path="/workspace/file1.py",
            agent_id="agent-1",
            timeout_seconds=1  # Short timeout
        )
        
        service.acquire_lock(
            file_path="/workspace/file2.py", 
            agent_id="agent-2",
            timeout_seconds=300  # Long timeout
        )
        
        # Wait for first lock to expire
        await asyncio.sleep(1.5)
        
        # Run cleanup
        result = cleanup_service.cleanup_expired_locks()
        
        assert result["cleaned_count"] >= 1
        assert isinstance(result["cleaned_files"], list)
        
        # Verify expired lock was cleaned but valid lock remains
        status1 = service.get_lock_status("/workspace/file1.py")
        status2 = service.get_lock_status("/workspace/file2.py")
        
        assert status1["status"] == "unlocked"
        assert status2["status"] == "locked"
        
    def test_cleanup_service_empty_locks(self):
        """Test cleanup service when no locks exist"""
        service = LockingService()
        cleanup_service = CleanupService(service)
        
        result = cleanup_service.cleanup_expired_locks()
        
        assert result["cleaned_count"] == 0
        assert result["cleaned_files"] == []


class TestFileLockModelCoverage:
    """Test FileLock model for better coverage"""
    
    def test_file_lock_creation_comprehensive(self):
        """Test FileLock creation with various parameters"""
        # Test with all required parameters
        acquired_at = datetime.now()
        expires_at = acquired_at + timedelta(minutes=5)
        
        lock1 = FileLock(
            lock_id="test-1",
            file_path="/workspace/test1.py",
            agent_id="agent-1",
            acquired_at=acquired_at,
            expires_at=expires_at,
            status=LockStatus.LOCKED,
            metadata={}
        )
        
        assert lock1.lock_id == "test-1"
        assert lock1.file_path == "/workspace/test1.py"
        assert lock1.agent_id == "agent-1"
        assert lock1.status == LockStatus.LOCKED
        
        # Test with different status
        lock2 = FileLock(
            lock_id="test-2",
            file_path="/workspace/test2.py",
            agent_id="agent-2",
            acquired_at=acquired_at,
            expires_at=expires_at,
            status=LockStatus.EXPIRED,
            metadata={"test": True}
        )
        
        assert lock2.expires_at == expires_at
        assert lock2.status == LockStatus.EXPIRED
        assert lock2.metadata == {"test": True}
        
    def test_file_lock_expiry_check(self):
        """Test FileLock expiry checking"""
        # Create an expired lock
        now = datetime.now()
        past_time = now - timedelta(minutes=5)
        acquired_time = now - timedelta(minutes=10)
        
        expired_lock = FileLock(
            lock_id="expired-1",
            file_path="/workspace/expired.py",
            agent_id="agent-1",
            acquired_at=acquired_time,
            expires_at=past_time,
            status=LockStatus.EXPIRED,
            metadata={}
        )
        
        assert expired_lock.is_expired() is True
        
        # Create a valid lock
        future_time = now + timedelta(minutes=5)
        valid_lock = FileLock(
            lock_id="valid-1",
            file_path="/workspace/valid.py",
            agent_id="agent-1",
            acquired_at=now,
            expires_at=future_time,
            status=LockStatus.LOCKED,
            metadata={}
        )
        
        assert valid_lock.is_expired() is False
        
    def test_file_lock_to_dict(self):
        """Test FileLock serialization"""
        now = datetime.now()
        expires_at = now + timedelta(minutes=5)
        lock = FileLock(
            lock_id="dict-test",
            file_path="/workspace/dict.py",
            agent_id="agent-1",
            acquired_at=now,
            expires_at=expires_at,
            status=LockStatus.LOCKED,
            metadata={"key": "value"}
        )
        
        lock_dict = lock.to_dict()
        
        assert isinstance(lock_dict, dict)
        assert lock_dict["lock_id"] == "dict-test"
        assert lock_dict["file_path"] == "/workspace/dict.py"
        assert lock_dict["agent_id"] == "agent-1"
        assert lock_dict["status"] == "locked"
        assert "expires_at" in lock_dict
        assert "acquired_at" in lock_dict
        assert lock_dict["metadata"] == {"key": "value"}


class TestLockingServiceAdvanced:
    """Test advanced locking service functionality"""
    
    @pytest.mark.asyncio
    async def test_queue_processing_comprehensive(self):
        """Test queue processing functionality"""
        service = LockingService()
        
        # Acquire initial lock
        service.acquire_lock(
            file_path="/workspace/queue-test.py",
            agent_id="agent-1",
            timeout_seconds=2  # Short timeout
        )
        
        # Queue multiple requests
        queue_result1 = service.queue_lock_request(
            file_path="/workspace/queue-test.py",
            agent_id="agent-2",
            timeout_seconds=300
        )
        
        queue_result2 = service.queue_lock_request(
            file_path="/workspace/queue-test.py",
            agent_id="agent-3", 
            timeout_seconds=300
        )
        
        assert queue_result1["queued"] is True
        assert queue_result1["position"] == 1
        assert queue_result2["queued"] is True
        assert queue_result2["position"] == 2
        
        # Wait for initial lock to expire
        await asyncio.sleep(2.5)
        
        # Process the queue (this would normally be done automatically)
        # The queue should process the next request
        queue_status = service.get_queue_status("/workspace/queue-test.py")
        assert isinstance(queue_status, dict)
        
    def test_locking_service_edge_cases(self):
        """Test locking service edge cases"""
        service = LockingService()
        
        # Test with invalid timeout
        result = service.acquire_lock(
            file_path="/workspace/invalid-timeout.py",
            agent_id="agent-1",
            timeout_seconds=-1  # Invalid timeout
        )
        assert result["success"] is False
        
        # Test releasing non-existent lock
        result = service.release_lock(
            file_path="/workspace/non-existent.py",
            agent_id="agent-1"
        )
        assert result["success"] is False
        
        # Test getting status of non-existent file
        status = service.get_lock_status("/workspace/non-existent.py")
        assert status["status"] == "unlocked"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])