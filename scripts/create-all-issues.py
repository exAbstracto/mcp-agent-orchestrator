#!/usr/bin/env python3
"""
Script to create GitHub issues from user stories
Run from project root: python scripts/create-github-issues.py
"""

import subprocess
import time

# User stories data
stories = [
    # Phase 0 - Already created, will skip
    {
        "id": "US-001",
        "title": "Basic MCP Server Template",
        "skip": True  # Already created
    },
    {
        "id": "US-002", 
        "title": "Multi-Instance Coordination Demo",
        "skip": True  # Already created
    },
    {
        "id": "US-003",
        "title": "Basic Message Queue Implementation",
        "skip": True  # Already created
    },
    {
        "id": "US-004",
        "title": "Platform Capability Documentation",
        "skip": True  # Already created
    },
    {
        "id": "US-005",
        "title": "Task Coordinator - Create Task",
        "skip": True  # Already created
    },
    # Phase 1 - Remaining stories
    {
        "id": "US-006",
        "title": "Task Coordinator - Dependency Management",
        "role": "BA/PM agent",
        "want": "to manage task dependencies",
        "so_that": "work is completed in the correct order",
        "acceptance_criteria": [
            "Can define dependencies between tasks",
            "Dependency graph is validated (no cycles)",
            "Blocked tasks are identified automatically",
            "Agents are notified when dependencies are resolved",
            "Dependency visualization is available"
        ],
        "story_points": 5,
        "phase": 1,
        "priority": "high",
        "component": "mcp-server",
        "epic": "Core Infrastructure"
    },
    {
        "id": "US-007",
        "title": "Message Queue - Channel Management",
        "role": "agent",
        "want": "to subscribe to specific message channels",
        "so_that": "I only receive relevant messages",
        "acceptance_criteria": [
            "Agents can subscribe/unsubscribe to channels",
            "Channel-based message routing works correctly",
            "Broadcast messages reach all subscribers",
            "Direct messages reach only intended recipient",
            "Channel list is discoverable"
        ],
        "story_points": 3,
        "phase": 1,
        "priority": "high",
        "component": "mcp-server",
        "epic": "Core Infrastructure"
    },
    {
        "id": "US-008",
        "title": "Agent Health Monitoring",
        "role": "system operator",
        "want": "to monitor agent health status",
        "so_that": "I can detect and respond to agent failures",
        "acceptance_criteria": [
            "Agents send regular heartbeat signals",
            "Missing heartbeats are detected within 30 seconds",
            "Agent status is queryable via API",
            "Unhealthy agents trigger alerts",
            "Health history is maintained for 24 hours"
        ],
        "story_points": 3,
        "phase": 1,
        "priority": "high",
        "component": "infrastructure",
        "epic": "Core Infrastructure"
    },
    {
        "id": "US-009",
        "title": "Shared Workspace - File Locking",
        "role": "developer agent",
        "want": "to lock files while editing",
        "so_that": "other agents don't create conflicts",
        "acceptance_criteria": [
            "File locks can be acquired and released",
            "Lock requests include timeout duration",
            "Concurrent lock attempts are queued",
            "Stale locks are cleaned up automatically",
            "Lock status is visible to all agents"
        ],
        "story_points": 5,
        "phase": 1,
        "priority": "medium",
        "component": "mcp-server",
        "epic": "Core Infrastructure"
    },
    {
        "id": "US-010",
        "title": "Centralized Logging System",
        "role": "system operator",
        "want": "centralized logging from all components",
        "so_that": "I can debug issues across the system",
        "acceptance_criteria": [
            "All MCP servers send logs to central location",
            "Logs include correlation IDs for tracing",
            "Log levels are configurable",
            "Logs are searchable by various criteria",
            "Log retention is at least 7 days"
        ],
        "story_points": 3,
        "phase": 1,
        "priority": "medium",
        "component": "infrastructure",
        "epic": "Core Infrastructure"
    },
    # Phase 2
    {
        "id": "US-011",
        "title": "BA/PM Agent - Task Creation",
        "role": "BA/PM agent",
        "want": "to create tasks from user requirements",
        "so_that": "development work can begin",
        "acceptance_criteria": [
            "Can parse user requirements into tasks",
            "Tasks are created with appropriate metadata",
            "Dependencies are identified automatically",
            "Tasks are assigned based on agent capabilities",
            "Sprint planning view is available"
        ],
        "story_points": 5,
        "phase": 2,
        "priority": "high",
        "component": "agent",
        "epic": "Essential Agents"
    },
    {
        "id": "US-012",
        "title": "Backend Developer Agent - API Generation",
        "role": "backend developer agent",
        "want": "to generate API endpoints from specifications",
        "so_that": "backend services can be implemented quickly",
        "acceptance_criteria": [
            "Can generate RESTful API code from OpenAPI spec",
            "Generated code follows project standards",
            "Basic CRUD operations are implemented",
            "Error handling is included",
            "Unit tests are generated"
        ],
        "story_points": 8,
        "phase": 2,
        "priority": "high",
        "component": "agent",
        "epic": "Essential Agents"
    },
    {
        "id": "US-013",
        "title": "Frontend Developer Agent - Component Generation",
        "role": "frontend developer agent",
        "want": "to generate UI components from requirements",
        "so_that": "user interfaces can be built efficiently",
        "acceptance_criteria": [
            "Can generate React/Vue/Angular components",
            "Components follow design system guidelines",
            "Responsive design is implemented",
            "Accessibility standards are met",
            "Component tests are included"
        ],
        "story_points": 8,
        "phase": 2,
        "priority": "high",
        "component": "agent",
        "epic": "Essential Agents"
    },
    {
        "id": "US-014",
        "title": "DevOps Agent - Deployment Automation",
        "role": "DevOps agent",
        "want": "to automate deployment processes",
        "so_that": "code can be deployed reliably",
        "acceptance_criteria": [
            "Can generate deployment scripts",
            "Environment configurations are managed",
            "CI/CD pipelines are created",
            "Rollback procedures are defined",
            "Deployment status is monitored"
        ],
        "story_points": 5,
        "phase": 2,
        "priority": "medium",
        "component": "agent",
        "epic": "Essential Agents"
    },
    {
        "id": "US-015",
        "title": "Agent Handoff Protocol",
        "role": "agent",
        "want": "to hand off work to other agents",
        "so_that": "complex tasks can be completed collaboratively",
        "acceptance_criteria": [
            "Handoff includes context and artifacts",
            "Receiving agent acknowledges handoff",
            "Handoff history is maintained",
            "Failed handoffs are retried",
            "Handoff status is trackable"
        ],
        "story_points": 5,
        "phase": 2,
        "priority": "medium",
        "component": "infrastructure",
        "epic": "Essential Agents"
    },
    # Phase 3
    {
        "id": "US-016",
        "title": "Backend Test Generation",
        "role": "backend tester agent",
        "want": "to generate comprehensive test suites",
        "so_that": "backend code quality is ensured",
        "acceptance_criteria": [
            "Unit tests achieve 85% code coverage",
            "Integration tests verify API contracts",
            "Performance tests measure response times",
            "Database integrity tests are included",
            "Test reports are generated automatically"
        ],
        "story_points": 8,
        "phase": 3,
        "priority": "high",
        "component": "agent",
        "epic": "Testing Suite"
    },
    {
        "id": "US-017",
        "title": "Frontend Test Automation",
        "role": "frontend tester agent",
        "want": "to automate UI testing",
        "so_that": "frontend quality is maintained",
        "acceptance_criteria": [
            "Component tests verify functionality",
            "Visual regression tests catch UI changes",
            "Accessibility tests ensure compliance",
            "Cross-browser tests run automatically",
            "Test results are integrated with CI/CD"
        ],
        "story_points": 8,
        "phase": 3,
        "priority": "high",
        "component": "agent",
        "epic": "Testing Suite"
    },
    {
        "id": "US-018",
        "title": "E2E Test Scenarios",
        "role": "E2E tester agent",
        "want": "to create end-to-end test scenarios",
        "so_that": "complete user workflows are validated",
        "acceptance_criteria": [
            "Critical user journeys are identified",
            "Test scenarios cover happy paths",
            "Edge cases are tested",
            "Test data is managed properly",
            "Tests run in multiple environments"
        ],
        "story_points": 5,
        "phase": 3,
        "priority": "high",
        "component": "testing",
        "epic": "Testing Suite"
    },
    {
        "id": "US-019",
        "title": "Test Result Aggregation",
        "role": "QA manager",
        "want": "aggregated test results from all agents",
        "so_that": "I can assess overall quality",
        "acceptance_criteria": [
            "Test results from all agents are collected",
            "Unified test report is generated",
            "Quality metrics are calculated",
            "Trends are visualized",
            "Failed tests trigger notifications"
        ],
        "story_points": 3,
        "phase": 3,
        "priority": "medium",
        "component": "testing",
        "epic": "Testing Suite"
    },
    {
        "id": "US-020",
        "title": "Documentation Synchronization",
        "role": "developer",
        "want": "documentation to stay synchronized with code",
        "so_that": "documentation is always accurate",
        "acceptance_criteria": [
            "Code changes trigger doc updates",
            "Documentation versions match code versions",
            "Change notifications are sent to relevant agents",
            "Documentation validation rules are enforced",
            "Merge conflicts in docs are handled"
        ],
        "story_points": 5,
        "phase": 3,
        "priority": "medium",
        "component": "documentation",
        "epic": "Testing Suite"
    },
    # Phase 4
    {
        "id": "US-021",
        "title": "Security Vulnerability Scanning",
        "role": "security tester agent",
        "want": "to scan code for vulnerabilities",
        "so_that": "security issues are found early",
        "acceptance_criteria": [
            "SAST tools are integrated",
            "Dependency vulnerabilities are checked",
            "Security best practices are verified",
            "Compliance requirements are validated",
            "Security reports include remediation steps"
        ],
        "story_points": 8,
        "phase": 4,
        "priority": "high",
        "component": "agent",
        "epic": "Advanced Features"
    },
    {
        "id": "US-022",
        "title": "Intelligent Conflict Resolution",
        "role": "agent",
        "want": "smart conflict resolution",
        "so_that": "merge conflicts are minimized",
        "acceptance_criteria": [
            "Semantic understanding of code changes",
            "Automatic resolution of simple conflicts",
            "Complex conflicts escalated appropriately",
            "Resolution history is maintained",
            "Conflict patterns are learned"
        ],
        "story_points": 13,
        "phase": 4,
        "priority": "high",
        "component": "infrastructure",
        "epic": "Advanced Features"
    },
    {
        "id": "US-023",
        "title": "Performance Auto-Scaling",
        "role": "system operator",
        "want": "automatic resource scaling",
        "so_that": "the system handles varying loads",
        "acceptance_criteria": [
            "Resource usage is monitored continuously",
            "Scaling triggers are configurable",
            "New agent instances spawn automatically",
            "Load is balanced across instances",
            "Scaling events are logged"
        ],
        "story_points": 8,
        "phase": 4,
        "priority": "medium",
        "component": "infrastructure",
        "epic": "Advanced Features"
    },
    {
        "id": "US-024",
        "title": "Productivity Analytics",
        "role": "project manager",
        "want": "productivity metrics and insights",
        "so_that": "I can optimize team performance",
        "acceptance_criteria": [
            "Task completion rates are tracked",
            "Agent efficiency is measured",
            "Bottlenecks are identified",
            "Trends are visualized",
            "Recommendations are generated"
        ],
        "story_points": 5,
        "phase": 4,
        "priority": "medium",
        "component": "infrastructure",
        "epic": "Advanced Features"
    },
    {
        "id": "US-025",
        "title": "Real-time Dashboard",
        "role": "system operator",
        "want": "a real-time monitoring dashboard",
        "so_that": "I can oversee system operations",
        "acceptance_criteria": [
            "Agent status displayed in real-time",
            "Task progress is visualized",
            "System metrics are shown",
            "Alerts are prominent",
            "Dashboard is responsive"
        ],
        "story_points": 5,
        "phase": 4,
        "priority": "low",
        "component": "infrastructure",
        "epic": "Advanced Features"
    },
    # Phase 5
    {
        "id": "US-026",
        "title": "Authentication System",
        "role": "system administrator",
        "want": "secure authentication for all components",
        "so_that": "the system is protected from unauthorized access",
        "acceptance_criteria": [
            "JWT-based authentication implemented",
            "Agent certificates are managed",
            "Token rotation is automatic",
            "Failed auth attempts are logged",
            "Multi-factor auth is supported"
        ],
        "story_points": 8,
        "phase": 5,
        "priority": "high",
        "component": "infrastructure",
        "epic": "Production Readiness"
    },
    {
        "id": "US-027",
        "title": "Load Testing Suite",
        "role": "performance engineer",
        "want": "comprehensive load tests",
        "so_that": "system scalability is validated",
        "acceptance_criteria": [
            "Simulate 10+ concurrent agents",
            "Measure response times under load",
            "Identify performance bottlenecks",
            "Test resource limits",
            "Generate performance reports"
        ],
        "story_points": 5,
        "phase": 5,
        "priority": "high",
        "component": "testing",
        "epic": "Production Readiness"
    },
    {
        "id": "US-028",
        "title": "Disaster Recovery Implementation",
        "role": "system administrator",
        "want": "disaster recovery procedures",
        "so_that": "the system can recover from failures",
        "acceptance_criteria": [
            "Automated backup procedures run daily",
            "Recovery procedures are documented",
            "Failover mechanisms are tested",
            "Recovery time < 5 minutes",
            "Data integrity is maintained"
        ],
        "story_points": 8,
        "phase": 5,
        "priority": "high",
        "component": "infrastructure",
        "epic": "Production Readiness"
    },
    {
        "id": "US-029",
        "title": "Operations Documentation",
        "role": "operations engineer",
        "want": "comprehensive operational documentation",
        "so_that": "the system can be maintained effectively",
        "acceptance_criteria": [
            "Deployment procedures are documented",
            "Troubleshooting guides are complete",
            "Monitoring setup is explained",
            "Maintenance schedules are defined",
            "Runbooks cover common scenarios"
        ],
        "story_points": 5,
        "phase": 5,
        "priority": "medium",
        "component": "documentation",
        "epic": "Production Readiness"
    },
    {
        "id": "US-030",
        "title": "Production Integration Testing",
        "role": "release manager",
        "want": "full integration tests in production-like environment",
        "so_that": "releases are reliable",
        "acceptance_criteria": [
            "Test environment mirrors production",
            "All agent types are tested together",
            "Real-world scenarios are simulated",
            "Performance meets requirements",
            "No critical issues found"
        ],
        "story_points": 8,
        "phase": 5,
        "priority": "medium",
        "component": "testing",
        "epic": "Production Readiness"
    }
]

def create_github_issue(story):
    """Create a single GitHub issue from a story dictionary"""
    
    # Skip if marked
    if story.get("skip", False):
        print(f"⏭️  Skipping {story['id']}: {story['title']} (already created)")
        return
    
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
    print("Creating GitHub issues for remaining user stories...\n")
    
    created_count = 0
    skipped_count = 0
    
    for i, story in enumerate(stories):
        if story.get("skip", False):
            skipped_count += 1
        else:
            print(f"Creating story {i+1}/{len(stories)}...")
            create_github_issue(story)
            created_count += 1
    
    print(f"\n✓ Created {created_count} new user stories as GitHub issues!")
    print(f"⏭️  Skipped {skipped_count} already created stories")
    print(f"📊 Total: {len(stories)} user stories")
    print("\nView all issues at: https://github.com/exAbstracto/mcp-agent-orchestrator/issues")

if __name__ == "__main__":
    main() 