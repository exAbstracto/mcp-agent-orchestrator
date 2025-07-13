"""
Central Logging MCP Server for US-010: Centralized Logging System

MCP server providing centralized logging capabilities for all agents.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from mcp.server import Server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource
)

from src.services.logging_service import LoggingService
from src.services.search_service import SearchService
from src.services.retention_service import RetentionService
from src.models.log_entry import LogEntry, LogLevel
from src.models.search_criteria import SearchCriteria, TimeRange


class CentralLoggingServer:
    """MCP Server for centralized logging functionality"""
    
    def __init__(self, name: str = "central-logging", version: str = "1.0.0"):
        """Initialize the central logging server"""
        self.name = name
        self.version = version
        self.server = Server(name)
        self.logging_service = LoggingService()
        self.search_service = SearchService(self.logging_service)
        self.retention_service = RetentionService(self.logging_service)
        
        # Setup standard logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Register tools
        self._register_tools()
        
        self.logger.info(f"CentralLoggingServer {version} initialized")
    
    def send_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send log directly (for testing)"""
        try:
            log_entry = LogEntry.create(
                level=LogLevel(log_data["level"]),
                message=log_data["message"],
                component=log_data["component"],
                correlation_id=log_data["correlation_id"],
                metadata=log_data.get("metadata", {})
            )
            return self.logging_service.add_log_entry(log_entry)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_logs_by_correlation_id(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get logs by correlation ID (for testing)"""
        try:
            correlation_id = args["correlation_id"]
            logs = self.logging_service.get_logs_by_correlation_id(correlation_id)
            return {"success": True, "logs": [log.to_dict() for log in logs]}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def set_log_level(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Set log level (for testing)"""
        try:
            level = LogLevel(args["level"])
            component = args.get("component")
            if component:
                return self.logging_service.set_component_log_level(component, level)
            else:
                return self.logging_service.set_global_log_level(level)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_log_stats(self, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get log statistics (for testing)"""
        try:
            return self.logging_service.get_log_stats()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def search_logs(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search logs (for testing)"""
        try:
            # Build search criteria from args
            from src.models.search_criteria import SearchCriteria, TimeRange
            
            criteria = SearchCriteria()
            if "component" in args:
                criteria.component = args["component"]
            if "level" in args:
                criteria.level = LogLevel(args["level"])
            if "correlation_id" in args:
                criteria.correlation_id = args["correlation_id"]
            if "message_contains" in args:
                criteria.message_contains = args["message_contains"]
            
            # Handle time range
            if "start_time" in args and "end_time" in args:
                from datetime import datetime
                start = datetime.fromisoformat(args["start_time"])
                end = datetime.fromisoformat(args["end_time"])
                criteria.time_range = TimeRange(start=start, end=end)
            
            logs = self.search_service.search_logs(criteria)
            return {"success": True, "logs": [log.to_dict() for log in logs]}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _register_tools(self):
        """Register all MCP tools"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available central logging tools"""
            return [
                Tool(
                    name="log_message",
                    description="Log a message to the central logging system",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "level": {
                                "type": "string",
                                "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                                "description": "Log level"
                            },
                            "message": {
                                "type": "string",
                                "description": "Log message content"
                            },
                            "component": {
                                "type": "string",
                                "description": "Component or service name"
                            },
                            "correlation_id": {
                                "type": "string",
                                "description": "Correlation ID for tracking requests"
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional metadata (optional)",
                                "additionalProperties": True
                            }
                        },
                        "required": ["level", "message", "component", "correlation_id"]
                    }
                ),
                Tool(
                    name="search_logs",
                    description="Search logs with various criteria",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "component": {
                                "type": "string",
                                "description": "Filter by component name"
                            },
                            "level": {
                                "type": "string",
                                "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                                "description": "Filter by log level"
                            },
                            "correlation_id": {
                                "type": "string",
                                "description": "Filter by correlation ID"
                            },
                            "message_contains": {
                                "type": "string",
                                "description": "Search for text in log messages"
                            },
                            "start_time": {
                                "type": "string",
                                "format": "date-time",
                                "description": "Start of time range (ISO format)"
                            },
                            "end_time": {
                                "type": "string",
                                "format": "date-time",
                                "description": "End of time range (ISO format)"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_component_logs",
                    description="Get all logs from a specific component",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "component": {
                                "type": "string",
                                "description": "Component name to get logs for"
                            }
                        },
                        "required": ["component"]
                    }
                ),
                Tool(
                    name="trace_correlation",
                    description="Trace request flow by correlation ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "correlation_id": {
                                "type": "string",
                                "description": "Correlation ID to trace"
                            }
                        },
                        "required": ["correlation_id"]
                    }
                ),
                Tool(
                    name="get_recent_logs",
                    description="Get recent logs within specified hours",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "hours": {
                                "type": "number",
                                "description": "Number of hours to look back (default: 24)"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_error_logs",
                    description="Get ERROR and CRITICAL level logs",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "component": {
                                "type": "string",
                                "description": "Optional component filter"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_log_stats",
                    description="Get statistics about stored logs",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_component_activity",
                    description="Get activity summary by component",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="set_log_level",
                    description="Set log level for a component or globally",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "level": {
                                "type": "string",
                                "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                                "description": "Log level to set"
                            },
                            "component": {
                                "type": "string",
                                "description": "Component name (if not set, applies globally)"
                            }
                        },
                        "required": ["level"]
                    }
                ),
                Tool(
                    name="get_retention_policy",
                    description="Get current log retention policy",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="set_retention_policy",
                    description="Set log retention policy (minimum 7 days)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days": {
                                "type": "number",
                                "minimum": 7,
                                "description": "Number of days to retain logs (minimum 7)"
                            }
                        },
                        "required": ["days"]
                    }
                ),
                Tool(
                    name="cleanup_expired_logs",
                    description="Manually trigger cleanup of expired logs",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="preview_cleanup",
                    description="Preview what logs would be cleaned up",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            
            try:
                if name == "log_message":
                    return await self._log_message(arguments)
                elif name == "search_logs":
                    return await self._search_logs(arguments)
                elif name == "get_component_logs":
                    return await self._get_component_logs(arguments)
                elif name == "trace_correlation":
                    return await self._trace_correlation(arguments)
                elif name == "get_recent_logs":
                    return await self._get_recent_logs(arguments)
                elif name == "get_error_logs":
                    return await self._get_error_logs(arguments)
                elif name == "get_log_stats":
                    return await self._get_log_stats(arguments)
                elif name == "get_component_activity":
                    return await self._get_component_activity(arguments)
                elif name == "set_log_level":
                    return await self._set_log_level(arguments)
                elif name == "get_retention_policy":
                    return await self._get_retention_policy(arguments)
                elif name == "set_retention_policy":
                    return await self._set_retention_policy(arguments)
                elif name == "cleanup_expired_logs":
                    return await self._cleanup_expired_logs(arguments)
                elif name == "preview_cleanup":
                    return await self._preview_cleanup(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
                    
            except Exception as e:
                self.logger.error(f"Error in tool {name}: {str(e)}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _log_message(self, args: Dict[str, Any]) -> List[TextContent]:
        """Add a log entry to the central store"""
        try:
            level = LogLevel(args["level"])
            log_entry = LogEntry.create(
                level=level,
                message=args["message"],
                component=args["component"],
                correlation_id=args["correlation_id"],
                metadata=args.get("metadata", {})
            )
            
            result = self.logging_service.add_log_entry(log_entry)
            return [TextContent(type="text", text=f"Log entry added: {result}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error adding log: {str(e)}")]
    
    async def _search_logs(self, args: Dict[str, Any]) -> List[TextContent]:
        """Search logs with criteria"""
        try:
            # Build search criteria
            criteria = SearchCriteria()
            
            if "component" in args:
                criteria.component = args["component"]
            if "level" in args:
                criteria.level = LogLevel(args["level"])
            if "correlation_id" in args:
                criteria.correlation_id = args["correlation_id"]
            if "message_contains" in args:
                criteria.message_contains = args["message_contains"]
            
            # Handle time range
            if "start_time" in args and "end_time" in args:
                start = datetime.fromisoformat(args["start_time"])
                end = datetime.fromisoformat(args["end_time"])
                criteria.time_range = TimeRange(start=start, end=end)
            
            logs = self.search_service.search_logs(criteria)
            log_dicts = [log.to_dict() for log in logs]
            
            return [TextContent(type="text", text=f"Found {len(logs)} matching logs: {log_dicts}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error searching logs: {str(e)}")]
    
    async def _get_component_logs(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get logs from a specific component"""
        try:
            component = args["component"]
            logs = self.search_service.search_by_component(component)
            log_dicts = [log.to_dict() for log in logs]
            
            return [TextContent(type="text", text=f"Component '{component}' logs: {log_dicts}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting component logs: {str(e)}")]
    
    async def _trace_correlation(self, args: Dict[str, Any]) -> List[TextContent]:
        """Trace request flow by correlation ID"""
        try:
            correlation_id = args["correlation_id"]
            trace_info = self.search_service.trace_correlation_flow(correlation_id)
            
            return [TextContent(type="text", text=f"Correlation trace: {trace_info}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error tracing correlation: {str(e)}")]
    
    async def _get_recent_logs(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get recent logs"""
        try:
            hours = args.get("hours", 24)
            logs = self.search_service.search_recent_logs(hours)
            log_dicts = [log.to_dict() for log in logs]
            
            return [TextContent(type="text", text=f"Recent logs ({hours}h): {log_dicts}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting recent logs: {str(e)}")]
    
    async def _get_error_logs(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get error and critical logs"""
        try:
            component = args.get("component")
            logs = self.search_service.search_errors_and_above(component)
            log_dicts = [log.to_dict() for log in logs]
            
            return [TextContent(type="text", text=f"Error logs: {log_dicts}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting error logs: {str(e)}")]
    
    async def _get_log_stats(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get log statistics"""
        try:
            stats = self.logging_service.get_log_stats()
            return [TextContent(type="text", text=f"Log statistics: {stats}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting stats: {str(e)}")]
    
    async def _get_component_activity(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get component activity summary"""
        try:
            activity = self.search_service.get_component_activity_summary()
            return [TextContent(type="text", text=f"Component activity: {activity}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting activity: {str(e)}")]
    
    async def _set_log_level(self, args: Dict[str, Any]) -> List[TextContent]:
        """Set log level"""
        try:
            level = LogLevel(args["level"])
            component = args.get("component")
            
            if component:
                result = self.logging_service.set_component_log_level(component, level)
            else:
                result = self.logging_service.set_global_log_level(level)
            
            return [TextContent(type="text", text=f"Log level set: {result}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error setting log level: {str(e)}")]
    
    async def _get_retention_policy(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get retention policy"""
        try:
            policy = self.retention_service.get_retention_policy()
            return [TextContent(type="text", text=f"Retention policy: {policy}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting retention policy: {str(e)}")]
    
    async def _set_retention_policy(self, args: Dict[str, Any]) -> List[TextContent]:
        """Set retention policy"""
        try:
            days = args["days"]
            result = self.retention_service.set_retention_policy(days)
            return [TextContent(type="text", text=f"Retention policy updated: {result}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error setting retention policy: {str(e)}")]
    
    async def _cleanup_expired_logs(self, args: Dict[str, Any]) -> List[TextContent]:
        """Cleanup expired logs"""
        try:
            result = self.retention_service.cleanup_expired_logs()
            return [TextContent(type="text", text=f"Cleanup completed: {result}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error during cleanup: {str(e)}")]
    
    async def _preview_cleanup(self, args: Dict[str, Any]) -> List[TextContent]:
        """Preview cleanup"""
        try:
            preview = self.retention_service.get_cleanup_preview()
            return [TextContent(type="text", text=f"Cleanup preview: {preview}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting cleanup preview: {str(e)}")]


async def main():
    """Main entry point for the central logging server"""
    server_instance = CentralLoggingServer()
    
    async with server_instance.server:
        await server_instance.server.run()


if __name__ == "__main__":
    asyncio.run(main())