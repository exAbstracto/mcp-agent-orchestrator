#!/bin/bash
"""
Git Worktree Setup for Claude Code Multi-Instance Coordination

This script creates separate git worktrees for different Claude Code agents,
allowing them to work on the same repository simultaneously without conflicts.
"""

set -e  # Exit on any error

# Configuration
BASE_DIR="/tmp/mcp-agent-workspaces"
REPO_URL="https://github.com/exAbstracto/mcp-agent-orchestrator.git"

# Agent configurations
declare -A AGENTS=(
    ["backend-agent"]="develop"
    ["frontend-agent"]="develop"  
    ["devops-agent"]="develop"
    ["testing-agent"]="develop"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

cleanup_existing() {
    print_header "Cleaning Up Existing Workspaces"
    
    if [ -d "$BASE_DIR" ]; then
        print_warning "Removing existing workspace directory: $BASE_DIR"
        rm -rf "$BASE_DIR"
    fi
    
    # Clean up any existing worktrees in current repo
    if git worktree list >/dev/null 2>&1; then
        for agent in "${!AGENTS[@]}"; do
            workspace="$BASE_DIR/$agent-workspace"
            if git worktree list | grep -q "$workspace"; then
                print_warning "Removing existing worktree: $workspace"
                git worktree remove "$workspace" --force 2>/dev/null || true
            fi
        done
    fi
    
    print_success "Cleanup complete"
    echo
}

setup_base_directory() {
    print_header "Setting Up Base Directory"
    
    mkdir -p "$BASE_DIR"
    print_success "Created base directory: $BASE_DIR"
    echo
}

create_worktrees() {
    print_header "Creating Git Worktrees for Each Agent"
    
    for agent in "${!AGENTS[@]}"; do
        branch="${AGENTS[$agent]}"
        workspace="$BASE_DIR/$agent-workspace"
        
        echo -e "${BLUE}Setting up worktree for: $agent${NC}"
        
        # Create the worktree
        if git worktree add "$workspace" "$branch"; then
            print_success "Created worktree: $workspace (branch: $branch)"
            
            # Create agent-specific directories
            mkdir -p "$workspace/agent-workspace/$agent"
            mkdir -p "$workspace/logs/$agent"
            mkdir -p "$workspace/temp/$agent"
            
            # Create agent configuration
            cat > "$workspace/agent-config.json" << EOF
{
    "agent_id": "$agent",
    "workspace_path": "$workspace",
    "branch": "$branch",
    "role": "$(echo $agent | sed 's/-agent//')",
    "created_at": "$(date -Iseconds)",
    "mcp_server_port": $((8000 + $(echo "$agent" | tr -dc '0-9' | head -c1))),
    "capabilities": {
        "file_operations": true,
        "git_operations": true,
        "inter_agent_messaging": true
    }
}
EOF
            print_success "Created configuration for $agent"
            
        else
            print_error "Failed to create worktree for $agent"
            exit 1
        fi
        echo
    done
}

create_shared_workspace() {
    print_header "Setting Up Shared Workspace"
    
    shared_dir="$BASE_DIR/shared-workspace"
    mkdir -p "$shared_dir"/{messages,coordination,artifacts}
    
    # Create shared coordination file
    cat > "$shared_dir/coordination/agent-registry.json" << EOF
{
    "registry_version": "1.0.0",
    "last_updated": "$(date -Iseconds)",
    "active_agents": {},
    "message_queue": [],
    "coordination_state": "initialized"
}
EOF

    # Create message queue directory structure
    for agent in "${!AGENTS[@]}"; do
        mkdir -p "$shared_dir/messages/$agent"/{inbox,outbox,archive}
    done
    
    print_success "Created shared workspace: $shared_dir"
    echo
}

create_demo_scripts() {
    print_header "Creating Demo Scripts"
    
    # Create launch script for each agent
    for agent in "${!AGENTS[@]}"; do
        workspace="$BASE_DIR/$agent-workspace"
        
        cat > "$workspace/launch-agent.sh" << EOF
#!/bin/bash
# Launch script for $agent

WORKSPACE_DIR="$workspace"
AGENT_ID="$agent"
SHARED_DIR="$BASE_DIR/shared-workspace"

echo "🚀 Starting \$AGENT_ID..."
echo "📁 Workspace: \$WORKSPACE_DIR"
echo "🔗 Shared: \$SHARED_DIR"

# Register agent in shared registry
python3 -c "
import json
import datetime

registry_file = '\$SHARED_DIR/coordination/agent-registry.json'
with open(registry_file, 'r') as f:
    registry = json.load(f)

registry['active_agents']['\$AGENT_ID'] = {
    'workspace': '\$WORKSPACE_DIR',
    'status': 'active',
    'last_seen': datetime.datetime.now().isoformat(),
    'pid': $$
}

registry['last_updated'] = datetime.datetime.now().isoformat()

with open(registry_file, 'w') as f:
    json.dump(registry, f, indent=2)

print(f'✅ Registered agent: \$AGENT_ID')
"

# Start the MCP server (simulation)
echo "🔧 Starting MCP server for \$AGENT_ID..."
echo "   Port: \$(cat agent-config.json | grep mcp_server_port | grep -o '[0-9]*')"
echo "   Workspace: \$WORKSPACE_DIR"
echo "   Shared: \$SHARED_DIR"

# Keep running (in real implementation, this would start the actual MCP server)
echo "✅ \$AGENT_ID is running. Press Ctrl+C to stop."
trap 'echo "🛑 Stopping \$AGENT_ID..."; exit 0' INT
while true; do
    sleep 1
done
EOF
        
        chmod +x "$workspace/launch-agent.sh"
        print_success "Created launch script for $agent"
    done
    
    echo
}

create_coordination_test() {
    print_header "Creating Coordination Test"
    
    cat > "$BASE_DIR/test-coordination.py" << '#!/usr/bin/env python3'
"""
Multi-Instance Coordination Test

This script tests the coordination between multiple agent instances
using git worktrees and shared workspace approach.
"""

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List

class CoordinationTest:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.shared_dir = self.base_dir / "shared-workspace"
        self.registry_file = self.shared_dir / "coordination" / "agent-registry.json"
        
    def test_worktree_isolation(self) -> bool:
        """Test that each agent has isolated workspace"""
        print("🧪 Testing worktree isolation...")
        
        agents = ["backend-agent", "frontend-agent", "devops-agent", "testing-agent"]
        
        for agent in agents:
            workspace = self.base_dir / f"{agent}-workspace"
            if not workspace.exists():
                print(f"❌ Workspace missing for {agent}: {workspace}")
                return False
            
            config_file = workspace / "agent-config.json"
            if not config_file.exists():
                print(f"❌ Config missing for {agent}: {config_file}")
                return False
                
            # Test that each workspace has proper git setup
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=workspace,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ Git not properly set up in {workspace}")
                return False
                
            print(f"✅ {agent}: workspace isolated, branch: {result.stdout.strip()}")
        
        return True
    
    def test_shared_workspace(self) -> bool:
        """Test shared workspace accessibility"""
        print("\n🧪 Testing shared workspace...")
        
        required_dirs = [
            "messages",
            "coordination", 
            "artifacts"
        ]
        
        for dir_name in required_dirs:
            dir_path = self.shared_dir / dir_name
            if not dir_path.exists():
                print(f"❌ Missing shared directory: {dir_path}")
                return False
            print(f"✅ Shared directory exists: {dir_name}")
        
        return True
    
    def test_agent_registration(self) -> bool:
        """Test agent registration mechanism"""
        print("\n🧪 Testing agent registration...")
        
        if not self.registry_file.exists():
            print(f"❌ Registry file missing: {self.registry_file}")
            return False
        
        with open(self.registry_file) as f:
            registry = json.load(f)
        
        required_fields = ["registry_version", "last_updated", "active_agents", "message_queue"]
        for field in required_fields:
            if field not in registry:
                print(f"❌ Missing registry field: {field}")
                return False
        
        print("✅ Registry structure valid")
        return True
    
    def test_message_coordination(self) -> bool:
        """Test message passing between agents"""
        print("\n🧪 Testing message coordination...")
        
        # Create test message
        test_message = {
            "from": "backend-agent",
            "to": "frontend-agent", 
            "type": "coordination_test",
            "content": "Hello from backend agent!",
            "timestamp": time.time()
        }
        
        # Write message to outbox
        backend_outbox = self.shared_dir / "messages" / "backend-agent" / "outbox"
        frontend_inbox = self.shared_dir / "messages" / "frontend-agent" / "inbox"
        
        message_file = backend_outbox / f"test-{int(time.time())}.json"
        with open(message_file, 'w') as f:
            json.dump(test_message, f, indent=2)
        
        print(f"✅ Created test message: {message_file}")
        
        # Simulate message delivery (copy from outbox to inbox)
        inbox_file = frontend_inbox / message_file.name
        with open(message_file) as f:
            message = json.load(f)
        
        with open(inbox_file, 'w') as f:
            json.dump(message, f, indent=2)
        
        print(f"✅ Delivered message to: {inbox_file}")
        
        # Verify message received
        if inbox_file.exists():
            with open(inbox_file) as f:
                received = json.load(f)
                if received["content"] == test_message["content"]:
                    print("✅ Message coordination test passed")
                    return True
        
        print("❌ Message coordination test failed")
        return False
    
    def run_all_tests(self) -> bool:
        """Run all coordination tests"""
        print("🚀 Running Multi-Instance Coordination Tests")
        print("=" * 50)
        
        tests = [
            self.test_worktree_isolation,
            self.test_shared_workspace,
            self.test_agent_registration,
            self.test_message_coordination
        ]
        
        passed = 0
        for test in tests:
            if test():
                passed += 1
            else:
                print(f"\n❌ Test failed: {test.__name__}")
        
        print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
        
        if passed == len(tests):
            print("🎉 All coordination tests passed!")
            return True
        else:
            print("❌ Some coordination tests failed")
            return False

if __name__ == "__main__":
    import sys
    base_dir = sys.argv[1] if len(sys.argv) > 1 else "/tmp/mcp-agent-workspaces"
    
    tester = CoordinationTest(base_dir)
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
    
    chmod +x "$BASE_DIR/test-coordination.py"
    print_success "Created coordination test script"
    echo
}

print_summary() {
    print_header "Setup Complete!"
    
    echo -e "${GREEN}✅ Git worktrees created for all agents${NC}"
    echo -e "${GREEN}✅ Shared workspace configured${NC}"
    echo -e "${GREEN}✅ Agent launch scripts ready${NC}"
    echo -e "${GREEN}✅ Coordination test available${NC}"
    echo
    
    echo -e "${BLUE}📁 Workspace Structure:${NC}"
    echo "   $BASE_DIR/"
    echo "   ├── backend-agent-workspace/     # Backend agent workspace"
    echo "   ├── frontend-agent-workspace/    # Frontend agent workspace" 
    echo "   ├── devops-agent-workspace/      # DevOps agent workspace"
    echo "   ├── testing-agent-workspace/     # Testing agent workspace"
    echo "   ├── shared-workspace/            # Shared coordination space"
    echo "   └── test-coordination.py         # Coordination test script"
    echo
    
    echo -e "${BLUE}🚀 Next Steps:${NC}"
    echo "1. Test the setup:"
    echo "   cd $BASE_DIR && python3 test-coordination.py"
    echo
    echo "2. Launch agents (in separate terminals):"
    for agent in "${!AGENTS[@]}"; do
        echo "   cd $BASE_DIR/$agent-workspace && ./launch-agent.sh"
    done
    echo
    echo "3. Monitor coordination:"
    echo "   watch 'cat $BASE_DIR/shared-workspace/coordination/agent-registry.json'"
    echo
}

# Main execution
main() {
    print_header "Multi-Instance Git Worktree Setup"
    echo "Setting up coordination demo for Claude Code agents..."
    echo
    
    cleanup_existing
    setup_base_directory  
    create_worktrees
    create_shared_workspace
    create_demo_scripts
    create_coordination_test
    print_summary
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "This script must be run from within a git repository"
    exit 1
fi

main 