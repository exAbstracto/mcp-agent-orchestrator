#!/bin/bash
# Cursor Multi-Instance Setup for Multi-Agent Coordination

set -e

BASE_DIR="/tmp/cursor-agent-instances"

echo "🚀 Setting Up Cursor Multi-Instance Demo"
echo "========================================"

# Cleanup and create base directory
rm -rf "$BASE_DIR"
mkdir -p "$BASE_DIR"

# Create frontend agent instance
mkdir -p "$BASE_DIR/frontend-agent"/{config,workspace,tools,messages/{inbox,outbox}}

cat > "$BASE_DIR/frontend-agent/config/instance-config.json" << 'EOF'
{
    "agent_id": "frontend-agent",
    "role": "frontend",
    "tool_limit": 40,
    "tool_count": 30,
    "tools": [
        "react", "vue", "css", "html", "javascript", "typescript",
        "webpack", "vite", "jest", "cypress", "storybook", "figma",
        "sass", "tailwind", "npm", "yarn", "eslint", "prettier",
        "babel", "parcel", "emotion", "styled-components", "mui",
        "chakra", "bootstrap", "d3", "gsap", "framer-motion",
        "react-query", "redux"
    ]
}
EOF

cat > "$BASE_DIR/frontend-agent/launch.sh" << 'EOF'
#!/bin/bash
echo "🚀 Starting Frontend Agent (Cursor)"
echo "📁 Workspace: $PWD/workspace"
echo "🔧 Tools: 30/40 (Frontend development focused)"
echo "⚠️  This is a simulation - actual Cursor launch would be:"
echo "   cursor --user-data-dir=$PWD/user-data $PWD/workspace"
echo "✅ Frontend agent ready for coordination"
EOF
chmod +x "$BASE_DIR/frontend-agent/launch.sh"

# Create PM agent instance  
mkdir -p "$BASE_DIR/pm-agent"/{config,workspace,tools,messages/{inbox,outbox}}

cat > "$BASE_DIR/pm-agent/config/instance-config.json" << 'EOF'
{
    "agent_id": "pm-agent", 
    "role": "project-management",
    "tool_limit": 40,
    "tool_count": 25,
    "tools": [
        "jira", "trello", "asana", "notion", "slack", "discord",
        "teams", "zoom", "calendar", "email", "github", "gitlab",
        "figma", "miro", "lucidchart", "confluence", "sharepoint",
        "google-workspace", "airtable", "monday", "linear", "clickup",
        "todoist", "harvest", "zapier"
    ]
}
EOF

cat > "$BASE_DIR/pm-agent/launch.sh" << 'EOF'
#!/bin/bash
echo "🚀 Starting PM Agent (Cursor)"
echo "📁 Workspace: $PWD/workspace"  
echo "🔧 Tools: 25/40 (Project management focused)"
echo "⚠️  This is a simulation - actual Cursor launch would be:"
echo "   cursor --user-data-dir=$PWD/user-data $PWD/workspace"
echo "✅ PM agent ready for coordination"
EOF
chmod +x "$BASE_DIR/pm-agent/launch.sh"

echo "✅ Created Cursor instance configurations"
echo "✅ Frontend Agent: 30/40 tools (under limit)"
echo "✅ PM Agent: 25/40 tools (under limit)"

echo
echo "🚀 Test the setup:"
echo "cd $BASE_DIR/frontend-agent && ./launch.sh"
echo "cd $BASE_DIR/pm-agent && ./launch.sh" 