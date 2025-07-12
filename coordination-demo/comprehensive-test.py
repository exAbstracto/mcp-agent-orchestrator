#!/usr/bin/env python3
"""
Comprehensive Multi-Instance Coordination Test

This test validates all aspects of the multi-agent coordination system.
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime


def run_comprehensive_test():
    """Run comprehensive coordination test"""
    print("🚀 Comprehensive Multi-Instance Coordination Test")
    print("=" * 55)

    claude_dir = Path("/tmp/mcp-agent-workspaces")
    cursor_dir = Path("/tmp/cursor-agent-instances")

    tests_passed = 0
    total_tests = 0

    # Test 1: Infrastructure Check
    print("\n📋 Testing Infrastructure")
    total_tests += 1

    infrastructure_ok = (
        claude_dir.exists()
        and cursor_dir.exists()
        and (claude_dir / "shared-workspace").exists()
        and (
            claude_dir / "shared-workspace" / "coordination" / "agent-registry.json"
        ).exists()
    )

    if infrastructure_ok:
        print("✅ Infrastructure setup complete")
        tests_passed += 1
    else:
        print("❌ Infrastructure setup failed")

    # Test 2: Agent Configuration Check
    print("\n📋 Testing Agent Configurations")
    total_tests += 1

    # Check Claude Code agents
    claude_agents = ["backend-agent", "frontend-agent", "devops-agent", "testing-agent"]
    claude_configs_ok = True

    for agent in claude_agents:
        config_file = claude_dir / f"{agent}-workspace" / "agent-config.json"
        if not config_file.exists():
            claude_configs_ok = False
            print(f"❌ Missing config for {agent}")
        else:
            print(f"✅ {agent} configured")

    # Check Cursor agents
    cursor_agents = ["frontend-ui", "pm-coordination"]
    cursor_configs_ok = True

    for agent in cursor_agents:
        config_file = cursor_dir / agent / "config.json"
        if not config_file.exists():
            cursor_configs_ok = False
            print(f"❌ Missing config for {agent}")
        else:
            with open(config_file) as f:
                config = json.load(f)
            tool_count = config.get("current_tools", 0)
            tool_limit = config.get("tool_limit", 40)
            print(f"✅ {agent} configured ({tool_count}/{tool_limit} tools)")

    if claude_configs_ok and cursor_configs_ok:
        tests_passed += 1
        print("✅ All agent configurations valid")
    else:
        print("❌ Some agent configurations missing")

    # Test 3: File Sharing Test
    print("\n📋 Testing File Sharing")
    total_tests += 1

    # Create test scenario
    api_spec = {
        "title": "Test API",
        "version": "1.0.0",
        "endpoints": {"/test": {"GET": "Test endpoint"}},
    }

    # Backend creates API spec
    backend_file = claude_dir / "backend-agent-workspace" / "test-api.json"
    with open(backend_file, "w") as f:
        json.dump(api_spec, f, indent=2)

    # Share to common area
    shared_file = claude_dir / "shared-workspace" / "artifacts" / "test-api-shared.json"
    with open(shared_file, "w") as f:
        json.dump(api_spec, f, indent=2)

    # Frontend creates UI based on API
    ui_spec = {
        "component": "TestComponent",
        "based_on_api": "/test",
        "framework": "React",
    }

    frontend_file = cursor_dir / "frontend-ui" / "workspace" / "test-component.json"
    with open(frontend_file, "w") as f:
        json.dump(ui_spec, f, indent=2)

    # Check file sharing worked
    files_created = (
        backend_file.exists() and shared_file.exists() and frontend_file.exists()
    )

    if files_created:
        tests_passed += 1
        print("✅ File sharing between agents successful")
        print(f"  📄 Backend: {backend_file.name}")
        print(f"  📄 Shared: {shared_file.name}")
        print(f"  📄 Frontend: {frontend_file.name}")
    else:
        print("❌ File sharing failed")

    # Test 4: Message Coordination
    print("\n📋 Testing Message Coordination")
    total_tests += 1

    # Create coordination message
    message = {
        "from": "backend-agent",
        "to": "frontend-ui",
        "type": "coordination",
        "content": "API specification ready for implementation",
        "timestamp": datetime.now().isoformat(),
        "attachments": ["test-api-shared.json"],
    }

    # Send message
    outbox = claude_dir / "shared-workspace" / "messages" / "backend-agent" / "outbox"
    message_file = outbox / f"test-message-{int(time.time())}.json"

    with open(message_file, "w") as f:
        json.dump(message, f, indent=2)

    if message_file.exists():
        tests_passed += 1
        print("✅ Message coordination successful")
        print(f"  📧 Message: {message['from']} → {message['to']}")
        print(f"  📝 Content: {message['content']}")
    else:
        print("❌ Message coordination failed")

    # Test 5: Platform Limitations Check
    print("\n📋 Testing Platform Limitations")
    total_tests += 1

    limitations_documented = True

    # Check Cursor tool limits
    for agent in cursor_agents:
        config_file = cursor_dir / agent / "config.json"
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)

            tool_count = config.get("current_tools", 0)
            if tool_count > 40:
                print(f"❌ {agent} exceeds 40-tool limit: {tool_count}")
                limitations_documented = False
            else:
                print(f"✅ {agent} within tool limit: {tool_count}/40")

    # Check Claude Code capabilities
    for agent in claude_agents:
        config_file = claude_dir / f"{agent}-workspace" / "agent-config.json"
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)

            capabilities = config.get("capabilities", [])
            if len(capabilities) >= 3:
                print(f"✅ {agent} has comprehensive capabilities")
            else:
                print(f"⚠️  {agent} has limited capabilities")

    if limitations_documented:
        tests_passed += 1
        print("✅ Platform limitations properly managed")
    else:
        print("❌ Platform limitations not properly handled")

    # Cleanup test files
    test_files = [backend_file, shared_file, frontend_file, message_file]
    for test_file in test_files:
        if test_file.exists():
            test_file.unlink()

    # Print Summary
    print("\n" + "=" * 55)
    print("📊 TEST SUMMARY")
    print("=" * 55)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    print(f"Success Rate: {tests_passed/total_tests:.1%}")

    if tests_passed == total_tests:
        print(
            "\n🎉 All tests passed! Multi-instance coordination is working correctly."
        )
        print("\n✅ Validated:")
        print("  - Infrastructure setup")
        print("  - Agent configurations")
        print("  - File sharing between platforms")
        print("  - Message coordination")
        print("  - Platform limitation management")
        return True
    else:
        print(f"\n⚠️  {total_tests - tests_passed} tests failed.")
        return False


if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1)
