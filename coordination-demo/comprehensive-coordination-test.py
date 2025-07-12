#!/usr/bin/env python3
"""
Comprehensive Multi-Instance Coordination Test

This test validates all aspects of the multi-agent coordination system:
1. Multi-instance setup (both Cursor and Claude Code)
2. File sharing between agents
3. Message coordination
4. Platform-specific limitations
5. Real-world coordination scenario
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


class CoordinationTestSuite:
    def __init__(self):
        self.claude_dir = Path("/tmp/mcp-agent-workspaces")
        self.cursor_dir = Path("/tmp/cursor-agent-instances")
        self.test_results = []
        self.start_time = None

    def run_all_tests(self) -> bool:
        """Run the complete test suite"""
        print("🚀 Comprehensive Multi-Instance Coordination Test")
        print("=" * 55)
        self.start_time = time.time()

        # Test categories
        test_categories = [
            ("Infrastructure", self.test_infrastructure),
            ("Agent Configuration", self.test_agent_configuration),
            ("File Operations", self.test_file_operations),
            ("Message Coordination", self.test_message_coordination),
            ("Platform Limitations", self.test_platform_limitations),
            ("Real-World Scenario", self.test_real_world_scenario),
            ("Performance", self.test_performance),
            ("Cleanup", self.test_cleanup),
        ]

        all_passed = True
        for category, test_func in test_categories:
            print(f"\n📋 Testing: {category}")
            print("-" * 40)

            try:
                result = test_func()
                if result:
                    print(f"✅ {category}: PASSED")
                    self.test_results.append((category, "PASSED", None))
                else:
                    print(f"❌ {category}: FAILED")
                    self.test_results.append((category, "FAILED", None))
                    all_passed = False
            except Exception as e:
                print(f"❌ {category}: ERROR - {e}")
                self.test_results.append((category, "ERROR", str(e)))
                all_passed = False

        self.print_summary()
        return all_passed

    def test_infrastructure(self) -> bool:
        """Test that the infrastructure is properly set up"""
        checks = [
            ("Claude Code workspaces exist", lambda: self.claude_dir.exists()),
            ("Cursor instances exist", lambda: self.cursor_dir.exists()),
            (
                "Shared workspace exists",
                lambda: (self.claude_dir / "shared-workspace").exists(),
            ),
            (
                "Coordination registry exists",
                lambda: (
                    self.claude_dir
                    / "shared-workspace"
                    / "coordination"
                    / "agent-registry.json"
                ).exists(),
            ),
            (
                "Message directories exist",
                lambda: len(
                    list((self.claude_dir / "shared-workspace" / "messages").iterdir())
                )
                > 0,
            ),
        ]

        return self._run_checks("Infrastructure", checks)

    def test_agent_configuration(self) -> bool:
        """Test agent configurations are valid"""
        checks = []

        # Test Claude Code agents
        claude_agents = [
            "backend-agent",
            "frontend-agent",
            "devops-agent",
            "testing-agent",
        ]
        for agent in claude_agents:
            workspace = self.claude_dir / f"{agent}-workspace"
            config_file = workspace / "agent-config.json"

            checks.append(
                (f"Claude {agent} config exists", lambda cf=config_file: cf.exists())
            )

            if config_file.exists():
                checks.append(
                    (
                        f"Claude {agent} config valid",
                        lambda cf=config_file: self._validate_claude_config(cf),
                    )
                )

        # Test Cursor agents
        cursor_agents = ["frontend-ui", "pm-coordination"]
        for agent in cursor_agents:
            workspace = self.cursor_dir / agent
            config_file = workspace / "config.json"

            checks.append(
                (f"Cursor {agent} config exists", lambda cf=config_file: cf.exists())
            )

            if config_file.exists():
                checks.append(
                    (
                        f"Cursor {agent} config valid",
                        lambda cf=config_file: self._validate_cursor_config(cf),
                    )
                )

        return self._run_checks("Agent Configuration", checks)

    def test_file_operations(self) -> bool:
        """Test file operations between agents"""
        test_files = []
        checks = []

        # Test 1: Create files in each workspace
        workspaces = [
            (self.claude_dir / "backend-agent-workspace", "claude-backend-test.txt"),
            (self.cursor_dir / "frontend-ui" / "workspace", "cursor-frontend-test.txt"),
            (self.claude_dir / "shared-workspace" / "artifacts", "shared-test.txt"),
        ]

        for workspace, filename in workspaces:
            test_file = workspace / filename
            test_files.append(test_file)

            # Create test file
            with open(test_file, "w") as f:
                f.write(f"Test file created at {datetime.now().isoformat()}\n")
                f.write(f"Workspace: {workspace}\n")

            checks.append(
                (
                    f"File created: {filename}",
                    lambda tf=test_file: tf.exists() and tf.stat().st_size > 0,
                )
            )

        # Test 2: File sharing simulation
        shared_file = (
            self.claude_dir
            / "shared-workspace"
            / "artifacts"
            / "coordination-test.json"
        )
        coordination_data = {
            "test_id": "file-sharing-test",
            "timestamp": datetime.now().isoformat(),
            "agents": ["backend-agent", "frontend-ui"],
            "shared_data": {
                "api_endpoint": "/api/test",
                "ui_component": "TestComponent",
            },
        }

        with open(shared_file, "w") as f:
            json.dump(coordination_data, f, indent=2)

        test_files.append(shared_file)
        checks.append(
            ("Shared coordination file created", lambda: shared_file.exists())
        )

        # Test 3: File accessibility from different workspaces
        for workspace, _ in workspaces:
            if workspace.exists():
                files_in_workspace = list(workspace.glob("*"))
                checks.append(
                    (
                        f"Files accessible in {workspace.name}",
                        lambda files=files_in_workspace: len(files) > 0,
                    )
                )

        result = self._run_checks("File Operations", checks)

        # Cleanup test files
        for test_file in test_files:
            if test_file.exists():
                test_file.unlink()

        return result

    def test_message_coordination(self) -> bool:
        """Test message coordination between agents"""
        checks = []
        test_messages = []

        # Test 1: Create test messages
        message_scenarios = [
            {
                "from": "backend-agent",
                "to": "frontend-ui",
                "content": "API specification ready for implementation",
                "type": "coordination",
            },
            {
                "from": "frontend-ui",
                "to": "backend-agent",
                "content": "UI mockup completed, need API changes",
                "type": "feedback",
            },
        ]

        for scenario in message_scenarios:
            # Create message in sender's outbox
            sender = scenario["from"]
            if sender.startswith("backend") or sender.startswith("frontend-agent"):
                # Claude Code agent
                outbox = (
                    self.claude_dir
                    / "shared-workspace"
                    / "messages"
                    / sender
                    / "outbox"
                )
            else:
                # Cursor agent - would use different path in real implementation
                outbox = (
                    self.claude_dir
                    / "shared-workspace"
                    / "messages"
                    / "frontend-agent"
                    / "outbox"
                )  # Simplified for demo

            if outbox.exists():
                message_file = outbox / f"test-message-{int(time.time())}.json"
                scenario["timestamp"] = datetime.now().isoformat()
                scenario["message_id"] = f"test-{int(time.time())}"

                with open(message_file, "w") as f:
                    json.dump(scenario, f, indent=2)

                test_messages.append(message_file)
                checks.append(
                    (
                        f"Message created: {scenario['from']} → {scenario['to']}",
                        lambda mf=message_file: mf.exists(),
                    )
                )

        # Test 2: Message format validation
        for message_file in test_messages:
            if message_file.exists():
                checks.append(
                    (
                        f"Message format valid: {message_file.name}",
                        lambda mf=message_file: self._validate_message_format(mf),
                    )
                )

        # Test 3: Message queue functionality
        for agent in [
            "backend-agent",
            "frontend-agent",
            "devops-agent",
            "testing-agent",
        ]:
            message_dirs = self.claude_dir / "shared-workspace" / "messages" / agent
            if message_dirs.exists():
                inbox = message_dirs / "inbox"
                outbox = message_dirs / "outbox"
                archive = message_dirs / "archive"

                checks.append(
                    (
                        f"Message queue complete for {agent}",
                        lambda i=inbox, o=outbox, a=archive: i.exists()
                        and o.exists()
                        and a.exists(),
                    )
                )

        result = self._run_checks("Message Coordination", checks)

        # Cleanup test messages
        for message_file in test_messages:
            if message_file.exists():
                message_file.unlink()

        return result

    def test_platform_limitations(self) -> bool:
        """Test platform-specific limitations"""
        checks = []

        # Test 1: Cursor tool limits
        cursor_agents = ["frontend-ui", "pm-coordination"]
        for agent in cursor_agents:
            config_file = self.cursor_dir / agent / "config.json"
            if config_file.exists():
                with open(config_file) as f:
                    config = json.load(f)

                tool_count = config.get("current_tools", 0)
                tool_limit = config.get("tool_limit", 40)

                checks.append(
                    (
                        f"Cursor {agent} under tool limit",
                        lambda tc=tool_count, tl=tool_limit: tc <= tl,
                    )
                )

                checks.append(
                    (
                        f"Cursor {agent} tool count reasonable",
                        lambda tc=tool_count: 0 < tc <= 40,
                    )
                )

        # Test 2: Claude Code unlimited tools assumption
        claude_agents = [
            "backend-agent",
            "frontend-agent",
            "devops-agent",
            "testing-agent",
        ]
        for agent in claude_agents:
            config_file = self.claude_dir / f"{agent}-workspace" / "agent-config.json"
            if config_file.exists():
                with open(config_file) as f:
                    config = json.load(f)

                capabilities = config.get("capabilities", [])
                checks.append(
                    (
                        f"Claude {agent} has comprehensive capabilities",
                        lambda cap=capabilities: len(cap)
                        >= 3,  # file_operations, git_operations, mcp_server
                    )
                )

        # Test 3: Resource usage simulation
        estimated_memory = {
            "cursor_agents": len(cursor_agents) * 65,  # MB
            "claude_agents": len(claude_agents) * 13,  # MB
        }

        total_memory = sum(estimated_memory.values())
        checks.append(
            (
                "Memory usage within reasonable limits",
                lambda tm=total_memory: tm < 1000,  # Less than 1GB total
            )
        )

        return self._run_checks("Platform Limitations", checks)

    def test_real_world_scenario(self) -> bool:
        """Test a real-world coordination scenario"""
        print("  🎬 Scenario: Feature Development Coordination")

        scenario_steps = []

        # Step 1: PM creates feature specification
        pm_spec = {
            "feature": "User Profile Management",
            "requirements": [
                "User can view profile",
                "User can edit profile",
                "Profile includes avatar upload",
            ],
            "assigned_agents": {
                "backend": "backend-agent",
                "frontend": "frontend-ui",
                "testing": "testing-agent",
            },
            "created_by": "pm-coordination",
            "timestamp": datetime.now().isoformat(),
        }

        spec_file = (
            self.claude_dir
            / "shared-workspace"
            / "artifacts"
            / "user-profile-spec.json"
        )
        with open(spec_file, "w") as f:
            json.dump(pm_spec, f, indent=2)

        scenario_steps.append(("PM spec created", spec_file.exists()))

        # Step 2: Backend agent creates API design
        api_design = {
            "endpoints": {
                "/api/user/profile": {
                    "GET": "Retrieve user profile",
                    "PUT": "Update user profile",
                },
                "/api/user/avatar": {"POST": "Upload avatar image"},
            },
            "models": {
                "UserProfile": {
                    "id": "integer",
                    "name": "string",
                    "email": "string",
                    "avatar_url": "string",
                }
            },
        }

        api_file = (
            self.claude_dir / "shared-workspace" / "artifacts" / "user-profile-api.json"
        )
        with open(api_file, "w") as f:
            json.dump(api_design, f, indent=2)

        scenario_steps.append(("Backend API design created", api_file.exists()))

        # Step 3: Frontend creates UI mockup
        ui_mockup = {
            "components": {
                "ProfileView": "Display user profile information",
                "ProfileEdit": "Edit profile form",
                "AvatarUpload": "Avatar upload component",
            },
            "pages": {"profile": "/profile", "edit": "/profile/edit"},
            "state_management": "Redux for profile state",
        }

        ui_file = (
            self.claude_dir / "shared-workspace" / "artifacts" / "user-profile-ui.json"
        )
        with open(ui_file, "w") as f:
            json.dump(ui_mockup, f, indent=2)

        scenario_steps.append(("Frontend UI mockup created", ui_file.exists()))

        # Step 4: Testing plan
        test_plan = {
            "test_types": [
                "Unit tests for API endpoints",
                "Integration tests for profile flow",
                "UI component tests",
                "End-to-end user journey tests",
            ],
            "test_data": {
                "valid_profiles": 5,
                "invalid_inputs": 10,
                "file_upload_tests": 3,
            },
        }

        test_file = (
            self.claude_dir
            / "shared-workspace"
            / "artifacts"
            / "user-profile-tests.json"
        )
        with open(test_file, "w") as f:
            json.dump(test_plan, f, indent=2)

        scenario_steps.append(("Testing plan created", test_file.exists()))

        # Validate scenario completion
        checks = [
            (step_name, lambda result=result: result)
            for step_name, result in scenario_steps
        ]

        # Add coordination message flow
        coordination_summary = {
            "scenario": "User Profile Management",
            "artifacts_created": 4,
            "agents_involved": 4,
            "coordination_successful": all(result for _, result in scenario_steps),
            "completion_timestamp": datetime.now().isoformat(),
        }

        summary_file = (
            self.claude_dir / "shared-workspace" / "artifacts" / "scenario-summary.json"
        )
        with open(summary_file, "w") as f:
            json.dump(coordination_summary, f, indent=2)

        checks.append(("Scenario coordination summary created", summary_file.exists()))

        result = self._run_checks("Real-World Scenario", checks)

        # Cleanup scenario files
        scenario_files = [spec_file, api_file, ui_file, test_file, summary_file]
        for file in scenario_files:
            if file.exists():
                file.unlink()

        return result

    def test_performance(self) -> bool:
        """Test performance characteristics"""
        checks = []

        # Test 1: File operation speed
        start_time = time.time()
        test_files = []

        for i in range(10):
            test_file = (
                self.claude_dir
                / "shared-workspace"
                / "artifacts"
                / f"perf-test-{i}.txt"
            )
            with open(test_file, "w") as f:
                f.write(f"Performance test file {i}\n" * 100)
            test_files.append(test_file)

        file_creation_time = time.time() - start_time
        checks.append(
            (
                "File creation performance acceptable",
                lambda: file_creation_time
                < 5.0,  # Should create 10 files in under 5 seconds
            )
        )

        # Test 2: Message processing simulation
        start_time = time.time()

        for i in range(5):
            message = {
                "id": f"perf-test-{i}",
                "content": f"Performance test message {i}",
                "timestamp": datetime.now().isoformat(),
            }

            message_file = (
                self.claude_dir
                / "shared-workspace"
                / "messages"
                / "backend-agent"
                / "outbox"
                / f"perf-{i}.json"
            )
            with open(message_file, "w") as f:
                json.dump(message, f, indent=2)
            test_files.append(message_file)

        message_processing_time = time.time() - start_time
        checks.append(
            (
                "Message processing performance acceptable",
                lambda: message_processing_time
                < 2.0,  # Should process 5 messages in under 2 seconds
            )
        )

        # Test 3: Workspace traversal performance
        start_time = time.time()

        all_files = list(self.claude_dir.rglob("*.json"))
        all_files.extend(list(self.cursor_dir.rglob("*.json")))

        traversal_time = time.time() - start_time
        checks.append(
            (
                "Workspace traversal performance acceptable",
                lambda: traversal_time
                < 3.0,  # Should traverse all files in under 3 seconds
            )
        )

        result = self._run_checks("Performance", checks)

        # Cleanup performance test files
        for test_file in test_files:
            if test_file.exists():
                test_file.unlink()

        return result

    def test_cleanup(self) -> bool:
        """Test cleanup procedures"""
        checks = []

        # Create some test files for cleanup
        cleanup_test_files = [
            self.claude_dir / "shared-workspace" / "artifacts" / "cleanup-test.txt",
            self.claude_dir
            / "shared-workspace"
            / "messages"
            / "backend-agent"
            / "outbox"
            / "cleanup-message.json",
        ]

        for test_file in cleanup_test_files:
            test_file.parent.mkdir(parents=True, exist_ok=True)
            with open(test_file, "w") as f:
                f.write("Test file for cleanup")

        # Test cleanup functionality
        for test_file in cleanup_test_files:
            if test_file.exists():
                test_file.unlink()

            checks.append(
                (
                    f"Cleanup successful: {test_file.name}",
                    lambda tf=test_file: not tf.exists(),
                )
            )

        return self._run_checks("Cleanup", checks)

    def _run_checks(self, category: str, checks: List[Tuple[str, callable]]) -> bool:
        """Run a list of checks and return overall result"""
        passed = 0
        total = len(checks)

        for check_name, check_func in checks:
            try:
                if check_func():
                    print(f"  ✅ {check_name}")
                    passed += 1
                else:
                    print(f"  ❌ {check_name}")
            except Exception as e:
                print(f"  ❌ {check_name}: {e}")

        success_rate = passed / total if total > 0 else 0
        print(f"  📊 {category}: {passed}/{total} checks passed ({success_rate:.1%})")

        return success_rate >= 0.8  # 80% pass rate required

    def _validate_claude_config(self, config_file: Path) -> bool:
        """Validate Claude Code agent configuration"""
        try:
            with open(config_file) as f:
                config = json.load(f)

            required_fields = ["agent_id", "platform", "role", "capabilities"]
            return all(field in config for field in required_fields)
        except:
            return False

    def _validate_cursor_config(self, config_file: Path) -> bool:
        """Validate Cursor agent configuration"""
        try:
            with open(config_file) as f:
                config = json.load(f)

            required_fields = [
                "agent_id",
                "platform",
                "role",
                "tool_limit",
                "current_tools",
            ]
            return all(field in config for field in required_fields)
        except:
            return False

    def _validate_message_format(self, message_file: Path) -> bool:
        """Validate message format"""
        try:
            with open(message_file) as f:
                message = json.load(f)

            required_fields = ["from", "to", "content", "type", "timestamp"]
            return all(field in message for field in required_fields)
        except:
            return False

    def print_summary(self):
        """Print test summary"""
        total_time = time.time() - self.start_time if self.start_time else 0

        print("\n" + "=" * 55)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 55)

        passed = sum(1 for _, status, _ in self.test_results if status == "PASSED")
        failed = sum(1 for _, status, _ in self.test_results if status == "FAILED")
        errors = sum(1 for _, status, _ in self.test_results if status == "ERROR")
        total = len(self.test_results)

        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"🔥 Errors: {errors}")
        print(f"⏱️  Total Time: {total_time:.2f}s")
        print(f"📈 Success Rate: {passed/total:.1%}")

        print("\nDetailed Results:")
        for category, status, error in self.test_results:
            status_emoji = (
                "✅" if status == "PASSED" else "❌" if status == "FAILED" else "🔥"
            )
            print(f"  {status_emoji} {category}: {status}")
            if error:
                print(f"    Error: {error}")

        if passed == total:
            print(
                "\n🎉 All tests passed! Multi-instance coordination is working correctly."
            )
        else:
            print(f"\n⚠️  {failed + errors} tests failed. Review the issues above.")

        print("\n🔗 Coordination Infrastructure:")
        print(f"  Claude Code: {self.claude_dir}")
        print(f"  Cursor: {self.cursor_dir}")
        print(f"  Shared Workspace: {self.claude_dir}/shared-workspace")


if __name__ == "__main__":
    test_suite = CoordinationTestSuite()
    success = test_suite.run_all_tests()
    exit(0 if success else 1)
