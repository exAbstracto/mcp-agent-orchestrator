"""
File Workspace Server for US-009: Shared Workspace File Locking

MCP server that provides file locking capabilities for multi-agent development environments.
"""

import json
import logging
from typing import Any, Dict, List

from mcp.server import Server
from mcp.types import Tool, TextContent

from src.services.locking_service import LockingService
from src.services.cleanup_service import CleanupService


class FileWorkspaceServer:
    """MCP server for file workspace management using official MCP SDK"""
    
    def __init__(self, name: str, version: str):
        """Initialize the file workspace server"""
        self.name = name
        self.version = version
        self.server = Server(name)
        
        # Initialize services
        self.locking_service = LockingService()
        self.cleanup_service = CleanupService(self.locking_service)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self) -> None:
        """Register MCP tools for file locking"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available file locking tools"""
            return [
                Tool(
                    name="acquire_file_lock",
                    description="Acquire a file lock for exclusive access",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to the file to lock"},
                            "agent_id": {"type": "string", "description": "Unique identifier for the agent"},
                            "timeout_seconds": {"type": "integer", "default": 300, "description": "Lock timeout in seconds"}
                        },
                        "required": ["file_path", "agent_id"]
                    }
                ),
                Tool(
                    name="release_file_lock",
                    description="Release an existing file lock",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to the file to unlock"},
                            "agent_id": {"type": "string", "description": "Unique identifier for the agent"}
                        },
                        "required": ["file_path", "agent_id"]
                    }
                ),
                Tool(
                    name="get_file_lock_status",
                    description="Get the current lock status of a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to the file to check"}
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="list_all_locks",
                    description="List all active locks in the system",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="queue_lock_request",
                    description="Queue a lock request for a currently locked file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to the file to lock"},
                            "agent_id": {"type": "string", "description": "Unique identifier for the agent"},
                            "timeout_seconds": {"type": "integer", "default": 300, "description": "Desired lock timeout in seconds"}
                        },
                        "required": ["file_path", "agent_id"]
                    }
                ),
                Tool(
                    name="cancel_queued_request",
                    description="Cancel a queued lock request",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to the file"},
                            "agent_id": {"type": "string", "description": "Unique identifier for the agent"}
                        },
                        "required": ["file_path", "agent_id"]
                    }
                ),
                Tool(
                    name="get_queue_status",
                    description="Get the queue status for a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to the file"}
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="list_locks_by_agent",
                    description="List all locks held by a specific agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {"type": "string", "description": "Unique identifier for the agent"}
                        },
                        "required": ["agent_id"]
                    }
                ),
                Tool(
                    name="force_release_lock",
                    description="Forcibly release a lock (admin function)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to the file to unlock"},
                            "admin_reason": {"type": "string", "default": "Admin action", "description": "Reason for forced release"}
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="get_cleanup_stats",
                    description="Get statistics about locks and cleanup status",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="cleanup_expired_locks",
                    description="Manually trigger cleanup of expired locks",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                if name == "acquire_file_lock":
                    result = self.acquire_file_lock(arguments)
                elif name == "release_file_lock":
                    result = self.release_file_lock(arguments)
                elif name == "get_file_lock_status":
                    result = self.get_file_lock_status(arguments)
                elif name == "list_all_locks":
                    result = self.list_all_locks(arguments)
                elif name == "queue_lock_request":
                    result = self.queue_lock_request(arguments)
                elif name == "cancel_queued_request":
                    result = self.cancel_queued_request(arguments)
                elif name == "get_queue_status":
                    result = self.get_queue_status(arguments)
                elif name == "list_locks_by_agent":
                    result = self.list_locks_by_agent(arguments)
                elif name == "force_release_lock":
                    result = self.force_release_lock(arguments)
                elif name == "get_cleanup_stats":
                    result = self.get_cleanup_stats(arguments)
                elif name == "cleanup_expired_locks":
                    result = self.cleanup_expired_locks(arguments)
                else:
                    result = {"error": f"Unknown tool: {name}"}
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            except Exception as e:
                self.logger.error(f"Error in tool {name}: {str(e)}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    def acquire_file_lock(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Acquire a file lock using the locking service"""
        try:
            return self.locking_service.acquire_lock(
                file_path=arguments["file_path"],
                agent_id=arguments["agent_id"],
                timeout_seconds=arguments.get("timeout_seconds")
            )
        except Exception as e:
            return {"error": str(e)}
    
    def release_file_lock(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Release a file lock using the locking service"""
        try:
            return self.locking_service.release_lock(
                file_path=arguments["file_path"],
                agent_id=arguments["agent_id"]
            )
        except Exception as e:
            return {"error": str(e)}
    
    def get_file_lock_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get file lock status using the locking service"""
        try:
            return self.locking_service.get_lock_status(
                file_path=arguments["file_path"]
            )
        except Exception as e:
            return {"error": str(e)}
    
    def list_all_locks(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List all active locks using the locking service"""
        try:
            locks = self.locking_service.list_all_locks()
            return {"locks": locks}
        except Exception as e:
            return {"error": str(e)}
    
    def queue_lock_request(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Queue a lock request using the locking service"""
        try:
            return self.locking_service.queue_lock_request(
                file_path=arguments["file_path"],
                agent_id=arguments["agent_id"],
                timeout_seconds=arguments.get("timeout_seconds", 300)
            )
        except Exception as e:
            return {"error": str(e)}
    
    def cancel_queued_request(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel a queued lock request using the locking service"""
        try:
            return self.locking_service.cancel_queued_request(
                file_path=arguments["file_path"],
                agent_id=arguments["agent_id"]
            )
        except Exception as e:
            return {"error": str(e)}
    
    def get_queue_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get queue status using the locking service"""
        try:
            return self.locking_service.get_queue_status(
                file_path=arguments["file_path"]
            )
        except Exception as e:
            return {"error": str(e)}
    
    def list_locks_by_agent(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List locks by agent using the locking service"""
        try:
            locks = self.locking_service.list_locks_by_agent(
                agent_id=arguments["agent_id"]
            )
            return {"locks": locks}
        except Exception as e:
            return {"error": str(e)}
    
    def force_release_lock(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Force release a lock using the locking service"""
        try:
            return self.locking_service.force_release_lock(
                file_path=arguments["file_path"],
                admin_reason=arguments.get("admin_reason", "Admin action")
            )
        except Exception as e:
            return {"error": str(e)}
    
    def get_cleanup_stats(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get cleanup statistics using the cleanup service"""
        try:
            return self.cleanup_service.get_cleanup_stats()
        except Exception as e:
            return {"error": str(e)}
    
    def cleanup_expired_locks(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Manually trigger cleanup using the cleanup service"""
        try:
            return self.cleanup_service.cleanup_expired_locks()
        except Exception as e:
            return {"error": str(e)}
    
    async def run(self) -> None:
        """Run the file workspace server"""
        self.logger.info(f"Starting {self.name} v{self.version}")
        await self.server.run()


# Factory function for consistency
def create_file_workspace_server(name: str = "file-workspace", version: str = "1.0.0") -> FileWorkspaceServer:
    """Factory function to create file workspace server"""
    return FileWorkspaceServer(name, version)