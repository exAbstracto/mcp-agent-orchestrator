#!/bin/bash
# Simplified Git Worktree Setup for Claude Code Multi-Instance Coordination

set -e

BASE_DIR="/tmp/mcp-agent-workspaces"

echo "🚀 Setting Up Claude Code Git Worktrees"
echo "======================================="

# Cleanup and setup
rm -rf "$BASE_DIR"
mkdir -p "$BASE_DIR"

# Create worktrees for different agents
agents=("backend-agent" "frontend-agent" "devops-agent" "testing-agent")

for agent in "${agents[@]}"; do
    workspace="$BASE_DIR/$agent-workspace"
    branch="develop-$agent"
    
    echo "📁 Creating worktree for: $agent"
    # Create a new branch for this agent based on develop
    git checkout develop
    git checkout -b "$branch" 2>/dev/null || git checkout "$branch"
    git worktree add "$workspace" "$branch"
    
    # Create agent directories
    mkdir -p "$workspace/agent-workspace/$agent"
    mkdir -p "$workspace/logs/$agent"
    
    # Create agent config
    cat > "$workspace/agent-config.json" << EOF
{
    "agent_id": "$agent",
    "workspace_path": "$workspace",
    "branch": "$branch",
    "role": "${agent%-agent}",
    "created_at": "$(date -Iseconds)",
    "mcp_server_port": 8000,
    "capabilities": {
        "file_operations": true,
        "git_operations": true,
        "inter_agent_messaging": true
    }
}
EOF

    # Create launch script
    cat > "$workspace/launch-agent.sh" << EOF
#!/bin/bash
echo "🚀 Starting $agent..."
echo "📁 Workspace: $workspace"
echo "🔧 MCP Server on port 8000"
echo "✅ $agent is running. Press Ctrl+C to stop."
while true; do sleep 1; done
EOF
    chmod +x "$workspace/launch-agent.sh"
    
    echo "✅ Created: $agent-workspace"
done

# Create shared workspace
mkdir -p "$BASE_DIR/shared-workspace"/{messages,coordination,artifacts}

# Create agent registry
cat > "$BASE_DIR/shared-workspace/coordination/agent-registry.json" << EOF
{
    "registry_version": "1.0.0",
    "last_updated": "$(date -Iseconds)",
    "active_agents": {},
    "message_queue": [],
    "coordination_state": "initialized"
}
EOF

# Create message directories
for agent in "${agents[@]}"; do
    mkdir -p "$BASE_DIR/shared-workspace/messages/$agent"/{inbox,outbox,archive}
done

echo
echo "✅ Git worktree setup complete!"
echo "📁 Workspaces created:"
for agent in "${agents[@]}"; do
    echo "   - $BASE_DIR/$agent-workspace"
done
echo
echo "🚀 Test coordination:"
echo "cd $BASE_DIR/backend-agent-workspace && ./launch-agent.sh" 