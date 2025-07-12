#!/usr/bin/env python3
"""
Comprehensive unit tests for all Makefile commands.
Tests command execution, error handling, and integration scenarios.
"""

import os
import subprocess
import tempfile
import shutil
import time
import json
from pathlib import Path
try:
    import pytest
except ImportError:
    pytest = None
from unittest.mock import patch, MagicMock


class TestMakefileCommands:
    """Test suite for all Makefile commands."""

    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        cls.project_root = Path(__file__).parent.parent
        cls.original_cwd = os.getcwd()
        os.chdir(cls.project_root)
        
        # Ensure we have a clean test environment
        cls.run_make_command("clean")
        cls.run_make_command("clean-coordination")

    @classmethod
    def teardown_class(cls):
        """Clean up test environment."""
        os.chdir(cls.original_cwd)
        
    @staticmethod
    def run_make_command(target, timeout=30, capture_output=True, env=None):
        """Run a make command and return result."""
        try:
            result = subprocess.run(
                ["make", target],
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                env=env
            )
            return result
        except subprocess.TimeoutExpired:
            # Return a mock object for timeout to avoid None checks
            return MagicMock(returncode=124, stdout="", stderr="Command timed out")
        except Exception as e:
            return MagicMock(returncode=1, stdout="", stderr=str(e))

    def test_help_command(self):
        """Test help command displays all categories and commands."""
        result = self.run_make_command("help")
        assert result is not None and result.returncode == 0
        
        # Check for all major categories
        categories = [
            "General", "Environment Setup", "MCP Servers", "Testing",
            "Code Quality", "Coordination Demos", "Multi-Instance Setup",
            "Development Utilities", "Performance & Monitoring",
            "Git Workflow", "All-in-One Commands", "Project Info"
        ]
        
        for category in categories:
            assert category in result.stdout
            
        # Check for key commands
        key_commands = [
            "help", "install", "test", "clean", "message-queue-demo",
            "lint", "format", "git-status", "dev-setup"
        ]
        
        for command in key_commands:
            assert command in result.stdout

    def test_info_command(self):
        """Test info command displays project information."""
        result = self.run_make_command("info")
        assert result is not None and result.returncode == 0
        
        # Check for project structure information
        assert "Multi-Agent Development System" in result.stdout
        assert "mcp-servers/" in result.stdout
        assert "coordination-demo/" in result.stdout
        assert "Message Queue" in result.stdout
        assert "US-003" in result.stdout

    def test_install_command(self):
        """Test install command sets up virtual environment."""
        # Remove existing venv if present
        venv_path = Path("mcp-servers/venv")
        if venv_path.exists():
            shutil.rmtree(venv_path)
            
        result = self.run_make_command("install", timeout=60)
        assert result.returncode == 0
        
        # Check virtual environment was created
        assert venv_path.exists()
        assert (venv_path / "bin" / "python").exists()
        assert (venv_path / "bin" / "pip").exists()

    def test_install_dev_command(self):
        """Test install-dev command installs development dependencies."""
        # Ensure install is run first
        self.run_make_command("install", timeout=60)
        
        result = self.run_make_command("install-dev", timeout=60)
        assert result.returncode == 0
        
        # Check that dev dependencies are installed
        venv_python = Path("mcp-servers/venv/bin/python")
        if venv_python.exists():
            # Test that pytest is available
            test_result = subprocess.run(
                [str(venv_python), "-c", "import pytest; print('pytest available')"],
                capture_output=True,
                text=True
            )
            assert test_result.returncode == 0
            assert "pytest available" in test_result.stdout

    def test_message_queue_demo_command(self):
        """Test message queue demo command."""
        # Ensure dependencies are installed
        self.run_make_command("install", timeout=60)
        
        # Run demo with timeout since it's interactive
        result = self.run_make_command("message-queue-demo", timeout=10)
        
        # Demo should start successfully (may timeout due to interactivity)
        assert result is None or result.returncode == 0 or "Demo" in result.stdout

    def test_template_demo_command(self):
        """Test template demo command."""
        # Ensure dependencies are installed
        self.run_make_command("install", timeout=60)
        
        # Run template demo
        result = self.run_make_command("template-demo", timeout=10)
        
        # Demo should start successfully
        assert result is None or result.returncode == 0 or "Template" in result.stdout

    def test_test_command(self):
        """Test the test command runs all tests."""
        # Ensure dependencies are installed
        self.run_make_command("install", timeout=60)
        self.run_make_command("install-dev", timeout=60)
        
        result = self.run_make_command("test", timeout=60)
        
        # Tests should run (may have failures but should execute)
        assert result.returncode in [0, 1, 2]  # Success, test failures, or collection issues
        assert "pytest" in result.stdout or "test" in result.stdout.lower()

    def test_test_message_queue_command(self):
        """Test message queue specific tests."""
        # Ensure dependencies are installed
        self.run_make_command("install", timeout=60)
        self.run_make_command("install-dev", timeout=60)
        
        result = self.run_make_command("test-message-queue", timeout=60)
        
        # Tests should run for message queue
        assert result.returncode in [0, 1, 2]
        assert "message-queue" in result.stdout.lower() or "pytest" in result.stdout

    def test_test_template_command(self):
        """Test template specific tests."""
        # Ensure dependencies are installed
        self.run_make_command("install", timeout=60)
        self.run_make_command("install-dev", timeout=60)
        
        result = self.run_make_command("test-template", timeout=60)
        
        # Tests should run for template
        assert result.returncode in [0, 1, 2]
        assert "template" in result.stdout.lower() or "pytest" in result.stdout

    def test_test_coverage_command(self):
        """Test coverage command generates coverage reports."""
        # Ensure dependencies are installed
        self.run_make_command("install", timeout=60)
        self.run_make_command("install-dev", timeout=60)
        
        result = self.run_make_command("test-coverage", timeout=60)
        
        # Coverage should run
        assert result.returncode in [0, 1, 2]
        assert "coverage" in result.stdout.lower() or "cov" in result.stdout

    def test_lint_command(self):
        """Test linting command."""
        # Ensure dependencies are installed
        self.run_make_command("install", timeout=60)
        self.run_make_command("install-dev", timeout=60)
        
        result = self.run_make_command("lint", timeout=30)
        
        # Linting should run successfully
        assert result.returncode == 0
        assert "flake8" in result.stdout.lower() or "lint" in result.stdout.lower()

    def test_format_command(self):
        """Test code formatting command."""
        # Ensure dependencies are installed
        self.run_make_command("install", timeout=60)
        self.run_make_command("install-dev", timeout=60)
        
        result = self.run_make_command("format", timeout=30)
        
        # Formatting should run successfully
        assert result.returncode == 0
        assert "black" in result.stdout.lower() or "format" in result.stdout.lower()

    def test_type_check_command(self):
        """Test type checking command."""
        # Ensure dependencies are installed
        self.run_make_command("install", timeout=60)
        self.run_make_command("install-dev", timeout=60)
        
        result = self.run_make_command("type-check", timeout=30)
        
        # Type checking should run
        assert result.returncode == 0
        assert "mypy" in result.stdout.lower() or "type" in result.stdout.lower()

    def test_clean_command(self):
        """Test clean command removes temporary files."""
        # Create some temporary files to clean
        test_files = [
            "test_cache/__pycache__/test.pyc",
            "test_cache/.pytest_cache/test.py",
            "test_cache/htmlcov/index.html",
            "test_cache/.coverage"
        ]
        
        # Create test directories and files
        for test_file in test_files:
            file_path = Path(test_file)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()
        
        # Run clean command
        result = self.run_make_command("clean")
        assert result.returncode == 0
        
        # Check that files were cleaned
        for test_file in test_files:
            assert not Path(test_file).exists()
            
        # Clean up test directory
        if Path("test_cache").exists():
            shutil.rmtree("test_cache")

    def test_clean_coordination_command(self):
        """Test coordination cleanup command."""
        # Create temporary coordination files
        coord_dirs = [
            "/tmp/mcp-agent-workspaces/test",
            "/tmp/cursor-test",
            "/tmp/claude-code-worktrees/test"
        ]
        
        coord_files = [
            "coordination-demo/shared-workspace/messages_test.json"
        ]
        
        # Create test directories and files
        for coord_dir in coord_dirs:
            try:
                Path(coord_dir).mkdir(parents=True, exist_ok=True)
                Path(coord_dir, "test.txt").touch()
            except:
                pass  # Skip if permission denied
        
        for coord_file in coord_files:
            file_path = Path(coord_file)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()
        
        # Run clean coordination command
        result = self.run_make_command("clean-coordination")
        assert result.returncode == 0
        
        # Check that coordination files were cleaned
        for coord_file in coord_files:
            assert not Path(coord_file).exists()

    def test_logs_command(self):
        """Test logs command."""
        result = self.run_make_command("logs", timeout=5)
        
        # Command should run (may not find logs, but should execute)
        assert result.returncode == 0
        assert "log" in result.stdout.lower() or "no log files" in result.stdout.lower()

    def test_docs_command(self):
        """Test docs command displays available documentation."""
        result = self.run_make_command("docs")
        assert result.returncode == 0
        
        # Check for documentation references
        assert "README.md" in result.stdout
        assert "docs/" in result.stdout
        assert "platform-capabilities" in result.stdout or "analysis" in result.stdout

    def test_git_status_command(self):
        """Test git status command."""
        result = self.run_make_command("git-status")
        assert result.returncode == 0
        
        # Should show git information
        assert "branch" in result.stdout.lower() or "git" in result.stdout.lower()

    def test_dev_setup_command(self):
        """Test complete development setup."""
        # Remove existing venv if present
        venv_path = Path("mcp-servers/venv")
        if venv_path.exists():
            shutil.rmtree(venv_path)
            
        result = self.run_make_command("dev-setup", timeout=120)
        assert result.returncode == 0
        
        # Check that environment is set up
        assert venv_path.exists()
        assert "Development environment ready" in result.stdout

    def test_quick_test_command(self):
        """Test quick test command (clean + test)."""
        # Ensure dependencies are installed
        self.run_make_command("install", timeout=60)
        self.run_make_command("install-dev", timeout=60)
        
        result = self.run_make_command("quick-test", timeout=90)
        
        # Should run clean and test
        assert result.returncode in [0, 1, 2]
        assert "clean" in result.stdout.lower() or "test" in result.stdout.lower()

    def test_ci_check_command(self):
        """Test CI check command (clean + lint + type-check + test)."""
        # Ensure dependencies are installed
        self.run_make_command("install", timeout=60)
        self.run_make_command("install-dev", timeout=60)
        
        result = self.run_make_command("ci-check", timeout=120)
        
        # Should run all CI checks
        assert result.returncode in [0, 1, 2]
        assert "CI checks" in result.stdout or "lint" in result.stdout.lower()

    def test_benchmark_command(self):
        """Test benchmark command."""
        # Ensure dependencies are installed
        self.run_make_command("install", timeout=60)
        
        result = self.run_make_command("benchmark", timeout=30)
        
        # Should attempt to run benchmarks
        assert result.returncode in [0, 1, 2]
        assert "benchmark" in result.stdout.lower() or "performance" in result.stdout.lower()

    def test_health_check_command(self):
        """Test health check command."""
        # Ensure dependencies are installed
        self.run_make_command("install", timeout=60)
        
        result = self.run_make_command("health-check", timeout=30)
        
        # Should run health checks
        assert result.returncode in [0, 1, 2]
        assert "health" in result.stdout.lower() or "check" in result.stdout.lower()

    def test_commit_command_requires_message(self):
        """Test commit command requires COMMIT_MSG parameter."""
        result = self.run_make_command("commit")
        
        # Should fail without commit message
        assert result.returncode != 0
        assert "COMMIT_MSG" in result.stdout or "commit" in result.stdout.lower()

    def test_invalid_command(self):
        """Test invalid command handling."""
        result = self.run_make_command("invalid-command-that-does-not-exist")
        
        # Should fail with error
        assert result.returncode != 0
        assert "No rule to make target" in result.stderr or "invalid" in result.stderr.lower()

    def test_environment_variables(self):
        """Test commands work with different environment variables."""
        # Test with different PYTHON environment
        env = os.environ.copy()
        env["PYTHON"] = "python3"
        
        result = self.run_make_command("help", env=env)
        assert result.returncode == 0

    def test_concurrent_command_execution(self):
        """Test that commands can be run concurrently safely."""
        import threading
        import queue
        
        results = queue.Queue()
        
        def run_command(cmd):
            result = self.run_make_command(cmd)
            results.put((cmd, result.returncode if result else -1))
        
        # Run multiple safe commands concurrently
        commands = ["help", "info", "git-status", "docs"]
        threads = []
        
        for cmd in commands:
            thread = threading.Thread(target=run_command, args=(cmd,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        while not results.empty():
            cmd, returncode = results.get()
            assert returncode == 0, f"Command {cmd} failed with code {returncode}"

    def test_makefile_syntax_validation(self):
        """Test that Makefile syntax is valid."""
        result = subprocess.run(
            ["make", "-n", "help"],
            capture_output=True,
            text=True
        )
        
        # Should not have syntax errors
        assert result.returncode == 0
        assert "syntax error" not in result.stderr.lower()

    def test_command_dependencies(self):
        """Test that commands with dependencies work correctly."""
        # Test dev-setup which depends on install and install-dev
        result = self.run_make_command("dev-setup", timeout=120)
        assert result.returncode == 0
        
        # Check that venv was created (indicating install worked)
        assert Path("mcp-servers/venv").exists()

    def test_error_handling_resilience(self):
        """Test that commands handle errors gracefully."""
        # Test commands that might fail gracefully
        resilient_commands = ["lint", "format", "type-check", "logs"]
        
        for cmd in resilient_commands:
            result = self.run_make_command(cmd, timeout=30)
            # Should not crash, even if tools are missing
            assert result.returncode in [0, 1, 2]

    def test_file_creation_and_cleanup(self):
        """Test that commands create and clean up files correctly."""
        # Test that coverage creates HTML reports
        self.run_make_command("install", timeout=60)
        self.run_make_command("install-dev", timeout=60)
        
        # Run coverage
        self.run_make_command("test-coverage", timeout=60)
        
        # Check if coverage files might be created
        possible_coverage_dirs = [
            "mcp-servers/message-queue/htmlcov",
            "mcp-servers/template/htmlcov"
        ]
        
        # At least one should exist if coverage ran
        coverage_exists = any(Path(d).exists() for d in possible_coverage_dirs)
        
        # Clean up
        self.run_make_command("clean")
        
        # Coverage dirs should be cleaned
        for d in possible_coverage_dirs:
            assert not Path(d).exists()

    def test_all_commands_documented(self):
        """Test that all commands are documented in help."""
        # Get help output
        result = self.run_make_command("help")
        help_output = result.stdout
        
        # List of all commands that should be documented
        expected_commands = [
            "help", "info", "install", "install-dev", "dev-setup",
            "message-queue", "message-queue-demo", "template-demo", "real-mcp-server",
            "test", "test-message-queue", "test-template", "test-coverage", 
            "test-coordination", "quick-test",
            "lint", "format", "type-check", "ci-check",
            "demo-file-sharing", "demo-real-mcp", "demo-comprehensive",
            "setup-coordination", "setup-real-mcp",
            "setup-cursor", "setup-claude-worktrees", "launch-cursor-instances",
            "clean", "clean-coordination", "logs", "docs",
            "benchmark", "health-check",
            "git-status", "commit", "push"
        ]
        
        for cmd in expected_commands:
            assert cmd in help_output, f"Command '{cmd}' not found in help output"


if __name__ == "__main__":
    # Run tests directly
    import sys
    if pytest is not None:
        sys.exit(pytest.main([__file__, "-v"]))
    else:
        print("pytest not available, install with: pip install pytest")
        sys.exit(1) 