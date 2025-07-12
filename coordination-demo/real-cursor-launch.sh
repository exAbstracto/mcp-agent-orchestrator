#!/bin/bash
"""
Real Multi-Instance Cursor Launch Demo

This script launches ACTUAL Cursor instances with different configurations
and demonstrates REAL communication between them.
"""

set -e

# Configuration
BASE_DIR="/tmp/real-cursor-instances"
PROJECT_ROOT=$(pwd)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

cleanup_existing() {
    print_header "Cleaning Up Existing Instances"
    
    # Kill any existing Cursor instances
    pkill -f "cursor.*user-data-dir.*real-cursor-instances" 2>/dev/null || true
    
    # Remove old directories
    [ -d "$BASE_DIR" ] && rm -rf "$BASE_DIR"
    
    print_success "Cleanup complete"
    echo
}

setup_instance() {
    local instance_name=$1
    local role=$2
    local port=$3
    
    local instance_dir="$BASE_DIR/$instance_name"
    local workspace_dir="$instance_dir/workspace"
    local user_data_dir="$instance_dir/user-data"
    
    print_header "Setting up $instance_name ($role)"
    
    # Create directories
    mkdir -p "$instance_dir"/{workspace,user-data,messages/{inbox,outbox}}
    
    # Create a unique project for this instance
    cp -r "$PROJECT_ROOT" "$workspace_dir/project"
    
    # Create instance-specific files
    cat > "$workspace_dir/agent-config.json" << EOF
{
    "agent_id": "$instance_name",
    "role": "$role",
    "port": $port,
    "workspace": "$workspace_dir",
    "shared_workspace": "$BASE_DIR/shared-workspace",
    "created_at": "$(date -Iseconds)"
}
EOF

    # Create communication script for this instance
    cat > "$workspace_dir/send-message.py" << EOF
#!/usr/bin/env python3
"""
Real-time message sender for $instance_name
"""
import json
import os
import datetime
import sys

def send_message(to_agent, message_type, content):
    shared_workspace = "$BASE_DIR/shared-workspace"
    messages_dir = os.path.join(shared_workspace, "messages")
    os.makedirs(messages_dir, exist_ok=True)
    
    message = {
        "from": "$instance_name",
        "to": to_agent,
        "type": message_type,
        "content": content,
        "timestamp": datetime.datetime.now().isoformat(),
        "workspace": "$workspace_dir"
    }
    
    # Save message
    msg_file = os.path.join(messages_dir, f"{to_agent}_from_{message['from']}_{datetime.datetime.now().strftime('%H%M%S')}.json")
    with open(msg_file, 'w') as f:
        json.dump(message, f, indent=2)
    
    print(f"📧 Message sent from $instance_name to {to_agent}")
    print(f"📄 Saved to: {msg_file}")
    return msg_file

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 send-message.py <to_agent> <message_type> <content>")
        sys.exit(1)
    
    to_agent = sys.argv[1]
    message_type = sys.argv[2]
    content = " ".join(sys.argv[3:])
    
    send_message(to_agent, message_type, content)
EOF

    # Create message checker for this instance
    cat > "$workspace_dir/check-messages.py" << EOF
#!/usr/bin/env python3
"""
Real-time message checker for $instance_name
"""
import json
import os
import glob
from datetime import datetime

def check_messages():
    shared_workspace = "$BASE_DIR/shared-workspace"
    messages_dir = os.path.join(shared_workspace, "messages")
    
    if not os.path.exists(messages_dir):
        print("📭 No messages directory found")
        return []
    
    # Find messages for this agent
    pattern = os.path.join(messages_dir, f"$instance_name_from_*.json")
    message_files = glob.glob(pattern)
    
    messages = []
    for msg_file in sorted(message_files):
        try:
            with open(msg_file, 'r') as f:
                message = json.load(f)
                messages.append((msg_file, message))
        except Exception as e:
            print(f"❌ Error reading {msg_file}: {e}")
    
    return messages

if __name__ == "__main__":
    print(f"📬 Checking messages for $instance_name...")
    messages = check_messages()
    
    if not messages:
        print("📭 No messages found")
    else:
        print(f"📧 Found {len(messages)} messages:")
        for msg_file, message in messages:
            print(f"  📄 From: {message['from']}")
            print(f"  📝 Type: {message['type']}")
            print(f"  💬 Content: {message['content']}")
            print(f"  🕒 Time: {message['timestamp']}")
            print()
EOF

    # Create workspace files specific to this role
    case $role in
        "frontend")
            cat > "$workspace_dir/frontend-task.md" << EOF
# Frontend Agent Tasks

## Current Assignment
- Design user interface components
- Create React components
- Handle CSS styling
- Integrate with API endpoints

## Communication Commands
\`\`\`bash
# Send message to backend
python3 send-message.py backend-agent "api-request" "Need user endpoints for dashboard"

# Check for messages
python3 check-messages.py
\`\`\`

## Files to Work On
- src/components/UserDashboard.jsx
- src/styles/dashboard.css
- src/api/userApi.js
EOF
            ;;
        "backend")
            cat > "$workspace_dir/backend-task.md" << EOF
# Backend Agent Tasks

## Current Assignment
- Develop API endpoints
- Database integration
- Authentication logic
- Performance optimization

## Communication Commands
\`\`\`bash
# Send message to frontend
python3 send-message.py frontend-agent "api-ready" "User endpoints available at /api/users"

# Check for messages
python3 check-messages.py
\`\`\`

## Files to Work On
- src/api/userEndpoints.js
- src/database/userModel.js
- src/auth/userAuth.js
EOF
            ;;
        "project-manager")
            cat > "$workspace_dir/pm-task.md" << EOF
# Project Manager Agent Tasks

## Current Assignment
- Coordinate between agents
- Track project progress
- Manage requirements
- Update documentation

## Communication Commands
\`\`\`bash
# Send message to both agents
python3 send-message.py frontend-agent "task-assignment" "Please create user dashboard component"
python3 send-message.py backend-agent "task-assignment" "Please create user API endpoints"

# Check for messages
python3 check-messages.py
\`\`\`

## Files to Work On
- project-status.md
- requirements.md
- coordination-log.md
EOF
            ;;
    esac
    
    print_success "$instance_name setup complete"
    echo "  📁 Workspace: $workspace_dir"
    echo "  🗂️  User Data: $user_data_dir"
    echo
}

launch_cursor_instance() {
    local instance_name=$1
    local role=$2
    
    local instance_dir="$BASE_DIR/$instance_name"
    local workspace_dir="$instance_dir/workspace"
    local user_data_dir="$instance_dir/user-data"
    
    print_header "Launching Real Cursor Instance: $instance_name"
    
    # Launch actual Cursor instance
    echo "🚀 Starting Cursor with command:"
    echo "   cursor --user-data-dir='$user_data_dir' '$workspace_dir'"
    
    # Launch in background
    nohup cursor --user-data-dir="$user_data_dir" "$workspace_dir" > "$instance_dir/cursor.log" 2>&1 &
    local cursor_pid=$!
    
    echo $cursor_pid > "$instance_dir/cursor.pid"
    
    print_success "Cursor instance launched (PID: $cursor_pid)"
    echo "  📋 Role: $role"
    echo "  📁 Workspace: $workspace_dir"
    echo "  📜 Log: $instance_dir/cursor.log"
    echo "  🆔 PID: $cursor_pid"
    echo
    
    # Wait a moment for launch
    sleep 2
}

setup_shared_workspace() {
    print_header "Setting up Shared Workspace"
    
    local shared_dir="$BASE_DIR/shared-workspace"
    mkdir -p "$shared_dir"/{messages,artifacts,coordination}
    
    # Create real-time coordination monitor
    cat > "$shared_dir/monitor-coordination.py" << EOF
#!/usr/bin/env python3
"""
Real-time coordination monitor
"""
import json
import os
import time
import glob
from datetime import datetime

def monitor_messages():
    messages_dir = "$shared_dir/messages"
    print("🔍 Monitoring real-time coordination...")
    print("Press Ctrl+C to stop")
    
    seen_files = set()
    
    try:
        while True:
            # Check for new messages
            if os.path.exists(messages_dir):
                message_files = glob.glob(os.path.join(messages_dir, "*.json"))
                
                for msg_file in message_files:
                    if msg_file not in seen_files:
                        seen_files.add(msg_file)
                        
                        try:
                            with open(msg_file, 'r') as f:
                                message = json.load(f)
                            
                            print(f"📧 NEW MESSAGE: {message['from']} → {message['to']}")
                            print(f"   📝 Type: {message['type']}")
                            print(f"   💬 Content: {message['content']}")
                            print(f"   🕒 Time: {message['timestamp']}")
                            print()
                        except Exception as e:
                            print(f"❌ Error reading {msg_file}: {e}")
            
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped")

if __name__ == "__main__":
    monitor_messages()
EOF

    chmod +x "$shared_dir/monitor-coordination.py"
    
    print_success "Shared workspace setup complete"
    echo "  📁 Location: $shared_dir"
    echo "  📺 Monitor: python3 $shared_dir/monitor-coordination.py"
    echo
}

show_coordination_demo() {
    print_header "Real Coordination Demo Instructions"
    
    echo "🎯 Now you have 3 REAL Cursor instances running:"
    echo "   1. Frontend Agent - UI development"
    echo "   2. Backend Agent - API development"  
    echo "   3. Project Manager - Coordination"
    echo
    echo "💬 To demonstrate REAL communication:"
    echo
    echo "1. In the Frontend Agent Cursor instance:"
    echo "   📁 Open: $BASE_DIR/frontend-agent/workspace/"
    echo "   🔧 Run: python3 send-message.py backend-agent \"api-request\" \"Need user endpoints\""
    echo
    echo "2. In the Backend Agent Cursor instance:"
    echo "   📁 Open: $BASE_DIR/backend-agent/workspace/"
    echo "   📬 Run: python3 check-messages.py"
    echo "   📤 Run: python3 send-message.py frontend-agent \"api-ready\" \"User endpoints available\""
    echo
    echo "3. Monitor real-time coordination:"
    echo "   🔍 Run: python3 $BASE_DIR/shared-workspace/monitor-coordination.py"
    echo
    echo "🎮 Each Cursor instance is completely separate with its own:"
    echo "   - User data directory"
    echo "   - Workspace"
    echo "   - Configuration"
    echo "   - Real file system"
    echo
}

main() {
    print_header "Real Multi-Instance Cursor Demo"
    
    cleanup_existing
    setup_shared_workspace
    
    # Setup instances
    setup_instance "frontend-agent" "frontend" 3001
    setup_instance "backend-agent" "backend" 3002
    setup_instance "project-manager" "project-manager" 3003
    
    # Launch actual Cursor instances
    launch_cursor_instance "frontend-agent" "frontend"
    launch_cursor_instance "backend-agent" "backend"
    launch_cursor_instance "project-manager" "project-manager"
    
    # Show demo instructions
    show_coordination_demo
    
    print_success "Real multi-instance demo is now running!"
    echo "🔍 Check running instances: ps aux | grep cursor"
    echo "🛑 Stop all instances: pkill -f 'cursor.*user-data-dir.*real-cursor-instances'"
}

main "$@" 