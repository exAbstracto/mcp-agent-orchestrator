#!/bin/bash
# Multi-Instance Coordination Demo Setup

set -e

CLAUDE_DIR="/tmp/mcp-agent-workspaces"
CURSOR_DIR="/tmp/cursor-agent-instances"

echo "🚀 Setting Up Multi-Instance Coordination Demo"
echo "=============================================="

# Clean up existing
rm -rf "$CLAUDE_DIR" "$CURSOR_DIR"

echo "📁 Setting up Claude Code workspaces..."
mkdir -p "$CLAUDE_DIR"/{backend-agent,frontend-agent,devops-agent,testing-agent}-workspace
mkdir -p "$CLAUDE_DIR/shared-workspace"/{messages,coordination,artifacts}

# Create Claude Code agent configs
agents=("backend-agent" "frontend-agent" "devops-agent" "testing-agent")
for agent in "${agents[@]}"; do
    workspace="$CLAUDE_DIR/$agent-workspace"
    
    cat > "$workspace/agent-config.json" << EOF
{
    "agent_id": "$agent",
    "platform": "claude-code",
    "workspace_path": "$workspace",
    "role": "${agent%-agent}",
    "capabilities": ["file_operations", "git_operations", "mcp_server"],
    "coordination": {
        "shared_workspace": "$CLAUDE_DIR/shared-workspace",
        "message_queue": "$CLAUDE_DIR/shared-workspace/messages/$agent"
    }
}
EOF

    mkdir -p "$CLAUDE_DIR/shared-workspace/messages/$agent"/{inbox,outbox,archive}
    
    cat > "$workspace/launch.sh" << EOF
#!/bin/bash
echo "🚀 Starting Claude Code Agent: $agent"
echo "📁 Workspace: $workspace"
echo "🔧 Unlimited tools, high memory efficiency"
echo "🔗 Shared workspace: $CLAUDE_DIR/shared-workspace"
echo "✅ $agent ready for coordination"
EOF
    chmod +x "$workspace/launch.sh"
    
    echo "✅ Created: $agent (Claude Code)"
done

echo "📁 Setting up Cursor instances..."
mkdir -p "$CURSOR_DIR"/{frontend-ui,pm-coordination,tech-writing}

# Frontend UI agent (Cursor) - 30/40 tools
mkdir -p "$CURSOR_DIR/frontend-ui"/{config,workspace,messages/{inbox,outbox}}
cat > "$CURSOR_DIR/frontend-ui/config.json" << EOF
{
    "agent_id": "frontend-ui",
    "platform": "cursor",
    "role": "frontend-ui",
    "tool_limit": 40,
    "current_tools": 30,
    "specialized_for": ["react", "vue", "css", "figma", "storybook"],
    "coordination": {
        "shared_with_claude": "$CLAUDE_DIR/shared-workspace"
    }
}
EOF

cat > "$CURSOR_DIR/frontend-ui/launch.sh" << EOF
#!/bin/bash
echo "🚀 Starting Cursor Agent: frontend-ui"
echo "📁 Workspace: $CURSOR_DIR/frontend-ui/workspace"
echo "🔧 Tools: 30/40 (Frontend UI specialized)"
echo "🎨 Optimized for: React, Vue, CSS, Figma integration"
echo "✅ Frontend UI agent ready"
EOF
chmod +x "$CURSOR_DIR/frontend-ui/launch.sh"

# PM Coordination agent (Cursor) - 25/40 tools
mkdir -p "$CURSOR_DIR/pm-coordination"/{config,workspace,messages/{inbox,outbox}}
cat > "$CURSOR_DIR/pm-coordination/config.json" << EOF
{
    "agent_id": "pm-coordination",
    "platform": "cursor",
    "role": "project-management",
    "tool_limit": 40,
    "current_tools": 25,
    "specialized_for": ["jira", "trello", "notion", "slack", "github"],
    "coordination": {
        "shared_with_claude": "$CLAUDE_DIR/shared-workspace"
    }
}
EOF

cat > "$CURSOR_DIR/pm-coordination/launch.sh" << EOF
#!/bin/bash
echo "🚀 Starting Cursor Agent: pm-coordination"
echo "📁 Workspace: $CURSOR_DIR/pm-coordination/workspace"
echo "🔧 Tools: 25/40 (PM & Coordination specialized)"
echo "📋 Optimized for: Project management, team coordination"
echo "✅ PM coordination agent ready"
EOF
chmod +x "$CURSOR_DIR/pm-coordination/launch.sh"

echo "✅ Created: frontend-ui (Cursor)"
echo "✅ Created: pm-coordination (Cursor)"

# Create shared coordination registry
cat > "$CLAUDE_DIR/shared-workspace/coordination/agent-registry.json" << EOF
{
    "registry_version": "1.0.0",
    "last_updated": "$(date -Iseconds)",
    "platforms": {
        "claude_code": {
            "agents": ["backend-agent", "frontend-agent", "devops-agent", "testing-agent"],
            "advantages": ["unlimited_tools", "memory_efficient", "cli_optimized"],
            "use_cases": ["backend_dev", "automation", "testing", "devops"]
        },
        "cursor": {
            "agents": ["frontend-ui", "pm-coordination"],
            "constraints": {"max_tools": 40},
            "advantages": ["gui_integration", "visual_editing"],
            "use_cases": ["ui_design", "project_management", "documentation"]
        }
    },
    "coordination_state": "demo_ready"
}
EOF

# Create test coordination script
cat > "$CLAUDE_DIR/test-coordination.py" << 'EOF'
#!/usr/bin/env python3
"""Multi-Instance Coordination Test"""

import json
import os
from pathlib import Path

def test_coordination():
    print("🧪 Testing Multi-Instance Coordination")
    print("=" * 40)
    
    claude_dir = Path("/tmp/mcp-agent-workspaces")
    cursor_dir = Path("/tmp/cursor-agent-instances")
    
    # Test Claude Code setup
    print("\n🔵 Claude Code Agents:")
    claude_agents = ["backend-agent", "frontend-agent", "devops-agent", "testing-agent"]
    for agent in claude_agents:
        workspace = claude_dir / f"{agent}-workspace"
        if workspace.exists():
            with open(workspace / "agent-config.json") as f:
                config = json.load(f)
            print(f"  ✅ {agent}: {config['role']} (unlimited tools)")
        else:
            print(f"  ❌ {agent}: workspace missing")
    
    # Test Cursor setup
    print("\n🟡 Cursor Agents:")
    cursor_agents = ["frontend-ui", "pm-coordination"]
    for agent in cursor_agents:
        workspace = cursor_dir / agent
        if workspace.exists():
            with open(workspace / "config.json") as f:
                config = json.load(f)
            tools = config['current_tools']
            limit = config['tool_limit']
            print(f"  ✅ {agent}: {config['role']} ({tools}/{limit} tools)")
        else:
            print(f"  ❌ {agent}: workspace missing")
    
    # Test shared workspace
    print("\n🔗 Shared Coordination:")
    registry = claude_dir / "shared-workspace" / "coordination" / "agent-registry.json"
    if registry.exists():
        with open(registry) as f:
            reg = json.load(f)
        claude_count = len(reg['platforms']['claude_code']['agents'])
        cursor_count = len(reg['platforms']['cursor']['agents'])
        print(f"  ✅ Registry: {claude_count} Claude + {cursor_count} Cursor agents")
        print(f"  ✅ State: {reg['coordination_state']}")
    else:
        print("  ❌ Coordination registry missing")
    
    # Test message queues
    print("\n📬 Message Coordination:")
    messages_dir = claude_dir / "shared-workspace" / "messages"
    if messages_dir.exists():
        agent_dirs = [d for d in messages_dir.iterdir() if d.is_dir()]
        print(f"  ✅ Message queues: {len(agent_dirs)} agents")
        for agent_dir in agent_dirs:
            inbox = agent_dir / "inbox"
            outbox = agent_dir / "outbox"
            if inbox.exists() and outbox.exists():
                print(f"    ✅ {agent_dir.name}: inbox & outbox ready")
    else:
        print("  ❌ Message coordination missing")
    
    print(f"\n🎉 Coordination demo ready!")
    print(f"   Claude Code: {claude_dir}")
    print(f"   Cursor: {cursor_dir}")

if __name__ == "__main__":
    test_coordination()
EOF

chmod +x "$CLAUDE_DIR/test-coordination.py"

echo
echo "🎉 Multi-Instance Coordination Demo Setup Complete!"
echo
echo "📊 Summary:"
echo "  🔵 Claude Code: 4 agents (unlimited tools)"
echo "  🟡 Cursor: 2 agents (40-tool limit managed)"
echo "  🔗 Shared workspace for coordination"
echo "  📬 Message queues for inter-agent communication"
echo
echo "🧪 Test the setup:"
echo "  python3 $CLAUDE_DIR/test-coordination.py"
echo
echo "🚀 Launch agents:"
echo "  # Claude Code agents:"
for agent in "${agents[@]}"; do
    echo "  cd $CLAUDE_DIR/$agent-workspace && ./launch.sh"
done
echo "  # Cursor agents:"
echo "  cd $CURSOR_DIR/frontend-ui && ./launch.sh"
echo "  cd $CURSOR_DIR/pm-coordination && ./launch.sh" 