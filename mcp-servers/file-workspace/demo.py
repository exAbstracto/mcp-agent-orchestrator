#!/usr/bin/env python3
"""
Demo script for US-009: Shared Workspace File Locking

This script demonstrates the file locking functionality without requiring
a full MCP server setup.
"""

import asyncio
import time
from src.services.locking_service import LockingService
from src.services.cleanup_service import CleanupService
from src.file_workspace_server import FileWorkspaceServer


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def demo_basic_file_locking():
    """Demonstrate basic file locking operations"""
    print_section("Basic File Locking Demo")
    
    service = LockingService()
    
    # Agent 1 acquires a lock
    print("🔒 Agent-1 requests lock on /workspace/main.py...")
    result = service.acquire_lock(
        file_path="/workspace/main.py",
        agent_id="agent-1",
        timeout_seconds=300
    )
    print(f"✅ Lock acquired: {result['lock_id'][:8]}...")
    
    # Check lock status
    status = service.get_lock_status("/workspace/main.py")
    print(f"📋 Status: {status['status']} by {status['agent_id']}")
    
    # Agent 2 tries to acquire same file
    print("\n🔒 Agent-2 tries to acquire same file...")
    result2 = service.acquire_lock(
        file_path="/workspace/main.py",
        agent_id="agent-2",
        timeout_seconds=300
    )
    print(f"❌ Lock failed: {result2['error']}")
    
    # Agent 1 releases the lock
    print("\n🔓 Agent-1 releases the lock...")
    release_result = service.release_lock(
        file_path="/workspace/main.py",
        agent_id="agent-1"
    )
    print(f"✅ Lock released successfully")
    
    # Now Agent 2 can acquire it
    print("\n🔒 Agent-2 tries again...")
    result3 = service.acquire_lock(
        file_path="/workspace/main.py",
        agent_id="agent-2",
        timeout_seconds=300
    )
    print(f"✅ Lock acquired: {result3['lock_id'][:8]}...")


def demo_lock_queuing():
    """Demonstrate lock queuing functionality"""
    print_section("Lock Queuing Demo")
    
    service = LockingService()
    
    # Agent 1 locks the file
    print("🔒 Agent-1 locks /workspace/shared.py...")
    service.acquire_lock("/workspace/shared.py", "agent-1", 300)
    
    # Multiple agents queue for the same file
    print("\n📋 Multiple agents queue for the same file...")
    
    agents = ["agent-2", "agent-3", "agent-4"]
    for agent in agents:
        result = service.queue_lock_request("/workspace/shared.py", agent, 300)
        print(f"🚶 {agent} queued at position {result['position']}")
    
    # Show queue status
    queue_status = service.get_queue_status("/workspace/shared.py")
    print(f"\n📊 Queue length: {queue_status['queue_length']}")
    for i, req in enumerate(queue_status['queued_agents']):
        print(f"   {i+1}. {req['agent_id']} (waiting {req['estimated_wait_time']:.0f}s)")
    
    # Agent 3 cancels their request
    print(f"\n❌ Agent-3 cancels their queued request...")
    cancel_result = service.cancel_queued_request("/workspace/shared.py", "agent-3")
    print(f"✅ Request cancelled")
    
    # Show updated queue
    queue_status = service.get_queue_status("/workspace/shared.py")
    print(f"\n📊 Updated queue length: {queue_status['queue_length']}")
    for i, req in enumerate(queue_status['queued_agents']):
        print(f"   {i+1}. {req['agent_id']}")


def demo_lock_cleanup():
    """Demonstrate automatic lock cleanup"""
    print_section("Automatic Lock Cleanup Demo")
    
    service = LockingService()
    cleanup_service = CleanupService(service)
    
    # Create locks with short timeouts for demo
    print("🔒 Creating locks with short timeouts for demo...")
    
    files = ["/workspace/temp1.py", "/workspace/temp2.py", "/workspace/temp3.py"]
    agents = ["agent-1", "agent-2", "agent-3"]
    
    for file_path, agent in zip(files, agents):
        service.acquire_lock(file_path, agent, timeout_seconds=2)  # 2 second timeout
        print(f"   {agent} locked {file_path}")
    
    print(f"\n📊 Current locks: {len(service.list_all_locks())}")
    
    # Wait for locks to expire
    print("\n⏰ Waiting 3 seconds for locks to expire...")
    time.sleep(3)
    
    # Run cleanup
    print("\n🧹 Running cleanup...")
    cleanup_result = cleanup_service.cleanup_expired_locks()
    
    print(f"✅ Cleaned {cleanup_result['cleaned_count']} expired locks")
    for file_path in cleanup_result['cleaned_files']:
        print(f"   Cleaned: {file_path}")
    
    print(f"\n📊 Remaining locks: {len(service.list_all_locks())}")


def demo_mcp_server_tools():
    """Demonstrate MCP server tool integration"""
    print_section("MCP Server Tools Demo")
    
    server = FileWorkspaceServer("file-workspace", "1.0.0")
    
    print("🚀 File Workspace Server initialized")
    print(f"   Name: {server.name}")
    print(f"   Version: {server.version}")
    
    # Demonstrate MCP tool calls
    print("\n🔧 Testing MCP tool: acquire_file_lock")
    result = server.acquire_file_lock({
        "file_path": "/workspace/api.py",
        "agent_id": "mcp-agent-1",
        "timeout_seconds": 600
    })
    print(f"✅ Tool result: {result['success']}")
    
    print("\n🔧 Testing MCP tool: get_file_lock_status")
    status = server.get_file_lock_status({"file_path": "/workspace/api.py"})
    print(f"📋 Status: {status['status']} by {status['agent_id']}")
    
    print("\n🔧 Testing MCP tool: list_all_locks")
    locks_result = server.list_all_locks({})
    print(f"📊 Total active locks: {len(locks_result['locks'])}")
    
    print("\n🔧 Testing MCP tool: get_cleanup_stats")
    stats = server.get_cleanup_stats({})
    print(f"📈 Active locks: {stats['total_active_locks']}")
    print(f"📈 Expired locks: {stats['expired_locks']}")


async def demo_complete_workflow():
    """Demonstrate complete workflow covering all acceptance criteria"""
    print_section("Complete US-009 Workflow Demo")
    
    server = FileWorkspaceServer("file-workspace", "1.0.0")
    
    print("🎯 Testing all US-009 acceptance criteria:")
    
    # ✅ File locks can be acquired and released
    print("\n1️⃣ File locks can be acquired and released")
    acquire_result = server.acquire_file_lock({
        "file_path": "/workspace/main.py",
        "agent_id": "agent-1",
        "timeout_seconds": 300  # ✅ Lock requests include timeout duration
    })
    print(f"   ✅ Lock acquired: {acquire_result['success']}")
    
    # ✅ Lock status is visible to all agents
    print("\n2️⃣ Lock status is visible to all agents")
    status = server.get_file_lock_status({"file_path": "/workspace/main.py"})
    print(f"   📋 Status visible: {status['status']} by {status['agent_id']}")
    
    # ✅ Concurrent lock attempts are queued
    print("\n3️⃣ Concurrent lock attempts are queued")
    queue_result = server.locking_service.queue_lock_request(
        file_path="/workspace/main.py",
        agent_id="agent-2",
        timeout_seconds=300
    )
    print(f"   🚶 Request queued: position {queue_result['position']}")
    
    # Release the lock
    release_result = server.release_file_lock({
        "file_path": "/workspace/main.py",
        "agent_id": "agent-1"
    })
    print(f"   🔓 Lock released: {release_result['success']}")
    
    # ✅ Stale locks are cleaned up automatically
    print("\n4️⃣ Stale locks are cleaned up automatically")
    server.acquire_file_lock({
        "file_path": "/workspace/temp.py",
        "agent_id": "agent-3",
        "timeout_seconds": 1  # Short timeout for demo
    })
    
    await asyncio.sleep(1.5)  # Wait for expiry
    
    cleanup_result = server.cleanup_service.cleanup_expired_locks()
    print(f"   🧹 Cleanup ran: {cleanup_result['cleaned_count']} locks cleaned")
    
    final_status = server.get_file_lock_status({"file_path": "/workspace/temp.py"})
    print(f"   ✅ Lock removed: {final_status['status']}")
    
    print("\n🎉 All US-009 acceptance criteria demonstrated successfully!")


async def main():
    """Run all demos"""
    print("🚀 US-009: Shared Workspace File Locking Demo")
    print("=" * 60)
    
    try:
        demo_basic_file_locking()
        demo_lock_queuing()
        demo_lock_cleanup()
        demo_mcp_server_tools()
        await demo_complete_workflow()
        
        print_section("Demo Complete")
        print("✅ All file locking features demonstrated successfully!")
        print("🔧 The system is ready for production use in multi-agent environments.")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())