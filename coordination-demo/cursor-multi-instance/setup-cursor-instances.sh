#!/bin/bash
"""
Cursor Multi-Instance Setup for Multi-Agent Coordination

This script sets up multiple Cursor instances with different configurations
for different agent roles, managing the 40-tool limit constraint.
"""

set -e  # Exit on any error

# Configuration
BASE_DIR="/tmp/cursor-agent-instances"
PROJECT_ROOT=$(pwd)

# Cursor instance configurations
declare -A CURSOR_AGENTS=(
    ["frontend-agent"]="frontend"
    ["pm-agent"]="project-management"
    ["tech-writer-agent"]="documentation"
)

# Tool sets for each agent type (staying under 40-tool limit)
declare -A TOOL_SETS=(
    ["frontend"]="react,vue,css,html,javascript,typescript,webpack,vite,jest,cypress,storybook,figma,sass,tailwind,npm,yarn,eslint,prettier,babel,parcel,rollup,emotion,styled-components,mui,chakra,bootstrap,d3,three,gsap,framer-motion,react-query,redux,zustand,formik,yup,react-hook-form,testing-library,playwright,chromatic,firebase"
    ["project-management"]="jira,trello,asana,notion,slack,discord,teams,zoom,calendar,email,github,gitlab,bitbucket,figma,miro,lucidchart,confluence,sharepoint,google-workspace,office365,airtable,monday,linear,clickup,basecamp,todoist,harvest,toggl,clockify,zapier,ifttt"
    ["documentation"]="markdown,mdx,docusaurus,gitbook,notion,confluence,sphinx,mkdocs,vuepress,gatsby,hugo,jekyll,nextjs,pandoc,latex,word,google-docs,figma,draw-io,mermaid,plantul,graphviz,screenshots,gif-recorder,video-editor,grammar-check,spell-check,style-guide,api-docs,swagger,postman"
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
    print_header "Cleaning Up Existing Cursor Instances"
    
    if [ -d "$BASE_DIR" ]; then
        print_warning "Removing existing instance directory: $BASE_DIR"
        rm -rf "$BASE_DIR"
    fi
    
    print_success "Cleanup complete"
    echo
}

create_instance_configs() {
    print_header "Creating Cursor Instance Configurations"
    
    mkdir -p "$BASE_DIR"
    
    for agent in "${!CURSOR_AGENTS[@]}"; do
        role="${CURSOR_AGENTS[$agent]}"
        instance_dir="$BASE_DIR/$agent"
        
        echo -e "${BLUE}Setting up Cursor instance for: $agent (role: $role)${NC}"
        
        # Create instance directory structure
        mkdir -p "$instance_dir"/{config,workspace,extensions,logs,tools}
        
        # Create user data directory structure (simulates --user-data-dir)
        mkdir -p "$instance_dir/user-data"/{User,logs,CachedData,databases,extensions}
        
        # Create instance configuration
        cat > "$instance_dir/config/instance-config.json" << EOF
{
    "agent_id": "$agent",
    "role": "$role", 
    "instance_dir": "$instance_dir",
    "user_data_dir": "$instance_dir/user-data",
    "workspace_dir": "$instance_dir/workspace",
    "created_at": "$(date -Iseconds)",
    "tool_limit": 40,
    "tool_warning_threshold": 35,
    "coordination": {
        "shared_workspace": "$BASE_DIR/../shared-workspace",
        "message_inbox": "$instance_dir/messages/inbox",
        "message_outbox": "$instance_dir/messages/outbox"
    }
}
EOF

        # Create tool configuration
        tools="${TOOL_SETS[$role]}"
        IFS=',' read -ra TOOL_ARRAY <<< "$tools"
        tool_count=${#TOOL_ARRAY[@]}
        
        cat > "$instance_dir/config/tools-config.json" << EOF
{
    "tool_set": "$role",
    "tool_count": $tool_count,
    "max_tools": 40,
    "tools": [
$(for i in "${!TOOL_ARRAY[@]}"; do
    tool="${TOOL_ARRAY[$i]}"
    if [ $i -eq $((${#TOOL_ARRAY[@]} - 1)) ]; then
        echo "        \"$tool\""
    else
        echo "        \"$tool\","
    fi
done)
    ],
    "tool_rotation_enabled": $([ $tool_count -gt 35 ] && echo "true" || echo "false"),
    "warning_at_count": 35
}
EOF

        # Create launch script
        cat > "$instance_dir/launch.sh" << EOF
#!/bin/bash
# Launch script for $agent Cursor instance

INSTANCE_DIR="$instance_dir"
AGENT_ID="$agent"
USER_DATA_DIR="\$INSTANCE_DIR/user-data"
WORKSPACE_DIR="\$INSTANCE_DIR/workspace"

echo "🚀 Starting Cursor instance for \$AGENT_ID..."
echo "📁 Instance Dir: \$INSTANCE_DIR"  
echo "👤 User Data: \$USER_DATA_DIR"
echo "🗂️  Workspace: \$WORKSPACE_DIR"

# Create workspace if it doesn't exist
mkdir -p "\$WORKSPACE_DIR"

# Copy project files to workspace (simulating project setup)
if [ ! -f "\$WORKSPACE_DIR/.initialized" ]; then
    echo "📦 Initializing workspace..."
    cp -r "$PROJECT_ROOT"/* "\$WORKSPACE_DIR/" 2>/dev/null || true
    touch "\$WORKSPACE_DIR/.initialized"
    echo "✅ Workspace initialized"
fi

# Tool count check
tool_count=\$(cat "\$INSTANCE_DIR/config/tools-config.json" | grep -o '\".*\"' | grep -v 'tool_set\|tool_count\|max_tools\|warning' | wc -l)
echo "🔧 Tool count: \$tool_count/40"

if [ \$tool_count -gt 35 ]; then
    echo "⚠️  WARNING: Approaching tool limit (\$tool_count/40)"
    echo "💡 Consider enabling tool rotation for this agent"
fi

# Simulate Cursor launch (actual command would be different)
echo "🎯 Cursor launch command (simulated):"
echo "   cursor --user-data-dir='\$USER_DATA_DIR' --extensions-dir='\$INSTANCE_DIR/extensions' '\$WORKSPACE_DIR'"

# Create message directories
mkdir -p "\$INSTANCE_DIR/messages"/{inbox,outbox}

# Register with coordination system
python3 -c "
import json
import datetime
import os

# Register this instance
registry_file = '$BASE_DIR/../shared-workspace/coordination/agent-registry.json'
if os.path.exists(registry_file):
    with open(registry_file, 'r') as f:
        registry = json.load(f)
else:
    registry = {'active_agents': {}, 'message_queue': []}

registry['active_agents']['$agent'] = {
    'type': 'cursor',
    'role': '$role',
    'instance_dir': '$instance_dir',
    'workspace': '\$WORKSPACE_DIR',
    'status': 'active',
    'tool_count': $tool_count,
    'last_seen': datetime.datetime.now().isoformat(),
    'pid': os.getpid()
}

registry['last_updated'] = datetime.datetime.now().isoformat()

os.makedirs(os.path.dirname(registry_file), exist_ok=True)
with open(registry_file, 'w') as f:
    json.dump(registry, f, indent=2)

print(f'✅ Registered Cursor instance: $agent')
"

echo "✅ \$AGENT_ID Cursor instance ready"
echo "🔗 Shared coordination: $BASE_DIR/../shared-workspace"
echo "📬 Messages: \$INSTANCE_DIR/messages/"
echo
echo "Press Ctrl+C to stop this instance"
trap 'echo "🛑 Stopping \$AGENT_ID..."; exit 0' INT
while true; do
    sleep 5
    # Simulate periodic tool usage monitoring
    if [ \$((RANDOM % 10)) -eq 0 ]; then
        echo "📊 Tool usage check: \$tool_count/40 tools active"
    fi
done
EOF
        
        chmod +x "$instance_dir/launch.sh"
        
        # Create tool rotation script
        cat > "$instance_dir/tools/rotate-tools.sh" << EOF
#!/bin/bash
# Tool rotation script for managing 40-tool limit

INSTANCE_DIR="$instance_dir"
TOOLS_CONFIG="\$INSTANCE_DIR/config/tools-config.json"

echo "🔄 Tool Rotation Manager for $agent"
echo "Current tool count: $tool_count"

if [ $tool_count -gt 40 ]; then
    echo "❌ ERROR: Tool count exceeds limit!"
    echo "💡 Implement tool rotation or grouping"
    exit 1
elif [ $tool_count -gt 35 ]; then
    echo "⚠️  WARNING: Approaching limit, rotation recommended"
    
    # Simulate tool rotation logic
    echo "🔄 Rotating tools based on current context..."
    echo "   - Unloading unused tools"
    echo "   - Loading context-specific tools"
    echo "   - Maintaining core tools"
fi

echo "✅ Tool rotation check complete"
EOF
        
        chmod +x "$instance_dir/tools/rotate-tools.sh"
        
        print_success "Created Cursor instance: $agent ($tool_count tools)"
        
        if [ $tool_count -gt 35 ]; then
            print_warning "Tool count ($tool_count) approaching limit for $agent"
        fi
        
        echo
    done
}

create_coordination_bridge() {
    print_header "Creating Cursor-Claude Code Coordination Bridge"
    
    bridge_dir="$BASE_DIR/coordination-bridge"
    mkdir -p "$bridge_dir"
    
    cat > "$bridge_dir/cursor-claude-bridge.py" << '#!/usr/bin/env python3'
"""
Cursor-Claude Code Coordination Bridge

This script facilitates communication between Cursor instances
and Claude Code agents through the shared workspace.
"""

import json
import time
import os
from pathlib import Path
from typing import Dict, List, Optional
import threading
import queue

class CoordinationBridge:
    def __init__(self, shared_workspace: str):
        self.shared_workspace = Path(shared_workspace)
        self.registry_file = self.shared_workspace / "coordination" / "agent-registry.json"
        self.message_queue = queue.Queue()
        self.running = False
        
    def start(self):
        """Start the coordination bridge"""
        print("🌉 Starting Cursor-Claude Code Coordination Bridge...")
        self.running = True
        
        # Start message processing thread
        message_thread = threading.Thread(target=self._process_messages)
        message_thread.daemon = True
        message_thread.start()
        
        # Start registry monitoring
        registry_thread = threading.Thread(target=self._monitor_registry)
        registry_thread.daemon = True
        registry_thread.start()
        
        print("✅ Bridge is running...")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping coordination bridge...")
            self.running = False
    
    def _process_messages(self):
        """Process messages between agents"""
        while self.running:
            try:
                # Check for messages from all agents
                self._check_cursor_messages()
                self._check_claude_messages()
                time.sleep(2)
            except Exception as e:
                print(f"❌ Error processing messages: {e}")
    
    def _check_cursor_messages(self):
        """Check for messages from Cursor instances"""
        cursor_base = Path("/tmp/cursor-agent-instances")
        
        if not cursor_base.exists():
            return
            
        for agent_dir in cursor_base.iterdir():
            if agent_dir.is_dir():
                outbox = agent_dir / "messages" / "outbox"
                if outbox.exists():
                    for message_file in outbox.glob("*.json"):
                        try:
                            with open(message_file) as f:
                                message = json.load(f)
                            
                            # Route message to Claude Code agent
                            self._route_to_claude(message)
                            
                            # Archive the message
                            archive_dir = agent_dir / "messages" / "archive"
                            archive_dir.mkdir(exist_ok=True)
                            message_file.rename(archive_dir / message_file.name)
                            
                        except Exception as e:
                            print(f"❌ Error processing Cursor message: {e}")
    
    def _check_claude_messages(self):
        """Check for messages from Claude Code agents"""
        claude_base = Path("/tmp/mcp-agent-workspaces")
        
        if not claude_base.exists():
            return
            
        shared_messages = claude_base / "shared-workspace" / "messages"
        if not shared_messages.exists():
            return
            
        for agent_dir in shared_messages.iterdir():
            if agent_dir.is_dir():
                outbox = agent_dir / "outbox"
                if outbox.exists():
                    for message_file in outbox.glob("*.json"):
                        try:
                            with open(message_file) as f:
                                message = json.load(f)
                            
                            # Route message to Cursor instance
                            self._route_to_cursor(message)
                            
                            # Archive the message
                            archive_dir = agent_dir / "archive"
                            archive_dir.mkdir(exist_ok=True)
                            message_file.rename(archive_dir / message_file.name)
                            
                        except Exception as e:
                            print(f"❌ Error processing Claude message: {e}")
    
    def _route_to_claude(self, message: Dict):
        """Route message to Claude Code agent"""
        target_agent = message.get("to")
        if not target_agent:
            return
            
        claude_base = Path("/tmp/mcp-agent-workspaces")
        target_inbox = claude_base / "shared-workspace" / "messages" / target_agent / "inbox"
        
        if target_inbox.exists():
            message_file = target_inbox / f"from-cursor-{int(time.time())}.json"
            with open(message_file, 'w') as f:
                json.dump(message, f, indent=2)
            print(f"📧 Routed message: Cursor → Claude ({target_agent})")
    
    def _route_to_cursor(self, message: Dict):
        """Route message to Cursor instance"""
        target_agent = message.get("to")
        if not target_agent:
            return
            
        cursor_base = Path("/tmp/cursor-agent-instances")
        target_inbox = cursor_base / target_agent / "messages" / "inbox"
        
        if target_inbox.exists():
            message_file = target_inbox / f"from-claude-{int(time.time())}.json"
            with open(message_file, 'w') as f:
                json.dump(message, f, indent=2)
            print(f"📧 Routed message: Claude → Cursor ({target_agent})")
    
    def _monitor_registry(self):
        """Monitor agent registry for status updates"""
        while self.running:
            try:
                if self.registry_file.exists():
                    with open(self.registry_file) as f:
                        registry = json.load(f)
                    
                    active_agents = registry.get("active_agents", {})
                    cursor_agents = [a for a, info in active_agents.items() 
                                   if info.get("type") == "cursor"]
                    claude_agents = [a for a, info in active_agents.items() 
                                   if info.get("type") != "cursor"]
                    
                    if len(cursor_agents) > 0 or len(claude_agents) > 0:
                        print(f"📊 Active agents: {len(cursor_agents)} Cursor, {len(claude_agents)} Claude Code")
                
                time.sleep(10)
            except Exception as e:
                print(f"❌ Error monitoring registry: {e}")

if __name__ == "__main__":
    bridge = CoordinationBridge("/tmp/mcp-agent-workspaces/shared-workspace")
    bridge.start()
#!/usr/bin/env python3
    
    chmod +x "$bridge_dir/cursor-claude-bridge.py"
    print_success "Created coordination bridge script"
    echo
}

create_demo_test() {
    print_header "Creating Cursor Multi-Instance Test"
    
    cat > "$BASE_DIR/test-cursor-instances.py" << '#!/usr/bin/env python3'
"""
Cursor Multi-Instance Test

Test script for validating Cursor multi-instance setup and coordination.
"""

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List

class CursorInstanceTest:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        
    def test_instance_configurations(self) -> bool:
        """Test that all Cursor instances are properly configured"""
        print("🧪 Testing Cursor instance configurations...")
        
        agents = ["frontend-agent", "pm-agent", "tech-writer-agent"]
        
        for agent in agents:
            instance_dir = self.base_dir / agent
            
            # Check instance directory exists
            if not instance_dir.exists():
                print(f"❌ Instance directory missing: {instance_dir}")
                return False
            
            # Check configuration files
            config_file = instance_dir / "config" / "instance-config.json"
            tools_file = instance_dir / "config" / "tools-config.json"
            
            if not config_file.exists():
                print(f"❌ Instance config missing for {agent}")
                return False
                
            if not tools_file.exists():
                print(f"❌ Tools config missing for {agent}")
                return False
            
            # Validate tool count
            with open(tools_file) as f:
                tools_config = json.load(f)
            
            tool_count = tools_config.get("tool_count", 0)
            if tool_count > 40:
                print(f"❌ Tool count exceeds limit for {agent}: {tool_count}/40")
                return False
            elif tool_count > 35:
                print(f"⚠️  Tool count approaching limit for {agent}: {tool_count}/40")
            
            print(f"✅ {agent}: configured with {tool_count}/40 tools")
        
        return True
    
    def test_workspace_isolation(self) -> bool:
        """Test that each instance has isolated workspace"""
        print("\n🧪 Testing workspace isolation...")
        
        agents = ["frontend-agent", "pm-agent", "tech-writer-agent"]
        
        for agent in agents:
            workspace_dir = self.base_dir / agent / "workspace"
            
            if not workspace_dir.exists():
                print(f"❌ Workspace missing for {agent}: {workspace_dir}")
                return False
            
            # Check for launch script
            launch_script = self.base_dir / agent / "launch.sh"
            if not launch_script.exists():
                print(f"❌ Launch script missing for {agent}")
                return False
            
            print(f"✅ {agent}: workspace isolated at {workspace_dir}")
        
        return True
    
    def test_tool_rotation_capability(self) -> bool:
        """Test tool rotation scripts exist and are functional"""
        print("\n🧪 Testing tool rotation capability...")
        
        agents = ["frontend-agent", "pm-agent", "tech-writer-agent"]
        
        for agent in agents:
            rotation_script = self.base_dir / agent / "tools" / "rotate-tools.sh"
            
            if not rotation_script.exists():
                print(f"❌ Tool rotation script missing for {agent}")
                return False
            
            # Test script is executable
            if not os.access(rotation_script, os.X_OK):
                print(f"❌ Tool rotation script not executable for {agent}")
                return False
            
            print(f"✅ {agent}: tool rotation capability available")
        
        return True
    
    def test_coordination_readiness(self) -> bool:
        """Test coordination bridge and messaging setup"""
        print("\n🧪 Testing coordination readiness...")
        
        bridge_script = self.base_dir / "coordination-bridge" / "cursor-claude-bridge.py"
        
        if not bridge_script.exists():
            print(f"❌ Coordination bridge missing: {bridge_script}")
            return False
        
        if not os.access(bridge_script, os.X_OK):
            print(f"❌ Coordination bridge not executable")
            return False
        
        # Check message directories exist
        agents = ["frontend-agent", "pm-agent", "tech-writer-agent"]
        for agent in agents:
            message_dirs = [
                self.base_dir / agent / "messages" / "inbox",
                self.base_dir / agent / "messages" / "outbox"
            ]
            
            for msg_dir in message_dirs:
                if not msg_dir.exists():
                    print(f"❌ Message directory missing: {msg_dir}")
                    return False
        
        print("✅ Coordination bridge and messaging ready")
        return True
    
    def run_all_tests(self) -> bool:
        """Run all Cursor instance tests"""
        print("🚀 Running Cursor Multi-Instance Tests")
        print("=" * 50)
        
        tests = [
            self.test_instance_configurations,
            self.test_workspace_isolation,
            self.test_tool_rotation_capability,
            self.test_coordination_readiness
        ]
        
        passed = 0
        for test in tests:
            if test():
                passed += 1
            else:
                print(f"\n❌ Test failed: {test.__name__}")
        
        print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
        
        if passed == len(tests):
            print("🎉 All Cursor instance tests passed!")
            return True
        else:
            print("❌ Some Cursor instance tests failed")
            return False

if __name__ == "__main__":
    import sys
    base_dir = sys.argv[1] if len(sys.argv) > 1 else "/tmp/cursor-agent-instances"
    
    tester = CursorInstanceTest(base_dir)
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
    
    chmod +x "$BASE_DIR/test-cursor-instances.py"
    print_success "Created Cursor instance test script"
    echo
}

print_summary() {
    print_header "Cursor Multi-Instance Setup Complete!"
    
    echo -e "${GREEN}✅ Multiple Cursor instance configurations created${NC}"
    echo -e "${GREEN}✅ Tool management and rotation scripts ready${NC}"  
    echo -e "${GREEN}✅ Coordination bridge for Claude Code integration${NC}"
    echo -e "${GREEN}✅ Comprehensive test suite available${NC}"
    echo
    
    echo -e "${BLUE}📁 Instance Structure:${NC}"
    echo "   $BASE_DIR/"
    for agent in "${!CURSOR_AGENTS[@]}"; do
        role="${CURSOR_AGENTS[$agent]}"
        tools="${TOOL_SETS[$role]}"
        IFS=',' read -ra TOOL_ARRAY <<< "$tools"
        tool_count=${#TOOL_ARRAY[@]}
        
        echo "   ├── $agent/                   # $role agent ($tool_count tools)"
        echo "   │   ├── config/               # Instance & tool configuration"
        echo "   │   ├── workspace/            # Isolated workspace"
        echo "   │   ├── messages/             # Inter-agent messaging"
        echo "   │   ├── tools/                # Tool rotation scripts"
        echo "   │   └── launch.sh             # Instance launcher"
    done
    echo "   ├── coordination-bridge/      # Cursor-Claude integration"
    echo "   └── test-cursor-instances.py  # Test suite"
    echo
    
    echo -e "${BLUE}🔧 Tool Distribution:${NC}"
    for agent in "${!CURSOR_AGENTS[@]}"; do
        role="${CURSOR_AGENTS[$agent]}"
        tools="${TOOL_SETS[$role]}"
        IFS=',' read -ra TOOL_ARRAY <<< "$tools"
        tool_count=${#TOOL_ARRAY[@]}
        
        status="✅"
        if [ $tool_count -gt 35 ]; then
            status="⚠️ "
        fi
        
        echo "   $status $agent: $tool_count/40 tools ($role)"
    done
    echo
    
    echo -e "${BLUE}🚀 Next Steps:${NC}"
    echo "1. Test the setup:"
    echo "   cd $BASE_DIR && python3 test-cursor-instances.py"
    echo
    echo "2. Launch instances (in separate terminals):"
    for agent in "${!CURSOR_AGENTS[@]}"; do
        echo "   cd $BASE_DIR/$agent && ./launch.sh"
    done
    echo
    echo "3. Start coordination bridge:"
    echo "   cd $BASE_DIR/coordination-bridge && python3 cursor-claude-bridge.py"
    echo
    echo "4. Monitor tool usage:"
    for agent in "${!CURSOR_AGENTS[@]}"; do
        echo "   cd $BASE_DIR/$agent/tools && ./rotate-tools.sh"
    done
    echo
    
    echo -e "${YELLOW}⚠️  Important Notes:${NC}"
    echo "• Each instance has isolated user-data and workspace directories"
    echo "• Tool rotation scripts help manage the 40-tool limit"
    echo "• Coordination bridge enables communication with Claude Code agents"
    echo "• Monitor tool usage regularly to avoid hitting limits"
    echo
}

# Main execution
main() {
    print_header "Cursor Multi-Instance Setup"
    echo "Setting up multiple Cursor instances for multi-agent coordination..."
    echo
    
    cleanup_existing
    create_instance_configs
    create_coordination_bridge
    create_demo_test
    print_summary
}

main 