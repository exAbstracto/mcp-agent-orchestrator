#!/usr/bin/env python3
"""
Demo script for the MCP Server Template

This script demonstrates basic usage of the MCP server template.
"""

import json
from src import MCPServer


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def main():
    """Run the MCP server demo."""
    
    # Create server instance
    print_section("Creating MCP Server")
    server = MCPServer("demo-server", "1.0.0")
    print(f"✓ Server created: {server.name} v{server.version}")
    
    # Register capabilities
    print_section("Registering Capabilities")
    server.register_capability("tools", {
        "supported": True,
        "listTools": True
    })
    server.register_capability("resources", {
        "supported": True,
        "types": ["file", "directory"]
    })
    print("✓ Capabilities registered")
    
    # Get server info
    print_section("Server Information")
    info = server.get_server_info()
    print(json.dumps(info, indent=2))
    
    # Handle initialize request
    print_section("Handling Initialize Request")
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "1.0.0",
            "clientInfo": {
                "name": "demo-client",
                "version": "0.1.0"
            }
        }
    }
    
    print("Request:")
    print(json.dumps(request, indent=2))
    
    response = server.handle_request(request)
    
    print("\nResponse:")
    print(json.dumps(response, indent=2))
    
    # Handle unknown method
    print_section("Handling Unknown Method")
    unknown_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "unknownMethod",
        "params": {}
    }
    
    print("Request:")
    print(json.dumps(unknown_request, indent=2))
    
    error_response = server.handle_request(unknown_request)
    
    print("\nResponse:")
    print(json.dumps(error_response, indent=2))
    
    # Invalid request
    print_section("Handling Invalid Request")
    invalid_request = {
        "method": "test"  # Missing jsonrpc and id
    }
    
    print("Request:")
    print(json.dumps(invalid_request, indent=2))
    
    invalid_response = server.handle_request(invalid_request)
    
    print("\nResponse:")
    print(json.dumps(invalid_response, indent=2))
    
    print_section("Demo Complete")
    print("✓ All basic MCP server functionality demonstrated")
    print("✓ Server is ready to be extended with custom methods")


if __name__ == "__main__":
    main() 