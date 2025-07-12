#!/usr/bin/env python3
"""
Real MCP Client for Agent Coordination
Uses official MCP Python SDK to coordinate multiple agent servers
"""

import asyncio
import json
import logging
from typing import Dict, List, Any
from datetime import datetime

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CoordinationOrchestrator:
    """
    Orchestrates coordination between multiple MCP agent servers
    """
    
    def __init__(self):
        self.agent_sessions: Dict[str, ClientSession] = {}
        self.agent_configs = {
            "backend-dev": {
                "command": "python",
                "args": ["../mcp-servers/real-mcp-server.py", "agent-001", "backend-dev"],
                "description": "Backend Development Agent"
            },
            "frontend-dev": {
                "command": "python", 
                "args": ["../mcp-servers/real-mcp-server.py", "agent-002", "frontend-dev"],
                "description": "Frontend Development Agent"
            },
            "tester": {
                "command": "python",
                "args": ["../mcp-servers/real-mcp-server.py", "agent-003", "tester"],
                "description": "Testing Agent"
            }
        }
    
    async def start_coordination(self):
        """Start coordination between all agents"""
        logger.info("🚀 Starting Multi-Agent Coordination using Real MCP Protocol")
        
        # Connect to all agent servers
        sessions = {}
        for agent_role, config in self.agent_configs.items():
            server_params = StdioServerParameters(
                command=config["command"],
                args=config["args"]
            )
            
            try:
                # Start server connection
                read, write = await stdio_client(server_params).__aenter__()
                session = ClientSession(read, write)
                await session.initialize()
                sessions[agent_role] = session
                logger.info(f"✅ Connected to {config['description']}")
                
            except Exception as e:
                logger.error(f"❌ Failed to connect to {agent_role}: {e}")
                continue
        
        self.agent_sessions = sessions
        
        # Demonstrate coordination workflow
        await self._demonstrate_coordination_workflow()
        
        # Cleanup connections
        for session in sessions.values():
            await session.__aexit__(None, None, None)
    
    async def _demonstrate_coordination_workflow(self):
        """Demonstrate real agent coordination workflow"""
        logger.info("\n🎭 Starting Multi-Agent Development Workflow")
        
        # 1. Backend creates API specification
        if "backend-dev" in self.agent_sessions:
            await self._create_api_spec()
        
        # 2. Frontend creates UI component
        if "frontend-dev" in self.agent_sessions:
            await self._create_ui_component()
        
        # 3. Tester creates test cases
        if "tester" in self.agent_sessions:
            await self._create_test_cases()
        
        # 4. Cross-agent coordination
        await self._coordinate_agents()
        
        # 5. Status check
        await self._check_all_statuses()
    
    async def _create_api_spec(self):
        """Backend agent creates API specification"""
        backend_session = self.agent_sessions["backend-dev"]
        
        api_spec = """
        {
          "endpoints": {
            "/api/users": {
              "GET": "List all users",
              "POST": "Create new user"
            },
            "/api/users/{id}": {
              "GET": "Get user by ID",
              "PUT": "Update user",
              "DELETE": "Delete user"
            }
          }
        }
        """
        
        result = await backend_session.call_tool(
            "create_artifact",
            {
                "name": "user-api-spec",
                "type": "docs",
                "content": api_spec,
                "language": "json"
            }
        )
        
        logger.info("📋 Backend: Created API specification")
        print(f"Result: {result}")
    
    async def _create_ui_component(self):
        """Frontend agent creates UI component"""
        frontend_session = self.agent_sessions["frontend-dev"]
        
        ui_component = """
        import React, { useState, useEffect } from 'react';
        
        const UserList = () => {
          const [users, setUsers] = useState([]);
          
          useEffect(() => {
            fetch('/api/users')
              .then(res => res.json())
              .then(data => setUsers(data));
          }, []);
          
          return (
            <div className="user-list">
              <h2>Users</h2>
              {users.map(user => (
                <div key={user.id} className="user-card">
                  <h3>{user.name}</h3>
                  <p>{user.email}</p>
                </div>
              ))}
            </div>
          );
        };
        
        export default UserList;
        """
        
        result = await frontend_session.call_tool(
            "create_artifact",
            {
                "name": "UserList.jsx",
                "type": "code",
                "content": ui_component,
                "language": "javascript"
            }
        )
        
        logger.info("🎨 Frontend: Created UI component")
        print(f"Result: {result}")
    
    async def _create_test_cases(self):
        """Tester agent creates test cases"""
        tester_session = self.agent_sessions["tester"]
        
        test_cases = """
        import pytest
        import requests
        
        class TestUserAPI:
            
            def test_get_users(self):
                response = requests.get('/api/users')
                assert response.status_code == 200
                assert isinstance(response.json(), list)
            
            def test_create_user(self):
                user_data = {
                    'name': 'John Doe',
                    'email': 'john@example.com'
                }
                response = requests.post('/api/users', json=user_data)
                assert response.status_code == 201
                assert response.json()['name'] == user_data['name']
            
            def test_get_user_by_id(self):
                response = requests.get('/api/users/1')
                assert response.status_code == 200
                assert 'id' in response.json()
        """
        
        result = await tester_session.call_tool(
            "create_artifact",
            {
                "name": "test_user_api.py",
                "type": "test", 
                "content": test_cases,
                "language": "python"
            }
        )
        
        logger.info("🧪 Tester: Created test cases")
        print(f"Result: {result}")
    
    async def _coordinate_agents(self):
        """Demonstrate inter-agent coordination"""
        logger.info("\n💬 Coordinating between agents...")
        
        # Backend sends message to Frontend
        if "backend-dev" in self.agent_sessions and "frontend-dev" in self.agent_sessions:
            await self.agent_sessions["backend-dev"].call_tool(
                "send_message",
                {
                    "to_agent": "agent-002",
                    "message": "API specification is ready. Please ensure your UI component handles all endpoints correctly.",
                    "priority": "high"
                }
            )
        
        # Frontend responds to Backend
        if "frontend-dev" in self.agent_sessions:
            await self.agent_sessions["frontend-dev"].call_tool(
                "send_message",
                {
                    "to_agent": "agent-001",
                    "message": "UI component created. Added error handling for API calls. Ready for integration testing.",
                    "priority": "medium"
                }
            )
        
        # Tester coordinates with both
        if "tester" in self.agent_sessions:
            await self.agent_sessions["tester"].call_tool(
                "send_message",
                {
                    "to_agent": "agent-001",
                    "message": "Test cases created for API endpoints. Please run integration tests before deployment.",
                    "priority": "high"
                }
            )
            
            await self.agent_sessions["tester"].call_tool(
                "send_message",
                {
                    "to_agent": "agent-002", 
                    "message": "UI tests needed. Please add data-testid attributes to components for E2E testing.",
                    "priority": "medium"
                }
            )
    
    async def _check_all_statuses(self):
        """Check status of all agents"""
        logger.info("\n📊 Checking coordination status...")
        
        for role, session in self.agent_sessions.items():
            try:
                result = await session.call_tool(
                    "get_coordination_status",
                    {"include_history": True}
                )
                print(f"\n{role.upper()} STATUS:")
                print("=" * 50)
                for content in result:
                    if hasattr(content, 'text'):
                        print(content.text)
                        
            except Exception as e:
                logger.error(f"Failed to get status for {role}: {e}")


async def main():
    """Main coordination demo"""
    orchestrator = CoordinationOrchestrator()
    
    try:
        await orchestrator.start_coordination()
        logger.info("✅ Coordination demo completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Coordination failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 