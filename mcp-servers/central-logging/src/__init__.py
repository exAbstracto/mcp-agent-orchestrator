"""Central Logging MCP Server Package"""

__version__ = "1.0.0"

# Only import MCP server if mcp module is available
try:
    from .central_logging_server import CentralLoggingServer
    __all__ = ["CentralLoggingServer"]
except ImportError:
    # MCP not available, only core models and services
    __all__ = []