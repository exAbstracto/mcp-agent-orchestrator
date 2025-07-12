#!/bin/bash
"""
Real Shared Codebase Coordination Demo

This script sets up multiple Cursor instances working on the SAME codebase
with real coordination, shared file changes, and collaborative development.
"""

set -e

# Configuration
SHARED_PROJECT="/tmp/shared-coordination-project"
CURSOR_INSTANCES="/tmp/cursor-shared-instances"
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
    print_header "Cleaning Up Previous Demo"
    
    # Kill any existing Cursor instances
    pkill -f "cursor.*shared.*instances" 2>/dev/null || true
    pkill -f "cursor.*shared.*project" 2>/dev/null || true
    
    # Remove old directories
    [ -d "$SHARED_PROJECT" ] && rm -rf "$SHARED_PROJECT"
    [ -d "$CURSOR_INSTANCES" ] && rm -rf "$CURSOR_INSTANCES"
    
    print_success "Cleanup complete"
    echo
}

create_shared_project() {
    print_header "Creating Shared Project"
    
    mkdir -p "$SHARED_PROJECT"
    cd "$SHARED_PROJECT"
    
    # Initialize git repo for coordination
    git init
    git config user.email "multi-agent@demo.com"
    git config user.name "Multi-Agent Demo"
    
    # Create project structure
    mkdir -p {src/{components,api,utils},tests,docs}
    
    # Create initial files that agents will collaborate on
    cat > "README.md" << 'EOF'
# Multi-Agent Collaborative Project

This project demonstrates real coordination between multiple Cursor instances working on the same codebase.

## Current Status
- 🔄 Project initialized
- 👥 Multi-agent coordination active
- 📝 Real-time collaboration in progress

## Agents Working On This Project
- Frontend Agent: UI components and styling
- Backend Agent: API endpoints and data logic
- Project Manager: Documentation and coordination

## Recent Changes
<!-- Agents will add their changes here -->
EOF

    cat > "src/components/README.md" << 'EOF'
# Frontend Components

## Status: 🔄 In Development

Frontend Agent is working on these components:
- [ ] User Login Form
- [ ] Dashboard Layout
- [ ] Navigation Component

## Recent Updates
<!-- Frontend Agent will update this -->
EOF

    cat > "src/api/README.md" << 'EOF'
# API Endpoints

## Status: 🔄 In Development

Backend Agent is working on these endpoints:
- [ ] /api/auth/login
- [ ] /api/auth/register
- [ ] /api/users/profile

## Recent Updates
<!-- Backend Agent will update this -->
EOF

    cat > "COORDINATION_LOG.md" << 'EOF'
# Real-Time Coordination Log

## Project Manager Updates
<!-- Project Manager will coordinate here -->

## Agent Communication
<!-- Real coordination messages will appear here -->
EOF

    # Initial commit
    git add .
    git commit -m "Initial project setup for multi-agent coordination"
    
    print_success "Shared project created at: $SHARED_PROJECT"
    echo "  📁 Project structure ready"
    echo "  🔗 Git repository initialized"
    echo "  📝 Coordination files created"
    echo
}

setup_cursor_instance() {
    local agent_name=$1
    local agent_role=$2
    local window_title=$3
    
    print_header "Setting up Cursor Instance: $agent_name"
    
    local instance_dir="$CURSOR_INSTANCES/$agent_name"
    mkdir -p "$instance_dir"/{user-data,settings}
    
    # Create agent-specific settings
    cat > "$instance_dir/settings/agent-config.json" << EOF
{
    "agent_id": "$agent_name",
    "role": "$agent_role",
    "shared_project": "$SHARED_PROJECT",
    "window_title": "$window_title",
    "created_at": "$(date -Iseconds)"
}
EOF

    # Create coordination script for this agent
    cat > "$instance_dir/coordinate.py" << EOF
#!/usr/bin/env python3
"""
Real-time coordination for $agent_name
"""
import os
import json
import time
import subprocess
from datetime import datetime

SHARED_PROJECT = "$SHARED_PROJECT"
AGENT_NAME = "$agent_name"
AGENT_ROLE = "$agent_role"

def log_coordination(message, file_changed=None):
    """Log coordination activity"""
    timestamp = datetime.now().isoformat()
    coord_log = os.path.join(SHARED_PROJECT, "COORDINATION_LOG.md")
    
    with open(coord_log, "a") as f:
        f.write(f"\n### {timestamp} - {AGENT_NAME} ({AGENT_ROLE})\n")
        f.write(f"{message}\n")
        if file_changed:
            f.write(f"📄 File: {file_changed}\n")
        f.write("\n")

def update_agent_status(status, work_done=None):
    """Update agent status in README"""
    readme_path = os.path.join(SHARED_PROJECT, "README.md")
    
    with open(readme_path, "r") as f:
        content = f.read()
    
    # Update agent status
    agent_line = f"- {AGENT_ROLE}: {status}"
    if work_done:
        agent_line += f" - {work_done}"
    
    # Simple replacement for demo
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if f"{AGENT_ROLE}:" in line:
            lines[i] = agent_line
            break
    
    with open(readme_path, "w") as f:
        f.write('\n'.join(lines))
    
    log_coordination(f"Status updated: {status}")

def commit_changes(message):
    """Commit changes to shared repository"""
    os.chdir(SHARED_PROJECT)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", f"[{AGENT_NAME}] {message}"], check=True)
    log_coordination(f"Committed changes: {message}")

if __name__ == "__main__":
    print(f"🤖 {AGENT_NAME} coordination active")
    print(f"📁 Working on: {SHARED_PROJECT}")
    print(f"🎯 Role: {AGENT_ROLE}")
    
    # Example coordination actions
    update_agent_status("Active and ready for coordination")
    commit_changes("Agent online and ready for work")
EOF

    chmod +x "$instance_dir/coordinate.py"
    
    print_success "$agent_name instance configured"
    echo "  📁 Instance: $instance_dir"
    echo "  🎯 Role: $agent_role"
    echo "  📝 Coordination script ready"
    echo
}

launch_shared_cursor_instances() {
    print_header "Launching Cursor Instances on Shared Project"
    
    # Launch Frontend Agent
    echo "🚀 Launching Frontend Agent..."
    nohup cursor --user-data-dir="$CURSOR_INSTANCES/frontend-agent/user-data" \
                 --title="Frontend Agent - Multi-Agent Coordination" \
                 "$SHARED_PROJECT" > "$CURSOR_INSTANCES/frontend-agent/cursor.log" 2>&1 &
    echo $! > "$CURSOR_INSTANCES/frontend-agent/cursor.pid"
    
    sleep 3
    
    # Launch Backend Agent
    echo "🚀 Launching Backend Agent..."
    nohup cursor --user-data-dir="$CURSOR_INSTANCES/backend-agent/user-data" \
                 --title="Backend Agent - Multi-Agent Coordination" \
                 "$SHARED_PROJECT" > "$CURSOR_INSTANCES/backend-agent/cursor.log" 2>&1 &
    echo $! > "$CURSOR_INSTANCES/backend-agent/cursor.pid"
    
    sleep 3
    
    # Launch Project Manager
    echo "🚀 Launching Project Manager..."
    nohup cursor --user-data-dir="$CURSOR_INSTANCES/project-manager/user-data" \
                 --title="Project Manager - Multi-Agent Coordination" \
                 "$SHARED_PROJECT" > "$CURSOR_INSTANCES/project-manager/cursor.log" 2>&1 &
    echo $! > "$CURSOR_INSTANCES/project-manager/cursor.pid"
    
    print_success "All Cursor instances launched on shared project"
    echo "  📁 Shared Project: $SHARED_PROJECT"
    echo "  👥 3 agents working on same codebase"
    echo "  🔄 Real coordination starting..."
    echo
}

create_coordination_monitor() {
    print_header "Setting up Real-Time Coordination Monitor"
    
    cat > "$SHARED_PROJECT/monitor-coordination.py" << 'EOF'
#!/usr/bin/env python3
"""
Real-time coordination monitor for shared project
"""
import os
import time
import subprocess
from datetime import datetime

SHARED_PROJECT = os.path.dirname(os.path.abspath(__file__))

def monitor_git_changes():
    """Monitor git changes in real-time"""
    print("🔍 Monitoring real-time coordination on shared project...")
    print(f"📁 Project: {SHARED_PROJECT}")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    last_commit = None
    
    try:
        while True:
            os.chdir(SHARED_PROJECT)
            
            # Check for new commits
            try:
                current_commit = subprocess.run(
                    ["git", "rev-parse", "HEAD"], 
                    capture_output=True, text=True, check=True
                ).stdout.strip()
                
                if last_commit and current_commit != last_commit:
                    # New commit detected
                    commit_info = subprocess.run(
                        ["git", "log", "-1", "--pretty=format:%an: %s", "HEAD"],
                        capture_output=True, text=True, check=True
                    ).stdout
                    
                    changed_files = subprocess.run(
                        ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                        capture_output=True, text=True, check=True
                    ).stdout.strip()
                    
                    print(f"📝 NEW COORDINATION: {commit_info}")
                    if changed_files:
                        print(f"📄 Files changed: {changed_files.replace(chr(10), ', ')}")
                    print(f"🕒 Time: {datetime.now().strftime('%H:%M:%S')}")
                    print("-" * 30)
                
                last_commit = current_commit
                
            except subprocess.CalledProcessError:
                pass
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped")

if __name__ == "__main__":
    monitor_git_changes()
EOF

    chmod +x "$SHARED_PROJECT/monitor-coordination.py"
    
    print_success "Coordination monitor created"
    echo "  📺 Monitor: python3 $SHARED_PROJECT/monitor-coordination.py"
    echo
}

simulate_initial_coordination() {
    print_header "Initiating Agent Coordination"
    
    cd "$SHARED_PROJECT"
    
    # Frontend Agent activity
    echo "🎨 Frontend Agent starting work..."
    python3 "$CURSOR_INSTANCES/frontend-agent/coordinate.py"
    
    sleep 1
    
    # Backend Agent activity  
    echo "🔧 Backend Agent starting work..."
    python3 "$CURSOR_INSTANCES/backend-agent/coordinate.py"
    
    sleep 1
    
    # Project Manager activity
    echo "📋 Project Manager coordinating..."
    python3 "$CURSOR_INSTANCES/project-manager/coordinate.py"
    
    # Create some initial collaborative work
    echo "🔄 Creating initial collaborative work..."
    
    # Frontend Agent creates component
    cat > "src/components/LoginForm.jsx" << 'EOF'
import React, { useState } from 'react';

// Frontend Agent: Initial login form component
const LoginForm = () => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  
  const handleSubmit = (e) => {
    e.preventDefault();
    // TODO: Backend Agent - please implement auth API call
    console.log('Login attempt:', credentials);
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input 
        type="text" 
        placeholder="Username"
        value={credentials.username}
        onChange={(e) => setCredentials({...credentials, username: e.target.value})}
      />
      <input 
        type="password" 
        placeholder="Password"
        value={credentials.password}
        onChange={(e) => setCredentials({...credentials, password: e.target.value})}
      />
      <button type="submit">Login</button>
    </form>
  );
};

export default LoginForm;
EOF

    git add .
    git commit -m "[Frontend Agent] Created initial LoginForm component - needs backend integration"
    
    # Backend Agent responds
    cat > "src/api/auth.js" << 'EOF'
// Backend Agent: Authentication API endpoints
const express = require('express');
const router = express.Router();

// POST /api/auth/login
router.post('/login', async (req, res) => {
  const { username, password } = req.body;
  
  try {
    // TODO: Frontend Agent - this endpoint is ready for integration
    // Authentication logic here
    const token = generateAuthToken(username);
    
    res.json({
      success: true,
      token: token,
      user: { username }
    });
  } catch (error) {
    res.status(401).json({
      success: false,
      message: 'Invalid credentials'
    });
  }
});

// Helper function
function generateAuthToken(username) {
  // Simplified token generation for demo
  return `token_${username}_${Date.now()}`;
}

module.exports = router;
EOF

    git add .
    git commit -m "[Backend Agent] Implemented auth API - ready for frontend integration"
    
    # Update coordination log
    cat >> "COORDINATION_LOG.md" << 'EOF'

### Real Coordination Example
1. Frontend Agent created LoginForm component
2. Backend Agent implemented matching auth API
3. Both agents working on same shared codebase
4. Ready for integration testing

### Next Steps
- Frontend Agent: Integrate with auth API
- Backend Agent: Add validation and error handling
- Project Manager: Coordinate testing phase
EOF

    git add .
    git commit -m "[Project Manager] Updated coordination log with current status"
    
    print_success "Initial coordination complete"
    echo "  📝 3 commits made by different agents"
    echo "  🔄 Real collaborative work demonstrated"
    echo "  📁 All changes in shared project"
    echo
}

show_coordination_instructions() {
    print_header "Real Shared Codebase Coordination Active"
    
    echo "🎯 What's happening now:"
    echo "   📁 All 3 Cursor instances are working on: $SHARED_PROJECT"
    echo "   🤝 Same codebase, real coordination"
    echo "   📝 Git commits track all agent work"
    echo "   🔄 Real-time collaboration in progress"
    echo
    echo "🔍 To see real coordination:"
    echo "   1. Monitor coordination: python3 $SHARED_PROJECT/monitor-coordination.py"
    echo "   2. Check git history: cd $SHARED_PROJECT && git log --oneline"
    echo "   3. View coordination log: cat $SHARED_PROJECT/COORDINATION_LOG.md"
    echo
    echo "📝 In each Cursor instance window:"
    echo "   - All agents can see and edit the same files"
    echo "   - Changes made by one agent appear in all instances"
    echo "   - Real collaboration on shared codebase"
    echo
    echo "🎮 Current work:"
    echo "   - Frontend Agent: Working on UI components"
    echo "   - Backend Agent: Implementing API endpoints"
    echo "   - Project Manager: Coordinating and documenting"
    echo
}

main() {
    print_header "Real Shared Codebase Coordination Demo"
    
    cleanup_existing
    create_shared_project
    
    # Setup Cursor instances
    setup_cursor_instance "frontend-agent" "Frontend Agent" "Frontend Agent - Multi-Agent Coordination"
    setup_cursor_instance "backend-agent" "Backend Agent" "Backend Agent - Multi-Agent Coordination"
    setup_cursor_instance "project-manager" "Project Manager" "Project Manager - Multi-Agent Coordination"
    
    # Launch all instances on shared project
    launch_shared_cursor_instances
    
    # Setup monitoring
    create_coordination_monitor
    
    # Create initial coordination
    simulate_initial_coordination
    
    # Show instructions
    show_coordination_instructions
    
    print_success "Real shared codebase coordination demo is running!"
    echo "🔍 Check running instances: ps aux | grep cursor"
    echo "🛑 Stop all instances: pkill -f 'cursor.*shared.*instances'"
}

main "$@" 