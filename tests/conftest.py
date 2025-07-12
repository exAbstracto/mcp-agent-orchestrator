"""
pytest configuration for Makefile command tests.
"""

import pytest
import os
from pathlib import Path


@pytest.fixture(scope="session", autouse=True)
def project_setup():
    """Ensure we're running tests from the correct directory."""
    original_cwd = os.getcwd()
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    yield
    
    os.chdir(original_cwd)


@pytest.fixture(scope="function")
def clean_environment():
    """Clean up test environment before each test."""
    # Clean up any test artifacts
    yield
    # Post-test cleanup if needed


def pytest_configure(config):
    """Configure pytest for this test suite."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    ) 