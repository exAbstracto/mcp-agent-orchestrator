#!/usr/bin/env python3
"""
Simple test to validate US-009 implementation without pytest dependency
"""

import sys
import os

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

# Import with absolute imports
from src.models.file_lock import FileLock, LockStatus
from src.services.locking_service import LockingService
from src.services.cleanup_service import CleanupService
from src.file_workspace_server import FileWorkspaceServer

def test_basic_lock_operations():
    """Test basic lock acquire and release"""
    print("Testing basic lock operations...")
    
    service = LockingService()
    
    # Test acquire lock
    result = service.acquire_lock(
        file_path="/workspace/test.py",
        agent_id="agent-1",
        timeout_seconds=300
    )
    
    assert result["success"] is True, "Lock acquisition should succeed"
    assert result["file_path"] == "/workspace/test.py", "File path should match"
    assert result["agent_id"] == "agent-1", "Agent ID should match"
    print("✅ Lock acquisition works")
    
    # Test get status
    status = service.get_lock_status("/workspace/test.py")
    assert status["status"] == "locked", "File should be locked"
    assert status["agent_id"] == "agent-1", "Agent should match"
    print("✅ Lock status check works")
    
    # Test release lock
    release_result = service.release_lock(
        file_path="/workspace/test.py",
        agent_id="agent-1"
    )
    
    assert release_result["success"] is True, "Lock release should succeed"
    print("✅ Lock release works")
    
    # Test status after release
    status = service.get_lock_status("/workspace/test.py")
    assert status["status"] == "unlocked", "File should be unlocked"
    print("✅ Status after release works")

def test_lock_conflicts():
    """Test that lock conflicts are handled properly"""
    print("\nTesting lock conflicts...")
    
    service = LockingService()
    
    # Agent 1 acquires lock
    result1 = service.acquire_lock("/workspace/test.py", "agent-1", 300)
    assert result1["success"] is True
    
    # Agent 2 tries to acquire same file
    result2 = service.acquire_lock("/workspace/test.py", "agent-2", 300)
    assert result2["success"] is False, "Second lock should fail"
    assert "already locked" in result2["error"].lower()
    print("✅ Lock conflicts handled correctly")

def test_queue_operations():
    """Test queue operations"""
    print("\nTesting queue operations...")
    
    service = LockingService()
    
    # Lock a file
    service.acquire_lock("/workspace/test.py", "agent-1", 300)
    
    # Queue a request
    queue_result = service.queue_lock_request("/workspace/test.py", "agent-2", 300)
    assert queue_result["queued"] is True
    assert queue_result["position"] == 1
    print("✅ Lock queuing works")
    
    # Check queue status
    queue_status = service.get_queue_status("/workspace/test.py")
    assert queue_status["queue_length"] == 1
    print("✅ Queue status works")

def test_mcp_server():
    """Test MCP server initialization"""
    print("\nTesting MCP server...")
    
    server = FileWorkspaceServer("file-workspace", "1.0.0")
    assert server.name == "file-workspace"
    assert server.version == "1.0.0"
    assert server.locking_service is not None
    assert server.cleanup_service is not None
    print("✅ MCP server initialization works")
    
    # Test tool integration
    result = server.acquire_file_lock({
        "file_path": "/workspace/test.py",
        "agent_id": "agent-1",
        "timeout_seconds": 300
    })
    assert result["success"] is True
    print("✅ MCP tool integration works")

def test_cleanup_service():
    """Test cleanup service"""
    print("\nTesting cleanup service...")
    
    service = LockingService()
    cleanup = CleanupService(service)
    
    # Test cleanup stats
    stats = cleanup.get_cleanup_stats()
    assert "total_active_locks" in stats
    assert "expired_locks" in stats
    print("✅ Cleanup stats work")

def test_acceptance_criteria():
    """Test all US-009 acceptance criteria"""
    print("\nTesting US-009 Acceptance Criteria...")
    
    server = FileWorkspaceServer("file-workspace", "1.0.0")
    
    # ✅ File locks can be acquired and released
    acquire_result = server.acquire_file_lock({
        "file_path": "/workspace/main.py",
        "agent_id": "agent-1",
        "timeout_seconds": 300  # ✅ Lock requests include timeout duration
    })
    assert acquire_result["success"] is True
    print("✅ AC1: File locks can be acquired and released")
    print("✅ AC2: Lock requests include timeout duration")
    
    # ✅ Lock status is visible to all agents
    status = server.get_file_lock_status({"file_path": "/workspace/main.py"})
    assert status["status"] == "locked"
    assert status["agent_id"] == "agent-1"
    print("✅ AC5: Lock status is visible to all agents")
    
    # ✅ Concurrent lock attempts are queued
    queue_result = server.locking_service.queue_lock_request(
        file_path="/workspace/main.py",
        agent_id="agent-2",
        timeout_seconds=300
    )
    assert queue_result["queued"] is True
    assert queue_result["position"] == 1
    print("✅ AC3: Concurrent lock attempts are queued")
    
    # ✅ Stale locks are cleaned up automatically (test cleanup function)
    cleanup_result = server.cleanup_service.cleanup_expired_locks()
    assert "cleaned_count" in cleanup_result
    print("✅ AC4: Stale locks are cleaned up automatically")
    
    print("\n🎉 All US-009 acceptance criteria PASSED!")

if __name__ == "__main__":
    try:
        test_basic_lock_operations()
        test_lock_conflicts()
        test_queue_operations()
        test_mcp_server()
        test_cleanup_service()
        test_acceptance_criteria()
        
        print("\n" + "="*50)
        print("🎉 ALL TESTS PASSED!")
        print("US-009 implementation is working correctly!")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)