#!/usr/bin/env python3
"""
Script to create GitHub issues from user stories
Run from project root: python scripts/create-github-issues.py
"""

import subprocess
import time

# User stories data
stories = [
    # Phase 0
    {
        "id": "US-001",
        "title": "Basic MCP Server Template",
        "role": "developer",
        "want": "a basic MCP server template",
        "so_that": "I can quickly create new MCP servers following best practices",
        "acceptance_criteria": [
            "Template includes minimal MCP protocol implementation",
            "Basic error handling and logging are configured",
            "Project structure follows MCP standards",
            "README with setup instructions exists",
            "Unit tests demonstrate basic functionality"
        ],
        "story_points": 3,
        "phase": 0,
        "priority": "high",
        "component": "mcp-server",
        "epic": "Foundation & Proof of Concept"
    },
    {
        "id": "US-002",
        "title": "Multi-Instance Coordination Demo",
        "role": "system architect",
        "want": "to test coordination between multiple AI assistant instances",
        "so_that": "I can validate the multi-agent architecture approach",
        "acceptance_criteria": [
            "Successfully launch 2 Cursor instances with different configurations",
            "Demonstrate file sharing between instances",
            "Validate git worktree approach for Claude Code",
            "Document any platform-specific limitations discovered",
            "Create a simple coordination test case"
        ],
        "story_points": 5,
        "phase": 0,
        "priority": "high",
        "component": "infrastructure",
        "epic": "Foundation & Proof of Concept"
    },
    {
        "id": "US-003",
        "title": "Basic Message Queue Implementation",
        "role": "agent developer",
        "want": "a simple message passing system between agents",
        "so_that": "agents can communicate asynchronously",
        "acceptance_criteria": [
            "Basic pub/sub functionality works",
            "Messages are delivered with < 100ms latency",
            "Message delivery is reliable (no message loss)",
            "Simple test demonstrates agent-to-agent communication",
            "Performance metrics are logged"
        ],
        "story_points": 5,
        "phase": 0,
        "priority": "high",
        "component": "mcp-server",
        "epic": "Foundation & Proof of Concept"
    },
    {
        "id": "US-004",
        "title": "Platform Capability Documentation",
        "role": "developer",
        "want": "comprehensive documentation of platform capabilities and limitations",
        "so_that": "I can make informed decisions about agent assignments",
        "acceptance_criteria": [
            "Document Cursor's 40-tool limit and workarounds",
            "Document Claude Code's full MCP support",
            "Create comparison matrix of capabilities",
            "Benchmark performance differences",
            "Provide recommendations for agent-platform matching"
        ],
        "story_points": 2,
        "phase": 0,
        "priority": "medium",
        "component": "documentation",
        "epic": "Foundation & Proof of Concept"
    },
    # Phase 1
    {
        "id": "US-005",
        "title": "Task Coordinator - Create Task",
        "role": "BA/PM agent",
        "want": "to create new development tasks",
        "so_that": "work can be assigned to appropriate agents",
        "acceptance_criteria": [
            "Task creation API endpoint works",
            "Tasks include title, description, assignee, priority",
            "Task ID is generated automatically",
            "Created tasks are persisted",
            "Task creation triggers notification to assignee"
        ],
        "story_points": 3,
        "phase": 1,
        "priority": "high",
        "component": "mcp-server",
        "epic": "Core Infrastructure"
    },
    # Add remaining stories...
]

def create_github_issue(story):
    """Create a single GitHub issue from a story dictionary"""
    
    # Build the issue body
    acceptance_criteria = "\n".join([f"- [ ] {ac}" for ac in story["acceptance_criteria"]])
    
    body = f"""**As a** {story["role"]}  
**I want** {story["want"]}  
**So that** {story["so_that"]}

## Acceptance Criteria:
{acceptance_criteria}

**Story Points:** {story["story_points"]}  
**Related Epic:** {story["epic"]}"""
    
    # Build labels
    labels = [
        "user-story",
        f"phase-{story['phase']}",
        f"priority:{story['priority']}",
        f"component:{story['component']}",
        f"SP:{story['story_points']}"
    ]
    
    # Handle special case for documentation component
    if story['component'] == 'documentation':
        labels[3] = 'documentation'  # Remove 'component:' prefix for this label
    
    labels_str = ",".join(labels)
    
    # Create the issue
    title = f"{story['id']}: {story['title']}"
    
    cmd = [
        "gh", "issue", "create",
        "--title", title,
        "--body", body,
        "--label", labels_str
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Created {story['id']}: {story['title']}")
        else:
            print(f"✗ Failed to create {story['id']}: {result.stderr}")
    except Exception as e:
        print(f"✗ Error creating {story['id']}: {str(e)}")
    
    # Small delay to avoid rate limiting
    time.sleep(0.5)

def main():
    print("Creating GitHub issues for user stories...\n")
    
    for i, story in enumerate(stories):
        print(f"Creating story {i+1}/{len(stories)}...")
        create_github_issue(story)
    
    print(f"\n✓ Created {len(stories)} user stories as GitHub issues!")
    print("View them at: https://github.com/exAbstracto/mcp-agent-orchestrator/issues")

if __name__ == "__main__":
    main() 