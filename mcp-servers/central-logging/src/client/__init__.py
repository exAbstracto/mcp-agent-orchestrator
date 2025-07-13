"""
Client package for US-010: Centralized Logging System

Provides logging client functionality for other MCP servers.
"""

from .logging_client import (
    LoggingClient,
    LoggingConfig,
    CorrelationContext,
    create_logger,
    quick_log
)

__all__ = [
    "LoggingClient",
    "LoggingConfig", 
    "CorrelationContext",
    "create_logger",
    "quick_log"
]