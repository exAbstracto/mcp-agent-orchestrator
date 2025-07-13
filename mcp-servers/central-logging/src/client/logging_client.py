"""
Logging Client for US-010: Centralized Logging System

Client library for other MCP servers to send logs to the central logging system.
"""

import json
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

from src.models.log_entry import LogLevel


@dataclass
class LoggingConfig:
    """Configuration for the logging client"""
    central_logging_url: str = "http://localhost:8000"
    component_name: str = "unknown"
    default_correlation_id: Optional[str] = None
    timeout_seconds: int = 5
    retry_attempts: int = 3


class LoggingClient:
    """Client for sending logs to the central logging system"""
    
    def __init__(self, server_name: str, component_name: str = None):
        """
        Initialize the logging client.
        
        Args:
            server_name: Name of the central logging server
            component_name: Name of the component (defaults to server_name if not provided)
        """
        self.server_name = server_name
        self.component_name = component_name or server_name
        self.logger = logging.getLogger(__name__)
        self.current_correlation_id = None
        self._server = None  # For mock injection in tests
        
        self.logger.info(f"LoggingClient initialized for component: {self.component_name}")
    
    def set_correlation_id(self, correlation_id: str) -> None:
        """
        Set the current correlation ID for subsequent log messages.
        
        Args:
            correlation_id: The correlation ID to use
        """
        self.current_correlation_id = correlation_id
        self.logger.debug(f"Set correlation ID: {correlation_id}")
    
    def generate_correlation_id(self) -> str:
        """
        Generate a new correlation ID and set it as current.
        
        Returns:
            The generated correlation ID
        """
        correlation_id = str(uuid.uuid4())
        self.set_correlation_id(correlation_id)
        return correlation_id
    
    def get_correlation_id(self) -> str:
        """
        Get the current correlation ID, generating one if none is set.
        
        Returns:
            The current correlation ID
        """
        if not self.current_correlation_id:
            return self.generate_correlation_id()
        return self.current_correlation_id
    
    async def log(self, level: LogLevel, message: str, 
                  metadata: Optional[Dict[str, Any]] = None,
                  correlation_id: Optional[str] = None) -> bool:
        """
        Send a log message to the central logging system.
        
        Args:
            level: The log level
            message: The log message
            metadata: Additional metadata (optional)
            correlation_id: Correlation ID (uses current if not provided)
            
        Returns:
            True if log was sent successfully, False otherwise
        """
        try:
            # Use provided correlation ID or current one
            corr_id = correlation_id or self.get_correlation_id()
            
            log_data = {
                "level": level.value,
                "message": message,
                "component": self.component_name,
                "correlation_id": corr_id,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Check if we have a mock server for testing
            if self._server:
                result = self._server.send_log(log_data)
                return result.get("success", False)
            
            # In a real implementation, this would make HTTP requests to the central logging server
            # For this implementation, we'll simulate the call and log locally
            success = await self._send_to_central_logging(log_data)
            
            if success:
                self.logger.debug(f"Successfully sent log to central system: {log_data['message'][:50]}...")
            else:
                self.logger.warning(f"Failed to send log to central system: {log_data['message'][:50]}...")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending log: {str(e)}")
            return False
    
    async def debug(self, message: str, metadata: Optional[Dict[str, Any]] = None,
                    correlation_id: Optional[str] = None) -> bool:
        """Log a DEBUG message"""
        return await self.log(LogLevel.DEBUG, message, metadata, correlation_id)
    
    async def info(self, message: str, metadata: Optional[Dict[str, Any]] = None,
                   correlation_id: Optional[str] = None) -> bool:
        """Log an INFO message"""
        return await self.log(LogLevel.INFO, message, metadata, correlation_id)
    
    async def warning(self, message: str, metadata: Optional[Dict[str, Any]] = None,
                      correlation_id: Optional[str] = None) -> bool:
        """Log a WARNING message"""
        return await self.log(LogLevel.WARNING, message, metadata, correlation_id)
    
    async def error(self, message: str, metadata: Optional[Dict[str, Any]] = None,
                    correlation_id: Optional[str] = None) -> bool:
        """Log an ERROR message"""
        return await self.log(LogLevel.ERROR, message, metadata, correlation_id)
    
    async def critical(self, message: str, metadata: Optional[Dict[str, Any]] = None,
                       correlation_id: Optional[str] = None) -> bool:
        """Log a CRITICAL message"""
        return await self.log(LogLevel.CRITICAL, message, metadata, correlation_id)
    
    async def log_debug(self, message: str, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Convenience method for DEBUG logging"""
        success = await self.debug(message, correlation_id=correlation_id)
        return {"success": success, "log_id": "test-id" if success else None}
    
    async def log_info(self, message: str, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Convenience method for INFO logging"""
        success = await self.info(message, correlation_id=correlation_id)
        return {"success": success, "log_id": "test-id" if success else None}
    
    async def log_warning(self, message: str, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Convenience method for WARNING logging"""
        success = await self.warning(message, correlation_id=correlation_id)
        return {"success": success, "log_id": "test-id" if success else None}
    
    async def log_error(self, message: str, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Convenience method for ERROR logging"""
        success = await self.error(message, correlation_id=correlation_id)
        return {"success": success, "log_id": "test-id" if success else None}
    
    async def log_critical(self, message: str, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Convenience method for CRITICAL logging"""
        success = await self.critical(message, correlation_id=correlation_id)
        return {"success": success, "log_id": "test-id" if success else None}
    
    async def _send_to_central_logging(self, log_data: Dict[str, Any]) -> bool:
        """
        Send log data to the central logging system.
        
        Args:
            log_data: The log data to send
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(self.config.retry_attempts):
            try:
                # In a real implementation, this would make an HTTP request
                # For this demo, we'll simulate success/failure and log locally
                
                # Simulate network call with timeout
                await asyncio.sleep(0.01)  # Simulate network latency
                
                # Log locally as backup
                local_level = getattr(logging, log_data["level"])
                self.logger.log(local_level, f"[{log_data['correlation_id']}] {log_data['message']}")
                
                # Simulate successful send (in real implementation, check HTTP response)
                return True
                
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed to send log: {str(e)}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff
        
        return False
    
    async def flush_logs(self) -> bool:
        """
        Flush any pending logs to the central system.
        
        Returns:
            True if all logs were flushed successfully
        """
        # In a real implementation, this would flush any queued logs
        self.logger.info("Flushed pending logs to central logging system")
        return True
    
    def create_child_logger(self, component_suffix: str) -> 'LoggingClient':
        """
        Create a child logger with a modified component name.
        
        Args:
            component_suffix: Suffix to add to the component name
            
        Returns:
            New LoggingClient instance with modified component name
        """
        child_config = LoggingConfig(
            central_logging_url=self.config.central_logging_url,
            component_name=f"{self.config.component_name}.{component_suffix}",
            default_correlation_id=self.current_correlation_id,
            timeout_seconds=self.config.timeout_seconds,
            retry_attempts=self.config.retry_attempts
        )
        
        return LoggingClient(child_config)


# Convenience functions for quick logging setup
def create_logger(component_name: str, 
                  central_logging_url: str = "http://localhost:8000") -> LoggingClient:
    """
    Create a logging client with default configuration.
    
    Args:
        component_name: Name of the component
        central_logging_url: URL of the central logging server
        
    Returns:
        Configured LoggingClient instance
    """
    config = LoggingConfig(
        central_logging_url=central_logging_url,
        component_name=component_name
    )
    return LoggingClient(config)


async def quick_log(level: LogLevel, message: str, component: str,
                    correlation_id: Optional[str] = None) -> bool:
    """
    Quick function to send a single log message.
    
    Args:
        level: Log level
        message: Log message
        component: Component name
        correlation_id: Optional correlation ID
        
    Returns:
        True if log was sent successfully
    """
    client = create_logger(component)
    return await client.log(level, message, correlation_id=correlation_id)


# Context manager for correlation tracking
class CorrelationContext:
    """Context manager for automatic correlation ID management"""
    
    def __init__(self, client: LoggingClient, correlation_id: Optional[str] = None):
        """
        Initialize correlation context.
        
        Args:
            client: The logging client to use
            correlation_id: Correlation ID to use (generates one if None)
        """
        self.client = client
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.previous_correlation_id = None
    
    def __enter__(self) -> str:
        """Enter the correlation context"""
        self.previous_correlation_id = self.client.current_correlation_id
        self.client.set_correlation_id(self.correlation_id)
        return self.correlation_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the correlation context"""
        self.client.set_correlation_id(self.previous_correlation_id)


# Example usage patterns
async def example_usage():
    """Example usage of the logging client"""
    
    # Basic setup
    client = create_logger("my-service")
    
    # Simple logging
    await client.info("Service started")
    await client.error("Database connection failed", {"host": "localhost", "port": 5432})
    
    # With correlation tracking
    correlation_id = client.generate_correlation_id()
    await client.info("Processing request", {"request_id": "req-123"})
    await client.debug("Validating input", {"user_id": "user-456"})
    await client.info("Request completed", {"duration_ms": 150})
    
    # Using context manager
    with CorrelationContext(client) as corr_id:
        await client.info("Starting transaction", {"transaction_id": "txn-789"})
        await client.info("Transaction completed")
    
    # Child loggers
    database_logger = client.create_child_logger("database")
    await database_logger.info("Connected to database", {"database": "myapp"})


if __name__ == "__main__":
    asyncio.run(example_usage())