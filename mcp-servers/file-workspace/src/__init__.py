"""File Workspace MCP Server Package"""

__version__ = "1.0.0"

# Only import MCP server if mcp module is available
try:
    from .file_workspace_server import FileWorkspaceServer
    __all__ = ["FileWorkspaceServer"]
except ImportError:
    # MCP not available, only core models and services
    __all__ = []