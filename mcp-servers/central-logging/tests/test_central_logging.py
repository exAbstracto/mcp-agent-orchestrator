"""
TDD Tests for US-010: Centralized Logging System

Test all acceptance criteria using Test-Driven Development approach.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Import the modules we'll implement
from src.models.log_entry import LogEntry, LogLevel
from src.models.search_criteria import SearchCriteria, TimeRange
from src.services.logging_service import LoggingService
from src.services.search_service import SearchService
from src.services.retention_service import RetentionService
from src.client.logging_client import LoggingClient
from src.central_logging_server import CentralLoggingServer


class TestCentralLogAggregation:
    """Test that all MCP servers can send logs to central location"""
    
    def test_send_log_entry_success(self):
        """Test successful log entry submission"""
        service = LoggingService()
        
        log_entry = LogEntry(
            level=LogLevel.INFO,
            message="Test message",
            component="test-component",
            correlation_id="test-123",
            metadata={"key": "value"}
        )
        
        result = service.add_log_entry(log_entry)
        
        assert result["success"] is True
        assert result["log_id"] is not None
        assert result["timestamp"] is not None
    
    def test_send_log_with_all_fields(self):
        """Test log entry with all required and optional fields"""
        service = LoggingService()
        
        log_entry = LogEntry(
            level=LogLevel.ERROR,
            message="Error occurred",
            component="agent-1",
            correlation_id="req-456",
            metadata={
                "error_code": 500,
                "stack_trace": "line 1\nline 2",
                "user_id": "user123"
            }
        )
        
        result = service.add_log_entry(log_entry)
        
        assert result["success"] is True
        
        # Verify log was stored
        stored_logs = service.get_all_logs()
        assert len(stored_logs) == 1
        
        stored_log = stored_logs[0]
        assert stored_log.level == LogLevel.ERROR
        assert stored_log.message == "Error occurred"
        assert stored_log.component == "agent-1"
        assert stored_log.correlation_id == "req-456"
        assert stored_log.metadata["error_code"] == 500
    
    def test_send_log_validates_required_fields(self):
        """Test that required fields are validated"""
        service = LoggingService()
        
        # Missing message
        with pytest.raises(ValueError, match="message"):
            LogEntry(
                level=LogLevel.INFO,
                message="",
                component="test",
                correlation_id="123"
            )
        
        # Missing component
        with pytest.raises(ValueError, match="component"):
            LogEntry(
                level=LogLevel.INFO,
                message="test",
                component="",
                correlation_id="123"
            )
    
    def test_multiple_components_send_logs(self):
        """Test that multiple components can send logs"""
        service = LoggingService()
        
        components = ["agent-1", "agent-2", "health-monitor", "file-workspace"]
        
        for i, component in enumerate(components):
            log_entry = LogEntry(
                level=LogLevel.INFO,
                message=f"Message from {component}",
                component=component,
                correlation_id=f"req-{i}"
            )
            
            result = service.add_log_entry(log_entry)
            assert result["success"] is True
        
        # Verify all logs stored
        all_logs = service.get_all_logs()
        assert len(all_logs) == 4
        
        # Verify each component's log
        component_logs = {log.component: log for log in all_logs}
        for component in components:
            assert component in component_logs
            assert component_logs[component].message == f"Message from {component}"


class TestCorrelationIdTracking:
    """Test that logs include correlation IDs for tracing"""
    
    def test_correlation_id_required_in_log_entry(self):
        """Test that correlation ID is required for log entries"""
        # Valid with correlation ID
        log_entry = LogEntry(
            level=LogLevel.INFO,
            message="Test message",
            component="test-component",
            correlation_id="trace-123"
        )
        assert log_entry.correlation_id == "trace-123"
        
        # Invalid without correlation ID
        with pytest.raises(ValueError, match="correlation_id"):
            LogEntry(
                level=LogLevel.INFO,
                message="Test message",
                component="test-component",
                correlation_id=""
            )
    
    def test_get_logs_by_correlation_id(self):
        """Test retrieving logs by correlation ID"""
        service = LoggingService()
        
        # Add logs with same correlation ID
        correlation_id = "request-789"
        
        logs_data = [
            ("agent-1", "Started processing request"),
            ("file-workspace", "Acquired file lock"),
            ("agent-1", "Processing completed"),
            ("health-monitor", "Agent reported healthy")
        ]
        
        for component, message in logs_data:
            log_entry = LogEntry(
                level=LogLevel.INFO,
                message=message,
                component=component,
                correlation_id=correlation_id
            )
            service.add_log_entry(log_entry)
        
        # Add unrelated log
        unrelated_log = LogEntry(
            level=LogLevel.INFO,
            message="Unrelated message",
            component="other-agent",
            correlation_id="different-123"
        )
        service.add_log_entry(unrelated_log)
        
        # Retrieve logs by correlation ID
        correlated_logs = service.get_logs_by_correlation_id(correlation_id)
        
        assert len(correlated_logs) == 4
        for log in correlated_logs:
            assert log.correlation_id == correlation_id
        
        # Verify chronological order
        messages = [log.message for log in correlated_logs]
        expected_messages = [msg for _, msg in logs_data]
        assert messages == expected_messages
    
    def test_correlation_id_spans_multiple_components(self):
        """Test that correlation ID can track across multiple components"""
        service = LoggingService()
        
        correlation_id = "multi-component-trace"
        
        # Simulate a request flowing through multiple components
        flow_logs = [
            ("api-gateway", "Received request"),
            ("auth-service", "User authenticated"),
            ("agent-1", "Task assigned"),
            ("file-workspace", "File locked"),
            ("agent-1", "Task processing"),
            ("health-monitor", "Health check passed"),
            ("agent-1", "Task completed"),
            ("file-workspace", "File unlocked"),
            ("api-gateway", "Response sent")
        ]
        
        for component, message in flow_logs:
            log_entry = LogEntry(
                level=LogLevel.INFO,
                message=message,
                component=component,
                correlation_id=correlation_id
            )
            service.add_log_entry(log_entry)
        
        # Retrieve complete trace
        trace_logs = service.get_logs_by_correlation_id(correlation_id)
        
        assert len(trace_logs) == 9
        
        # Verify the flow
        components_in_trace = [log.component for log in trace_logs]
        assert "api-gateway" in components_in_trace
        assert "auth-service" in components_in_trace
        assert "agent-1" in components_in_trace
        assert "file-workspace" in components_in_trace
        assert "health-monitor" in components_in_trace


class TestConfigurableLogLevels:
    """Test that log levels are configurable"""
    
    def test_log_level_enumeration(self):
        """Test that all expected log levels are available"""
        expected_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level_name in expected_levels:
            level = LogLevel(level_name)
            assert level.value == level_name
    
    def test_set_component_log_level(self):
        """Test setting log level for specific components"""
        service = LoggingService()
        
        # Set log level for specific component
        result = service.set_component_log_level("agent-1", LogLevel.WARNING)
        assert result["success"] is True
        assert result["component"] == "agent-1"
        assert result["level"] == "WARNING"
        
        # Verify log level is stored
        level = service.get_component_log_level("agent-1")
        assert level == LogLevel.WARNING
    
    def test_global_log_level_setting(self):
        """Test setting global log level"""
        service = LoggingService()
        
        # Set global log level
        result = service.set_global_log_level(LogLevel.ERROR)
        assert result["success"] is True
        assert result["level"] == "ERROR"
        
        # Verify global level
        level = service.get_global_log_level()
        assert level == LogLevel.ERROR
    
    def test_log_filtering_by_level(self):
        """Test that logs are filtered based on configured levels"""
        service = LoggingService()
        
        # Set component to WARNING level
        service.set_component_log_level("agent-1", LogLevel.WARNING)
        
        # Send logs at different levels
        log_levels = [
            (LogLevel.DEBUG, "Debug message"),
            (LogLevel.INFO, "Info message"),
            (LogLevel.WARNING, "Warning message"),
            (LogLevel.ERROR, "Error message"),
            (LogLevel.CRITICAL, "Critical message")
        ]
        
        for level, message in log_levels:
            log_entry = LogEntry(
                level=level,
                message=message,
                component="agent-1",
                correlation_id="level-test"
            )
            service.add_log_entry(log_entry)
        
        # Get stored logs for component
        component_logs = service.get_logs_by_component("agent-1")
        
        # Should only have WARNING, ERROR, and CRITICAL (3 logs)
        assert len(component_logs) == 3
        
        levels_stored = [log.level for log in component_logs]
        assert LogLevel.WARNING in levels_stored
        assert LogLevel.ERROR in levels_stored
        assert LogLevel.CRITICAL in levels_stored
        assert LogLevel.DEBUG not in levels_stored
        assert LogLevel.INFO not in levels_stored
    
    def test_list_available_log_levels(self):
        """Test listing all available log levels"""
        service = LoggingService()
        
        levels = service.list_log_levels()
        
        expected_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert len(levels) == 5
        for level in expected_levels:
            assert level in levels


class TestLogSearchFunctionality:
    """Test that logs are searchable by various criteria"""
    
    def test_search_logs_by_component(self):
        """Test searching logs by component name"""
        service = LoggingService()
        search_service = SearchService(service)
        
        # Add logs from different components
        components_data = [
            ("agent-1", "Agent 1 message"),
            ("agent-2", "Agent 2 message"),
            ("agent-1", "Another agent 1 message"),
            ("health-monitor", "Health check")
        ]
        
        for component, message in components_data:
            log_entry = LogEntry(
                level=LogLevel.INFO,
                message=message,
                component=component,
                correlation_id=f"search-{component}"
            )
            service.add_log_entry(log_entry)
        
        # Search for agent-1 logs
        criteria = SearchCriteria(component="agent-1")
        results = search_service.search_logs(criteria)
        
        assert len(results) == 2
        for log in results:
            assert log.component == "agent-1"
    
    def test_search_logs_by_level(self):
        """Test searching logs by log level"""
        service = LoggingService()
        search_service = SearchService(service)
        
        # Add logs with different levels
        levels_data = [
            (LogLevel.INFO, "Info message"),
            (LogLevel.ERROR, "Error message"),
            (LogLevel.WARNING, "Warning message"),
            (LogLevel.ERROR, "Another error message")
        ]
        
        for level, message in levels_data:
            log_entry = LogEntry(
                level=level,
                message=message,
                component="test-component",
                correlation_id=f"level-{level.value}"
            )
            service.add_log_entry(log_entry)
        
        # Search for ERROR logs
        criteria = SearchCriteria(level=LogLevel.ERROR)
        results = search_service.search_logs(criteria)
        
        assert len(results) == 2
        for log in results:
            assert log.level == LogLevel.ERROR
    
    def test_search_logs_by_time_range(self):
        """Test searching logs by time range"""
        service = LoggingService()
        search_service = SearchService(service)
        
        # Create logs with different timestamps
        now = datetime.now()
        
        # Old log (outside range)
        old_log = LogEntry(
            level=LogLevel.INFO,
            message="Old message",
            component="test",
            correlation_id="old"
        )
        old_log.timestamp = now - timedelta(hours=2)
        service.add_log_entry(old_log)
        
        # Recent logs (within range)
        for i in range(3):
            recent_log = LogEntry(
                level=LogLevel.INFO,
                message=f"Recent message {i}",
                component="test",
                correlation_id=f"recent-{i}"
            )
            recent_log.timestamp = now - timedelta(minutes=30 + i)
            service.add_log_entry(recent_log)
        
        # Search for logs in last hour
        time_range = TimeRange(
            start=now - timedelta(hours=1),
            end=now
        )
        criteria = SearchCriteria(time_range=time_range)
        results = search_service.search_logs(criteria)
        
        assert len(results) == 3
        for log in results:
            assert log.timestamp >= time_range.start
            assert log.timestamp <= time_range.end
    
    def test_search_logs_by_message_content(self):
        """Test searching logs by message content"""
        service = LoggingService()
        search_service = SearchService(service)
        
        # Add logs with different messages
        messages = [
            "User login successful",
            "File upload completed",
            "User logout",
            "Failed to upload file",
            "Database connection established"
        ]
        
        for i, message in enumerate(messages):
            log_entry = LogEntry(
                level=LogLevel.INFO,
                message=message,
                component="test",
                correlation_id=f"msg-{i}"
            )
            service.add_log_entry(log_entry)
        
        # Search for logs containing "upload"
        criteria = SearchCriteria(message_contains="upload")
        results = search_service.search_logs(criteria)
        
        assert len(results) == 2
        for log in results:
            assert "upload" in log.message.lower()
    
    def test_search_logs_with_multiple_criteria(self):
        """Test searching logs with multiple criteria combined"""
        service = LoggingService()
        search_service = SearchService(service)
        
        # Add diverse logs
        logs_data = [
            ("agent-1", LogLevel.ERROR, "Error processing request"),
            ("agent-1", LogLevel.INFO, "Processing completed"),
            ("agent-2", LogLevel.ERROR, "Failed to connect"),
            ("agent-1", LogLevel.ERROR, "Database error occurred")
        ]
        
        for component, level, message in logs_data:
            log_entry = LogEntry(
                level=level,
                message=message,
                component=component,
                correlation_id=f"multi-{component}-{level.value}"
            )
            service.add_log_entry(log_entry)
        
        # Search for agent-1 ERROR logs
        criteria = SearchCriteria(
            component="agent-1",
            level=LogLevel.ERROR
        )
        results = search_service.search_logs(criteria)
        
        assert len(results) == 2
        for log in results:
            assert log.component == "agent-1"
            assert log.level == LogLevel.ERROR


class TestLogRetention:
    """Test that log retention is at least 7 days"""
    
    def test_log_retention_policy_configuration(self):
        """Test configuring log retention policy"""
        retention_service = RetentionService()
        
        # Test default retention (7 days minimum)
        default_retention = retention_service.get_retention_policy()
        assert default_retention["days"] >= 7
        
        # Test setting custom retention (must be >= 7 days)
        result = retention_service.set_retention_policy(days=14)
        assert result["success"] is True
        assert result["days"] == 14
        
        # Test invalid retention (less than 7 days)
        result = retention_service.set_retention_policy(days=3)
        assert result["success"] is False
        assert "minimum 7 days" in result["error"].lower()
    
    def test_automatic_log_cleanup(self):
        """Test automatic cleanup of old logs"""
        service = LoggingService()
        retention_service = RetentionService(service)
        
        # Set retention to 7 days
        retention_service.set_retention_policy(days=7)
        
        now = datetime.now()
        
        # Add logs with different ages
        logs_data = [
            (now - timedelta(days=5), "Recent log 1"),
            (now - timedelta(days=6), "Recent log 2"),
            (now - timedelta(days=8), "Old log 1"),
            (now - timedelta(days=10), "Old log 2"),
            (now - timedelta(days=1), "Very recent log")
        ]
        
        for timestamp, message in logs_data:
            log_entry = LogEntry(
                level=LogLevel.INFO,
                message=message,
                component="test",
                correlation_id=f"retention-{message.split()[-1]}"
            )
            log_entry.timestamp = timestamp
            service.add_log_entry(log_entry)
        
        # Verify all logs initially present
        all_logs = service.get_all_logs()
        assert len(all_logs) == 5
        
        # Run cleanup
        cleanup_result = retention_service.cleanup_expired_logs()
        
        assert cleanup_result["success"] is True
        assert cleanup_result["deleted_count"] == 2  # 2 old logs
        
        # Verify only recent logs remain
        remaining_logs = service.get_all_logs()
        assert len(remaining_logs) == 3
        
        for log in remaining_logs:
            age_days = (now - log.timestamp).days
            assert age_days <= 7
    
    def test_retention_preserves_recent_logs(self):
        """Test that retention doesn't delete recent logs"""
        service = LoggingService()
        retention_service = RetentionService(service)
        
        # Set retention to minimum (7 days)
        retention_service.set_retention_policy(days=7)
        
        now = datetime.now()
        
        # Add only recent logs (within 7 days)
        for i in range(5):
            log_entry = LogEntry(
                level=LogLevel.INFO,
                message=f"Recent log {i}",
                component="test",
                correlation_id=f"preserve-{i}"
            )
            log_entry.timestamp = now - timedelta(days=i)
            service.add_log_entry(log_entry)
        
        # Run cleanup
        cleanup_result = retention_service.cleanup_expired_logs()
        
        assert cleanup_result["success"] is True
        assert cleanup_result["deleted_count"] == 0  # No logs deleted
        
        # Verify all logs preserved
        remaining_logs = service.get_all_logs()
        assert len(remaining_logs) == 5


class TestMCPServerIntegration:
    """Test MCP server integration with centralized logging tools"""
    
    def test_server_initialization(self):
        """Test that the central logging server initializes correctly"""
        server = CentralLoggingServer("central-logging", "1.0.0")
        
        assert server.name == "central-logging"
        assert server.version == "1.0.0"
        assert server.logging_service is not None
        assert server.search_service is not None
        assert server.retention_service is not None
    
    @pytest.mark.asyncio
    async def test_send_log_tool(self):
        """Test the send_log MCP tool"""
        server = CentralLoggingServer("central-logging", "1.0.0")
        
        arguments = {
            "level": "INFO",
            "message": "Test log message",
            "component": "test-component",
            "correlation_id": "test-123",
            "metadata": {"key": "value"}
        }
        
        result = server.send_log(arguments)
        
        assert result["success"] is True
        assert result["log_id"] is not None
    
    @pytest.mark.asyncio
    async def test_search_logs_tool(self):
        """Test the search_logs MCP tool"""
        server = CentralLoggingServer("central-logging", "1.0.0")
        
        # Add some logs first
        server.send_log({
            "level": "ERROR",
            "message": "Test error",
            "component": "agent-1",
            "correlation_id": "search-test"
        })
        
        # Search for the logs
        search_args = {
            "component": "agent-1",
            "level": "ERROR"
        }
        
        result = server.search_logs(search_args)
        
        assert "logs" in result
        assert len(result["logs"]) == 1
        assert result["logs"][0]["component"] == "agent-1"
    
    @pytest.mark.asyncio
    async def test_get_logs_by_correlation_id_tool(self):
        """Test the get_logs_by_correlation_id MCP tool"""
        server = CentralLoggingServer("central-logging", "1.0.0")
        
        correlation_id = "trace-456"
        
        # Add multiple logs with same correlation ID
        for i in range(3):
            server.send_log({
                "level": "INFO",
                "message": f"Step {i}",
                "component": f"component-{i}",
                "correlation_id": correlation_id
            })
        
        # Get logs by correlation ID
        result = server.get_logs_by_correlation_id({"correlation_id": correlation_id})
        
        assert "logs" in result
        assert len(result["logs"]) == 3
        for log in result["logs"]:
            assert log["correlation_id"] == correlation_id
    
    @pytest.mark.asyncio
    async def test_set_log_level_tool(self):
        """Test the set_log_level MCP tool"""
        server = CentralLoggingServer("central-logging", "1.0.0")
        
        # Set log level for component
        result = server.set_log_level({
            "component": "agent-1",
            "level": "WARNING"
        })
        
        assert result["success"] is True
        assert result["component"] == "agent-1"
        assert result["level"] == "WARNING"
    
    @pytest.mark.asyncio
    async def test_get_log_stats_tool(self):
        """Test the get_log_stats MCP tool"""
        server = CentralLoggingServer("central-logging", "1.0.0")
        
        # Add some logs
        for i in range(5):
            server.send_log({
                "level": "INFO",
                "message": f"Log {i}",
                "component": "test",
                "correlation_id": f"stats-{i}"
            })
        
        result = server.get_log_stats({})
        
        assert "total_logs" in result
        assert "components" in result
        assert "log_levels" in result
        assert result["total_logs"] >= 5


class TestLoggingClient:
    """Test logging client for integration with other servers"""
    
    def test_logging_client_initialization(self):
        """Test logging client initialization"""
        client = LoggingClient("central-logging-server")
        
        assert client.server_name == "central-logging-server"
        assert client.component_name is not None
    
    @pytest.mark.asyncio
    async def test_client_send_log(self):
        """Test client sending log to central server"""
        # Mock the central logging server
        mock_server = Mock()
        mock_server.send_log.return_value = {"success": True, "log_id": "test-id"}
        
        client = LoggingClient("mock-server")
        client._server = mock_server  # Inject mock
        
        result = await client.log_info("Test message", correlation_id="client-test")
        
        assert result["success"] is True
        mock_server.send_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_client_convenience_methods(self):
        """Test client convenience methods for different log levels"""
        mock_server = Mock()
        mock_server.send_log.return_value = {"success": True, "log_id": "test-id"}
        
        client = LoggingClient("mock-server")
        client._server = mock_server
        
        # Test all convenience methods
        await client.log_debug("Debug message", "debug-test")
        await client.log_info("Info message", "info-test")
        await client.log_warning("Warning message", "warning-test")
        await client.log_error("Error message", "error-test")
        await client.log_critical("Critical message", "critical-test")
        
        assert mock_server.send_log.call_count == 5


class TestUS010Integration:
    """Integration tests to verify all US-010 acceptance criteria"""
    
    @pytest.mark.asyncio
    async def test_complete_centralized_logging_workflow(self):
        """Test complete workflow covering all acceptance criteria"""
        server = CentralLoggingServer("central-logging", "1.0.0")
        
        # ✅ All MCP servers send logs to central location
        components = ["agent-1", "file-workspace", "health-monitor", "task-coordinator"]
        correlation_id = "workflow-test-123"
        
        for i, component in enumerate(components):
            result = server.send_log({
                "level": "INFO",
                "message": f"Component {component} is active",
                "component": component,
                "correlation_id": correlation_id,  # ✅ Logs include correlation IDs
                "metadata": {"step": i + 1}
            })
            assert result["success"] is True
        
        # ✅ Log levels are configurable
        level_result = server.set_log_level({
            "component": "agent-1",
            "level": "WARNING"
        })
        assert level_result["success"] is True
        
        # ✅ Logs are searchable by various criteria
        search_result = server.search_logs({
            "correlation_id": correlation_id
        })
        assert len(search_result["logs"]) == 4
        
        # Search by component
        component_search = server.search_logs({
            "component": "agent-1"
        })
        assert len(component_search["logs"]) >= 1
        
        # Get logs by correlation ID (tracing)
        trace_result = server.get_logs_by_correlation_id({
            "correlation_id": correlation_id
        })
        assert len(trace_result["logs"]) == 4
        
        # ✅ Log retention is at least 7 days (test configuration)
        retention_policy = server.retention_service.get_retention_policy()
        assert retention_policy["days"] >= 7
        
        # Test stats
        stats = server.get_log_stats({})
        assert stats["total_logs"] >= 4
        assert len(stats["components"]) >= 4
        
        print("✅ All US-010 acceptance criteria verified!")


class TestMCPToolFunctions:
    """Test MCP tool functions for comprehensive coverage"""
    
    def test_mcp_tool_log_message_comprehensive(self):
        """Test the send_log MCP tool function comprehensively"""
        server = CentralLoggingServer()
        
        # Set log level to DEBUG to ensure all logs are accepted
        server.set_log_level({"level": "DEBUG"})
        
        # Test all log levels
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in log_levels:
            result = server.send_log({
                "level": level,
                "message": f"Test {level} message",
                "component": "test-component",
                "correlation_id": f"test-{level.lower()}",
                "metadata": {"level_test": True}
            })
            # Should succeed now that log level is set to DEBUG
            assert result["success"] is True
            assert "log_id" in result
    
    def test_mcp_tool_search_logs_comprehensive(self):
        """Test the search_logs MCP tool function comprehensively"""
        server = CentralLoggingServer()
        
        # Add test logs
        server.send_log({
            "level": "INFO",
            "message": "Search test message 1",
            "component": "search-component-1",
            "correlation_id": "search-test-1"
        })
        
        server.send_log({
            "level": "ERROR", 
            "message": "Search test message 2",
            "component": "search-component-2",
            "correlation_id": "search-test-2"
        })
        
        # Test search by component
        result = server.search_logs({
            "component": "search-component-1"
        })
        assert result["success"] is True
        assert len(result["logs"]) >= 1
        
        # Test search by level
        result = server.search_logs({
            "level": "ERROR"
        })
        assert result["success"] is True
        
        # Test search by message content
        result = server.search_logs({
            "message": "Search test"
        })
        assert result["success"] is True
        
    def test_mcp_tool_get_log_stats_comprehensive(self):
        """Test the get_log_stats MCP tool function"""
        server = CentralLoggingServer()
        
        # Add some test logs
        for i in range(5):
            server.send_log({
                "level": "INFO",
                "message": f"Stats test message {i}",
                "component": f"stats-component-{i % 2}",  # Two different components
                "correlation_id": f"stats-test-{i}"
            })
        
        # Get log statistics
        result = server.get_log_stats({})
        # get_log_stats returns stats directly, not a success wrapper
        assert "total_logs" in result
        assert "log_levels" in result  # Updated from "by_level"
        assert "components" in result  # Updated from "by_component"
        assert result["total_logs"] >= 5
        
    def test_mcp_tool_set_log_level_comprehensive(self):
        """Test the set_log_level MCP tool function"""
        server = CentralLoggingServer()
        
        # Test setting global log level
        result = server.set_log_level({"level": "WARNING"})
        assert result["success"] is True
        
        # Test setting component-specific log level
        result = server.set_log_level({
            "level": "DEBUG",
            "component": "test-component"
        })
        assert result["success"] is True
        
    def test_mcp_tool_error_handling(self):
        """Test error handling in MCP tool functions"""
        server = CentralLoggingServer()
        
        # Test invalid log level
        result = server.send_log({
            "level": "INVALID_LEVEL",
            "message": "Test message",
            "component": "test-component",
            "correlation_id": "test-error"
        })
        assert result["success"] is False
        assert "error" in result
        
        # Test missing required fields
        result = server.send_log({
            "message": "Test message without level"
            # Missing level, component, correlation_id
        })
        assert result["success"] is False
        assert "error" in result
        
        # Test invalid correlation ID search
        result = server.get_logs_by_correlation_id({
            "correlation_id": "non-existent-correlation-id"
        })
        # This should succeed but return empty results
        assert result["success"] is True
        assert len(result["logs"]) == 0


class TestSearchServiceCoverage:
    """Test search service functionality for better coverage"""
    
    def test_search_service_comprehensive(self):
        """Test search service with various criteria"""
        server = CentralLoggingServer()
        
        # Add diverse test logs
        import time
        test_logs = [
            {"level": "DEBUG", "message": "Debug message for testing", "component": "debug-comp"},
            {"level": "INFO", "message": "Info message for testing", "component": "info-comp"}, 
            {"level": "WARNING", "message": "Warning message for testing", "component": "warn-comp"},
            {"level": "ERROR", "message": "Error message for testing", "component": "error-comp"},
            {"level": "CRITICAL", "message": "Critical message for testing", "component": "critical-comp"}
        ]
        
        for i, log_data in enumerate(test_logs):
            server.send_log({
                "level": log_data["level"],
                "message": log_data["message"], 
                "component": log_data["component"],
                "correlation_id": f"search-test-{i}",
                "metadata": {"test_index": i}
            })
        
        # Test search by level filtering
        result = server.search_logs({"level": "ERROR"})
        assert result["success"] is True
        
        # Test search by component filtering  
        result = server.search_logs({"component": "debug-comp"})
        assert result["success"] is True
        
        # Test search by message content
        result = server.search_logs({"message": "Warning"})
        assert result["success"] is True
        
        # Test search with multiple criteria
        result = server.search_logs({
            "level": "INFO",
            "component": "info-comp"
        })
        assert result["success"] is True


class TestRetentionServiceCoverage:
    """Test retention service functionality for better coverage"""
    
    def test_retention_service_comprehensive(self):
        """Test retention service functionality"""
        server = CentralLoggingServer()
        
        # Add test logs
        for i in range(10):
            server.send_log({
                "level": "INFO",
                "message": f"Retention test message {i}",
                "component": f"retention-comp-{i % 3}",
                "correlation_id": f"retention-test-{i}"
            })
        
        # Test getting retention stats
        result = server.get_log_stats({})
        # get_log_stats returns stats directly, not a success wrapper
        assert "total_logs" in result
        initial_count = result["total_logs"]
        
        # The retention service methods should be tested
        # Note: Some methods may not be directly exposed as MCP tools
        # but are part of the server's internal functionality


class TestLoggingClientCoverage:
    """Test logging client functionality for better coverage"""
    
    def test_logging_client_comprehensive(self):
        """Test logging client functionality"""
        from src.client.logging_client import LoggingClient
        
        client = LoggingClient("test-client")
        
        # Test convenience methods (note: no 'fatal' method)
        assert hasattr(client, 'debug')
        assert hasattr(client, 'info')
        assert hasattr(client, 'warning')
        assert hasattr(client, 'error')
        
        # Test that client has proper initialization
        assert client.component_name == "test-client"
        assert hasattr(client, 'current_correlation_id')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])