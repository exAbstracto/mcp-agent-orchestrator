#!/usr/bin/env python3
"""
Simple test runner for Makefile command tests.
Can be run without pytest installed.
"""

import sys
import os
from pathlib import Path


def main():
    """Run Makefile tests using unittest if pytest is not available."""
    # Add the project root to the path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # Change to project root
    os.chdir(project_root)
    
    try:
        # Try to use pytest first
        import pytest
        print("Running tests with pytest...")
        exit_code = pytest.main([
            "tests/test_makefile_commands.py",
            "-v",
            "--tb=short",
            "--disable-warnings"
        ])
        sys.exit(exit_code)
    except ImportError:
        print("pytest not available, running basic tests...")
        
        # Import test class
        from tests.test_makefile_commands import TestMakefileCommands
        
        # Create test instance
        test_instance = TestMakefileCommands()
        
        # Set up test environment
        test_instance.setup_class()
        
        # List of test methods to run
        test_methods = [
            "test_help_command",
            "test_info_command", 
            "test_clean_command",
            "test_docs_command",
            "test_git_status_command",
            "test_makefile_syntax_validation",
            "test_invalid_command",
            "test_all_commands_documented"
        ]
        
        passed = 0
        failed = 0
        
        print(f"Running {len(test_methods)} basic tests...")
        
        for method_name in test_methods:
            try:
                print(f"  {method_name}...", end=" ")
                method = getattr(test_instance, method_name)
                method()
                print("PASSED")
                passed += 1
            except Exception as e:
                print(f"FAILED: {e}")
                failed += 1
        
        # Clean up
        test_instance.teardown_class()
        
        print(f"\nResults: {passed} passed, {failed} failed")
        
        if failed > 0:
            sys.exit(1)
        else:
            print("All basic tests passed!")
            sys.exit(0)


if __name__ == "__main__":
    main() 