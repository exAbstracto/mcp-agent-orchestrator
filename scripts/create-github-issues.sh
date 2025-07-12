#!/bin/bash

# Script to create GitHub issues from user stories
echo "Creating GitHub issues for user stories..."

# Create issues with a loop to avoid script being too long
create_issue() {
  local title="$1"
  local body="$2"
  local labels="$3"
  
  gh issue create --title "$title" --body "$body" --label "$labels"
}

# Phase 0 - Story 1
create_issue "US-001: Basic MCP Server Template" \
"**As a** developer  
**I want** a basic MCP server template  
**So that** I can quickly create new MCP servers following best practices

## Acceptance Criteria:
- [ ] Template includes minimal MCP protocol implementation
- [ ] Basic error handling and logging are configured
- [ ] Project structure follows MCP standards
- [ ] README with setup instructions exists
- [ ] Unit tests demonstrate basic functionality

**Story Points:** 3  
**Related Epic:** Foundation & Proof of Concept" \
"user-story,phase-0,priority:high,component:mcp-server,SP:3"

echo "Created US-001"

# Add more stories here...
echo "All user stories have been created as GitHub issues!"
