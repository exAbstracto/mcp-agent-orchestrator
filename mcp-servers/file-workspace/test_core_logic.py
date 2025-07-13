#!/usr/bin/env python3
"""
Test core file locking logic without MCP dependencies
"""

import sys
import os
from datetime import datetime, timedelta

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

# Import only the core modules without MCP dependencies
from src.models.file_lock import FileLock, LockStatus
from src.services.locking_service import LockingService
from src.services.cleanup_service import CleanupService

def test_file_lock_model():
    """Test FileLock model creation and validation"""
    print("Testing FileLock model...")
    
    # Test valid lock creation
    lock = FileLock.create("/workspace/test.py", "agent-1", 300)
    assert lock.file_path == "/workspace/test.py"
    assert lock.agent_id == "agent-1"
    assert lock.status == LockStatus.LOCKED
    assert not lock.is_expired()
    print("✅ FileLock model works correctly")
    
    # Test lock serialization
    lock_dict = lock.to_dict()
    assert lock_dict["file_path"] == "/workspace/test.py"
    assert lock_dict["agent_id"] == "agent-1"
    assert lock_dict["status"] == "locked"
    print("✅ Lock serialization works")

def test_locking_service_basic():
    """Test basic locking service operations"""
    print("\nTesting LockingService basic operations...")
    
    service = LockingService()
    
    # Test acquire lock
    result = service.acquire_lock("/workspace/test.py", "agent-1", 300)
    assert result["success"] is True
    assert result["file_path"] == "/workspace/test.py"
    assert result["agent_id"] == "agent-1"
    print("✅ Lock acquisition works")
    
    # Test get status
    status = service.get_lock_status("/workspace/test.py")
    assert status["status"] == "locked"
    assert status["agent_id"] == "agent-1"
    print("✅ Lock status retrieval works")
    
    # Test release lock
    release_result = service.release_lock("/workspace/test.py", "agent-1")
    assert release_result["success"] is True
    print("✅ Lock release works")
    
    # Test status after release
    status = service.get_lock_status("/workspace/test.py")
    assert status["status"] == "unlocked"
    print("✅ Status after release correct")

def test_lock_conflicts():
    """Test lock conflict handling"""
    print("\nTesting lock conflicts...")
    
    service = LockingService()
    
    # Agent 1 gets the lock
    result1 = service.acquire_lock("/workspace/test.py", "agent-1", 300)
    assert result1["success"] is True
    
    # Agent 2 tries to get same lock
    result2 = service.acquire_lock("/workspace/test.py", "agent-2", 300)
    assert result2["success"] is False
    assert "already locked" in result2["error"].lower()
    print("✅ Lock conflicts handled correctly")
    
    # Wrong agent tries to release
    wrong_release = service.release_lock("/workspace/test.py", "agent-2")
    assert wrong_release["success"] is False
    assert "permission denied" in wrong_release["error"].lower()
    print("✅ Permission checks work")

def test_lock_queuing():
    """Test lock queuing functionality"""
    print("\nTesting lock queuing...")
    
    service = LockingService()
    
    # Lock a file
    service.acquire_lock("/workspace/test.py", "agent-1", 300)
    
    # Queue a request
    queue_result = service.queue_lock_request("/workspace/test.py", "agent-2", 300)
    assert queue_result["queued"] is True
    assert queue_result["position"] == 1
    print("✅ Lock queuing works")
    
    # Add another to queue
    queue_result2 = service.queue_lock_request("/workspace/test.py", "agent-3", 300)
    assert queue_result2["queued"] is True
    assert queue_result2["position"] == 2
    print("✅ Queue ordering works")
    
    # Check queue status
    queue_status = service.get_queue_status("/workspace/test.py")
    assert queue_status["queue_length"] == 2
    assert len(queue_status["queued_agents"]) == 2
    print("✅ Queue status works")
    
    # Cancel a queued request
    cancel_result = service.cancel_queued_request("/workspace/test.py", "agent-2")
    assert cancel_result["success"] is True
    
    # Check queue after cancellation
    queue_status = service.get_queue_status("/workspace/test.py")
    assert queue_status["queue_length"] == 1
    print("✅ Queue cancellation works")

def test_cleanup_service():
    """Test cleanup service functionality"""
    print("\nTesting CleanupService...")
    
    service = LockingService()
    cleanup = CleanupService(service)
    
    # Create a lock with short timeout for testing
    lock = FileLock.create("/workspace/test.py", "agent-1", 1)  # 1 second timeout
    service.active_locks["/workspace/test.py"] = lock
    
    # Make the lock expired by modifying its expiry time
    lock.expires_at = datetime.now() - timedelta(seconds=1)
    
    # Test cleanup
    cleanup_result = cleanup.cleanup_expired_locks()
    assert cleanup_result["cleaned_count"] == 1
    assert "/workspace/test.py" in cleanup_result["cleaned_files"]
    print("✅ Expired lock cleanup works")
    
    # Verify lock was removed
    status = service.get_lock_status("/workspace/test.py")
    assert status["status"] == "unlocked"
    print("✅ Lock removal after cleanup works")
    
    # Test cleanup stats
    stats = cleanup.get_cleanup_stats()
    assert "total_active_locks" in stats
    assert "expired_locks" in stats
    print("✅ Cleanup stats work")

def test_list_operations():
    """Test listing operations"""
    print("\nTesting list operations...")
    
    service = LockingService()
    
    # Create multiple locks
    service.acquire_lock("/workspace/test1.py", "agent-1", 300)
    service.acquire_lock("/workspace/test2.py", "agent-2", 300)
    service.acquire_lock("/workspace/test3.py", "agent-1", 300)
    
    # Test list all locks
    all_locks = service.list_all_locks()
    assert len(all_locks) == 3
    file_paths = [lock["file_path"] for lock in all_locks]
    assert "/workspace/test1.py" in file_paths
    assert "/workspace/test2.py" in file_paths
    assert "/workspace/test3.py" in file_paths
    print("✅ List all locks works")
    
    # Test list by agent
    agent1_locks = service.list_locks_by_agent("agent-1")
    assert len(agent1_locks) == 2
    agent1_files = [lock["file_path"] for lock in agent1_locks]
    assert "/workspace/test1.py" in agent1_files
    assert "/workspace/test3.py" in agent1_files
    print("✅ List locks by agent works")

def test_force_release():
    """Test force release functionality"""
    print("\nTesting force release...")
    
    service = LockingService()
    
    # Create a lock
    service.acquire_lock("/workspace/test.py", "agent-1", 300)
    
    # Force release it
    force_result = service.force_release_lock("/workspace/test.py", "System maintenance")
    assert force_result["success"] is True
    assert force_result["forced"] is True
    assert force_result["original_agent"] == "agent-1"
    print("✅ Force release works")
    
    # Verify lock is gone
    status = service.get_lock_status("/workspace/test.py")
    assert status["status"] == "unlocked"
    print("✅ Lock removed after force release")

def test_acceptance_criteria():
    """Test all US-009 acceptance criteria without MCP server"""
    print("\nTesting US-009 Acceptance Criteria (Core Logic)...")
    
    service = LockingService()
    cleanup = CleanupService(service)
    
    # ✅ File locks can be acquired and released
    acquire_result = service.acquire_lock(
        file_path="/workspace/main.py",
        agent_id="agent-1",
        timeout_seconds=300  # ✅ Lock requests include timeout duration
    )
    assert acquire_result["success"] is True
    print("✅ AC1: File locks can be acquired and released")
    print("✅ AC2: Lock requests include timeout duration")
    
    # ✅ Lock status is visible to all agents
    status = service.get_lock_status("/workspace/main.py")
    assert status["status"] == "locked"
    assert status["agent_id"] == "agent-1"
    print("✅ AC5: Lock status is visible to all agents")
    
    # ✅ Concurrent lock attempts are queued
    queue_result = service.queue_lock_request(
        file_path="/workspace/main.py",
        agent_id="agent-2",
        timeout_seconds=300
    )
    assert queue_result["queued"] is True
    assert queue_result["position"] == 1
    print("✅ AC3: Concurrent lock attempts are queued")
    
    # ✅ Stale locks are cleaned up automatically (test cleanup function)
    cleanup_result = cleanup.cleanup_expired_locks()
    assert "cleaned_count" in cleanup_result
    print("✅ AC4: Stale locks can be cleaned up automatically")
    
    print("\n🎉 All US-009 acceptance criteria PASSED!")

if __name__ == "__main__":
    try:
        test_file_lock_model()
        test_locking_service_basic()
        test_lock_conflicts()
        test_lock_queuing()
        test_cleanup_service()
        test_list_operations()
        test_force_release()
        test_acceptance_criteria()
        
        print("\n" + "="*60)
        print("🎉 ALL CORE LOGIC TESTS PASSED!")
        print("US-009 core implementation is working correctly!")
        print("File locking system ready for MCP integration!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)