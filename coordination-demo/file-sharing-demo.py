#!/usr/bin/env python3
"""
File Sharing Demonstration

This script demonstrates how agents can share files and coordinate
work across different platforms (Cursor and Claude Code).
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime

def create_test_scenario():
    """Create a test scenario showing file sharing between agents"""
    
    print("🎬 File Sharing Demonstration")
    print("=" * 40)
    
    claude_dir = Path("/tmp/mcp-agent-workspaces")
    cursor_dir = Path("/tmp/cursor-agent-instances")
    shared_dir = claude_dir / "shared-workspace"
    
    # Scenario: Backend agent creates API spec, Frontend UI agent creates UI mockup
    
    print("\n📝 Scenario: API Development Coordination")
    print("Backend Agent (Claude Code) → Frontend UI Agent (Cursor)")
    
    # 1. Backend agent creates API specification
    backend_workspace = claude_dir / "backend-agent-workspace"
    api_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Multi-Agent API",
            "version": "1.0.0",
            "description": "API created by backend agent for frontend consumption"
        },
        "paths": {
            "/api/users": {
                "get": {
                    "summary": "Get users",
                    "responses": {
                        "200": {
                            "description": "List of users",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "name": {"type": "string"},
                                                "email": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Save API spec in backend workspace
    with open(backend_workspace / "api-spec.json", 'w') as f:
        json.dump(api_spec, f, indent=2)
    
    # Share with frontend team via shared workspace
    shared_artifacts = shared_dir / "artifacts"
    with open(shared_artifacts / "api-spec-v1.json", 'w') as f:
        json.dump(api_spec, f, indent=2)
    
    print("✅ Backend Agent: Created API specification")
    print(f"   📄 Saved to: {backend_workspace}/api-spec.json")
    print(f"   🔗 Shared to: {shared_artifacts}/api-spec-v1.json")
    
    # 2. Send message to frontend UI agent
    message = {
        "from": "backend-agent",
        "to": "frontend-ui",
        "type": "file_share",
        "content": "API specification ready for frontend implementation",
        "attachments": [
            {
                "type": "api_spec",
                "path": "/tmp/mcp-agent-workspaces/shared-workspace/artifacts/api-spec-v1.json",
                "description": "OpenAPI 3.0 specification for user management API"
            }
        ],
        "timestamp": datetime.now().isoformat(),
        "priority": "high"
    }
    
    # Save message in backend outbox
    backend_outbox = shared_dir / "messages" / "backend-agent" / "outbox"
    with open(backend_outbox / f"api-spec-{int(time.time())}.json", 'w') as f:
        json.dump(message, f, indent=2)
    
    print("✅ Backend Agent: Sent coordination message")
    print(f"   📧 Message queued in: {backend_outbox}")
    
    # 3. Simulate frontend UI agent receiving and processing
    print("\n🎨 Frontend UI Agent (Cursor) Processing...")
    
    # Frontend agent creates UI mockup based on API
    ui_mockup = {
        "component": "UsersList",
        "framework": "React",
        "based_on_api": "/api/users",
        "props": {
            "users": [
                {"id": 1, "name": "John Doe", "email": "john@example.com"},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
            ]
        },
        "jsx": """
import React from 'react';

const UsersList = ({ users }) => {
  return (
    <div className="users-list">
      <h2>Users</h2>
      <div className="users-grid">
        {users.map(user => (
          <div key={user.id} className="user-card">
            <h3>{user.name}</h3>
            <p>{user.email}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default UsersList;
        """,
        "css": """
.users-list {
  padding: 20px;
}

.users-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.user-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 16px;
  background: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
        """
    }
    
    # Save in frontend workspace
    frontend_workspace = cursor_dir / "frontend-ui" / "workspace"
    with open(frontend_workspace / "UsersList.json", 'w') as f:
        json.dump(ui_mockup, f, indent=2)
    
    # Share back to shared workspace
    with open(shared_artifacts / "users-ui-mockup.json", 'w') as f:
        json.dump(ui_mockup, f, indent=2)
    
    print("✅ Frontend UI Agent: Created React component mockup")
    print(f"   📄 Saved to: {frontend_workspace}/UsersList.json")
    print(f"   🔗 Shared to: {shared_artifacts}/users-ui-mockup.json")
    
    # 4. Send feedback message back to backend
    feedback_message = {
        "from": "frontend-ui",
        "to": "backend-agent",
        "type": "feedback",
        "content": "UI mockup created. Suggest adding pagination for large user lists.",
        "attachments": [
            {
                "type": "ui_mockup",
                "path": "/tmp/mcp-agent-workspaces/shared-workspace/artifacts/users-ui-mockup.json",
                "description": "React component mockup for users list"
            }
        ],
        "suggestions": [
            "Add pagination parameters to /api/users endpoint",
            "Include total count in API response",
            "Add search/filter capabilities"
        ],
        "timestamp": datetime.now().isoformat()
    }
    
    # Note: In real implementation, this would go through the coordination bridge
    # For demo, we'll show the cross-platform message structure
    print("\n🔄 Cross-Platform Coordination Message:")
    print(json.dumps(feedback_message, indent=2))
    
    print("\n📊 File Sharing Summary:")
    print("✅ Backend Agent (Claude Code):")
    print("   - Created API specification")
    print("   - Shared via common workspace")
    print("   - Sent coordination message")
    
    print("✅ Frontend UI Agent (Cursor):")
    print("   - Received API specification")
    print("   - Created React component mockup")
    print("   - Provided feedback and suggestions")
    
    print("✅ Shared Workspace:")
    artifacts = list(shared_artifacts.glob("*.json"))
    print(f"   - {len(artifacts)} shared artifacts")
    for artifact in artifacts:
        print(f"     📄 {artifact.name}")
    
    return True

def test_file_operations():
    """Test various file operations between agents"""
    
    print("\n🧪 Testing File Operations")
    print("-" * 30)
    
    claude_dir = Path("/tmp/mcp-agent-workspaces")
    cursor_dir = Path("/tmp/cursor-agent-instances")
    shared_dir = claude_dir / "shared-workspace"
    
    operations_tested = []
    
    # Test 1: Claude Code agent creates files
    backend_workspace = claude_dir / "backend-agent-workspace"
    test_file = backend_workspace / "test-backend-file.txt"
    with open(test_file, 'w') as f:
        f.write("This file was created by Claude Code backend agent\n")
        f.write("Timestamp: " + datetime.now().isoformat() + "\n")
    operations_tested.append("✅ Claude Code: File creation")
    
    # Test 2: Cursor agent creates files  
    frontend_workspace = cursor_dir / "frontend-ui" / "workspace"
    test_file = frontend_workspace / "test-cursor-file.txt"
    with open(test_file, 'w') as f:
        f.write("This file was created by Cursor frontend UI agent\n")
        f.write("Timestamp: " + datetime.now().isoformat() + "\n")
    operations_tested.append("✅ Cursor: File creation")
    
    # Test 3: Shared file access
    shared_file = shared_dir / "artifacts" / "shared-test-file.txt"
    with open(shared_file, 'w') as f:
        f.write("This file is accessible by all agents\n")
        f.write("Created for coordination testing\n")
    operations_tested.append("✅ Shared: Common file access")
    
    # Test 4: File listing
    claude_files = list(backend_workspace.glob("*.txt"))
    cursor_files = list(frontend_workspace.glob("*.txt"))
    shared_files = list(shared_dir.glob("**/*.txt"))
    operations_tested.append(f"✅ File listing: {len(claude_files)} Claude, {len(cursor_files)} Cursor, {len(shared_files)} shared")
    
    print("\n📋 File Operations Results:")
    for operation in operations_tested:
        print(f"  {operation}")
    
    return True

if __name__ == "__main__":
    success = True
    
    try:
        create_test_scenario()
        test_file_operations()
        
        print("\n🎉 File Sharing Demonstration Complete!")
        print("All agents can successfully share files and coordinate work.")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        success = False
    
    exit(0 if success else 1) 