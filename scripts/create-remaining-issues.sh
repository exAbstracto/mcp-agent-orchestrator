#!/bin/bash

# Script to create remaining GitHub issues (US-007 through US-030)
echo "Creating remaining GitHub issues..."

# Disable pager
export GH_PAGER=""

# US-007
gh issue create --title "US-007: Message Queue - Channel Management" --body "**As an** agent  
**I want** to subscribe to specific message channels  
**So that** I only receive relevant messages

## Acceptance Criteria:
- [ ] Agents can subscribe/unsubscribe to channels
- [ ] Channel-based message routing works correctly
- [ ] Broadcast messages reach all subscribers
- [ ] Direct messages reach only intended recipient
- [ ] Channel list is discoverable

**Story Points:** 3  
**Related Epic:** Core Infrastructure" --label "user-story,phase-1,priority:high,component:mcp-server,SP:3"

# US-008
gh issue create --title "US-008: Agent Health Monitoring" --body "**As a** system operator  
**I want** to monitor agent health status  
**So that** I can detect and respond to agent failures

## Acceptance Criteria:
- [ ] Agents send regular heartbeat signals
- [ ] Missing heartbeats are detected within 30 seconds
- [ ] Agent status is queryable via API
- [ ] Unhealthy agents trigger alerts
- [ ] Health history is maintained for 24 hours

**Story Points:** 3  
**Related Epic:** Core Infrastructure" --label "user-story,phase-1,priority:high,component:infrastructure,SP:3"

# US-009
gh issue create --title "US-009: Shared Workspace - File Locking" --body "**As a** developer agent  
**I want** to lock files while editing  
**So that** other agents don't create conflicts

## Acceptance Criteria:
- [ ] File locks can be acquired and released
- [ ] Lock requests include timeout duration
- [ ] Concurrent lock attempts are queued
- [ ] Stale locks are cleaned up automatically
- [ ] Lock status is visible to all agents

**Story Points:** 5  
**Related Epic:** Core Infrastructure" --label "user-story,phase-1,priority:medium,component:mcp-server,SP:5"

# US-010
gh issue create --title "US-010: Centralized Logging System" --body "**As a** system operator  
**I want** centralized logging from all components  
**So that** I can debug issues across the system

## Acceptance Criteria:
- [ ] All MCP servers send logs to central location
- [ ] Logs include correlation IDs for tracing
- [ ] Log levels are configurable
- [ ] Logs are searchable by various criteria
- [ ] Log retention is at least 7 days

**Story Points:** 3  
**Related Epic:** Core Infrastructure" --label "user-story,phase-1,priority:medium,component:infrastructure,SP:3"

# US-011
gh issue create --title "US-011: BA/PM Agent - Task Creation" --body "**As a** BA/PM agent  
**I want** to create tasks from user requirements  
**So that** development work can begin

## Acceptance Criteria:
- [ ] Can parse user requirements into tasks
- [ ] Tasks are created with appropriate metadata
- [ ] Dependencies are identified automatically
- [ ] Tasks are assigned based on agent capabilities
- [ ] Sprint planning view is available

**Story Points:** 5  
**Related Epic:** Essential Agents" --label "user-story,phase-2,priority:high,component:agent,SP:5"

# US-012
gh issue create --title "US-012: Backend Developer Agent - API Generation" --body "**As a** backend developer agent  
**I want** to generate API endpoints from specifications  
**So that** backend services can be implemented quickly

## Acceptance Criteria:
- [ ] Can generate RESTful API code from OpenAPI spec
- [ ] Generated code follows project standards
- [ ] Basic CRUD operations are implemented
- [ ] Error handling is included
- [ ] Unit tests are generated

**Story Points:** 8  
**Related Epic:** Essential Agents" --label "user-story,phase-2,priority:high,component:agent,SP:8"

# US-013
gh issue create --title "US-013: Frontend Developer Agent - Component Generation" --body "**As a** frontend developer agent  
**I want** to generate UI components from requirements  
**So that** user interfaces can be built efficiently

## Acceptance Criteria:
- [ ] Can generate React/Vue/Angular components
- [ ] Components follow design system guidelines
- [ ] Responsive design is implemented
- [ ] Accessibility standards are met
- [ ] Component tests are included

**Story Points:** 8  
**Related Epic:** Essential Agents" --label "user-story,phase-2,priority:high,component:agent,SP:8"

# US-014
gh issue create --title "US-014: DevOps Agent - Deployment Automation" --body "**As a** DevOps agent  
**I want** to automate deployment processes  
**So that** code can be deployed reliably

## Acceptance Criteria:
- [ ] Can generate deployment scripts
- [ ] Environment configurations are managed
- [ ] CI/CD pipelines are created
- [ ] Rollback procedures are defined
- [ ] Deployment status is monitored

**Story Points:** 5  
**Related Epic:** Essential Agents" --label "user-story,phase-2,priority:medium,component:agent,SP:5"

# US-015
gh issue create --title "US-015: Agent Handoff Protocol" --body "**As an** agent  
**I want** to hand off work to other agents  
**So that** complex tasks can be completed collaboratively

## Acceptance Criteria:
- [ ] Handoff includes context and artifacts
- [ ] Receiving agent acknowledges handoff
- [ ] Handoff history is maintained
- [ ] Failed handoffs are retried
- [ ] Handoff status is trackable

**Story Points:** 5  
**Related Epic:** Essential Agents" --label "user-story,phase-2,priority:medium,component:infrastructure,SP:5"

echo "Phase 1 and 2 issues created. Continuing with Phase 3..."

# US-016
gh issue create --title "US-016: Backend Test Generation" --body "**As a** backend tester agent  
**I want** to generate comprehensive test suites  
**So that** backend code quality is ensured

## Acceptance Criteria:
- [ ] Unit tests achieve 85% code coverage
- [ ] Integration tests verify API contracts
- [ ] Performance tests measure response times
- [ ] Database integrity tests are included
- [ ] Test reports are generated automatically

**Story Points:** 8  
**Related Epic:** Testing Suite" --label "user-story,phase-3,priority:high,component:agent,SP:8"

# US-017
gh issue create --title "US-017: Frontend Test Automation" --body "**As a** frontend tester agent  
**I want** to automate UI testing  
**So that** frontend quality is maintained

## Acceptance Criteria:
- [ ] Component tests verify functionality
- [ ] Visual regression tests catch UI changes
- [ ] Accessibility tests ensure compliance
- [ ] Cross-browser tests run automatically
- [ ] Test results are integrated with CI/CD

**Story Points:** 8  
**Related Epic:** Testing Suite" --label "user-story,phase-3,priority:high,component:agent,SP:8"

# US-018
gh issue create --title "US-018: E2E Test Scenarios" --body "**As an** E2E tester agent  
**I want** to create end-to-end test scenarios  
**So that** complete user workflows are validated

## Acceptance Criteria:
- [ ] Critical user journeys are identified
- [ ] Test scenarios cover happy paths
- [ ] Edge cases are tested
- [ ] Test data is managed properly
- [ ] Tests run in multiple environments

**Story Points:** 5  
**Related Epic:** Testing Suite" --label "user-story,phase-3,priority:high,component:testing,SP:5"

# US-019
gh issue create --title "US-019: Test Result Aggregation" --body "**As a** QA manager  
**I want** aggregated test results from all agents  
**So that** I can assess overall quality

## Acceptance Criteria:
- [ ] Test results from all agents are collected
- [ ] Unified test report is generated
- [ ] Quality metrics are calculated
- [ ] Trends are visualized
- [ ] Failed tests trigger notifications

**Story Points:** 3  
**Related Epic:** Testing Suite" --label "user-story,phase-3,priority:medium,component:testing,SP:3"

# US-020
gh issue create --title "US-020: Documentation Synchronization" --body "**As a** developer  
**I want** documentation to stay synchronized with code  
**So that** documentation is always accurate

## Acceptance Criteria:
- [ ] Code changes trigger doc updates
- [ ] Documentation versions match code versions
- [ ] Change notifications are sent to relevant agents
- [ ] Documentation validation rules are enforced
- [ ] Merge conflicts in docs are handled

**Story Points:** 5  
**Related Epic:** Testing Suite" --label "user-story,phase-3,priority:medium,documentation,SP:5"

echo "Phase 3 issues created. Continuing with Phase 4..."

# US-021
gh issue create --title "US-021: Security Vulnerability Scanning" --body "**As a** security tester agent  
**I want** to scan code for vulnerabilities  
**So that** security issues are found early

## Acceptance Criteria:
- [ ] SAST tools are integrated
- [ ] Dependency vulnerabilities are checked
- [ ] Security best practices are verified
- [ ] Compliance requirements are validated
- [ ] Security reports include remediation steps

**Story Points:** 8  
**Related Epic:** Advanced Features" --label "user-story,phase-4,priority:high,component:agent,SP:8"

# US-022
gh issue create --title "US-022: Intelligent Conflict Resolution" --body "**As an** agent  
**I want** smart conflict resolution  
**So that** merge conflicts are minimized

## Acceptance Criteria:
- [ ] Semantic understanding of code changes
- [ ] Automatic resolution of simple conflicts
- [ ] Complex conflicts escalated appropriately
- [ ] Resolution history is maintained
- [ ] Conflict patterns are learned

**Story Points:** 13  
**Related Epic:** Advanced Features" --label "user-story,phase-4,priority:high,component:infrastructure,SP:13"

# US-023
gh issue create --title "US-023: Performance Auto-Scaling" --body "**As a** system operator  
**I want** automatic resource scaling  
**So that** the system handles varying loads

## Acceptance Criteria:
- [ ] Resource usage is monitored continuously
- [ ] Scaling triggers are configurable
- [ ] New agent instances spawn automatically
- [ ] Load is balanced across instances
- [ ] Scaling events are logged

**Story Points:** 8  
**Related Epic:** Advanced Features" --label "user-story,phase-4,priority:medium,component:infrastructure,SP:8"

# US-024
gh issue create --title "US-024: Productivity Analytics" --body "**As a** project manager  
**I want** productivity metrics and insights  
**So that** I can optimize team performance

## Acceptance Criteria:
- [ ] Task completion rates are tracked
- [ ] Agent efficiency is measured
- [ ] Bottlenecks are identified
- [ ] Trends are visualized
- [ ] Recommendations are generated

**Story Points:** 5  
**Related Epic:** Advanced Features" --label "user-story,phase-4,priority:medium,component:infrastructure,SP:5"

# US-025
gh issue create --title "US-025: Real-time Dashboard" --body "**As a** system operator  
**I want** a real-time monitoring dashboard  
**So that** I can oversee system operations

## Acceptance Criteria:
- [ ] Agent status displayed in real-time
- [ ] Task progress is visualized
- [ ] System metrics are shown
- [ ] Alerts are prominent
- [ ] Dashboard is responsive

**Story Points:** 5  
**Related Epic:** Advanced Features" --label "user-story,phase-4,priority:low,component:infrastructure,SP:5"

echo "Phase 4 issues created. Continuing with Phase 5..."

# US-026
gh issue create --title "US-026: Authentication System" --body "**As a** system administrator  
**I want** secure authentication for all components  
**So that** the system is protected from unauthorized access

## Acceptance Criteria:
- [ ] JWT-based authentication implemented
- [ ] Agent certificates are managed
- [ ] Token rotation is automatic
- [ ] Failed auth attempts are logged
- [ ] Multi-factor auth is supported

**Story Points:** 8  
**Related Epic:** Production Readiness" --label "user-story,phase-5,priority:high,component:infrastructure,SP:8"

# US-027
gh issue create --title "US-027: Load Testing Suite" --body "**As a** performance engineer  
**I want** comprehensive load tests  
**So that** system scalability is validated

## Acceptance Criteria:
- [ ] Simulate 10+ concurrent agents
- [ ] Measure response times under load
- [ ] Identify performance bottlenecks
- [ ] Test resource limits
- [ ] Generate performance reports

**Story Points:** 5  
**Related Epic:** Production Readiness" --label "user-story,phase-5,priority:high,component:testing,SP:5"

# US-028
gh issue create --title "US-028: Disaster Recovery Implementation" --body "**As a** system administrator  
**I want** disaster recovery procedures  
**So that** the system can recover from failures

## Acceptance Criteria:
- [ ] Automated backup procedures run daily
- [ ] Recovery procedures are documented
- [ ] Failover mechanisms are tested
- [ ] Recovery time < 5 minutes
- [ ] Data integrity is maintained

**Story Points:** 8  
**Related Epic:** Production Readiness" --label "user-story,phase-5,priority:high,component:infrastructure,SP:8"

# US-029
gh issue create --title "US-029: Operations Documentation" --body "**As an** operations engineer  
**I want** comprehensive operational documentation  
**So that** the system can be maintained effectively

## Acceptance Criteria:
- [ ] Deployment procedures are documented
- [ ] Troubleshooting guides are complete
- [ ] Monitoring setup is explained
- [ ] Maintenance schedules are defined
- [ ] Runbooks cover common scenarios

**Story Points:** 5  
**Related Epic:** Production Readiness" --label "user-story,phase-5,priority:medium,documentation,SP:5"

# US-030
gh issue create --title "US-030: Production Integration Testing" --body "**As a** release manager  
**I want** full integration tests in production-like environment  
**So that** releases are reliable

## Acceptance Criteria:
- [ ] Test environment mirrors production
- [ ] All agent types are tested together
- [ ] Real-world scenarios are simulated
- [ ] Performance meets requirements
- [ ] No critical issues found

**Story Points:** 8  
**Related Epic:** Production Readiness" --label "user-story,phase-5,priority:medium,component:testing,SP:8"

echo "✓ All remaining user stories have been created as GitHub issues!"
echo "View all issues at: https://github.com/exAbstracto/mcp-agent-orchestrator/issues" 