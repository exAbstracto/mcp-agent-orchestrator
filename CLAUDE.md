# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-Agent Development System - A sophisticated system that coordinates multiple AI coding assistants (Cursor and Claude Code) as a unified development team using Model Context Protocol (MCP).

**Key Technologies:**
- Python (primary) with async/await patterns
- Node.js for MCP server implementations  
- MCP (Model Context Protocol) for agent communication
- pytest for testing with 85% minimum coverage requirement
- GNU Make for build automation

## Essential Commands

### Development Setup
```bash
make dev-setup         # Complete development environment setup
make install           # Install all dependencies
make install-dev       # Install dev dependencies (pytest, black, flake8, mypy)
```

### Testing Commands (ALWAYS run before committing)
```bash
make test              # Run all tests
make test-coverage     # Run tests with coverage report
make test-us007        # Run US-007 channel management tests
make lint              # Run flake8 linting
make type-check        # Run mypy type checking
make format            # Format code with black
make ci-check          # Full CI pipeline (clean + lint + type-check + test)
```

### Running MCP Servers
```bash
make message-queue-demo        # Run message queue demonstration
make task-coordinator-demo     # Run task coordinator demo
make demo-comprehensive        # Run comprehensive coordination test
make health-check             # Check health of all MCP servers
```

### Single Test Execution
```bash
# Run specific test file
cd mcp-servers/message-queue && ./venv/bin/python -m pytest tests/test_specific.py -v

# Run specific test function
cd mcp-servers/task-coordinator && ./venv/bin/python -m pytest tests/test_file.py::test_function -v
```

## High-Level Architecture

### Core Components

1. **MCP Servers** (`mcp-servers/`)
   - **message-queue/**: Async pub/sub messaging system (US-003)
   - **task-coordinator/**: Task dependency management (US-006)
   - **template/**: Basic MCP server template for new services
   - Each server has its own virtual environment

2. **Coordination Demo** (`coordination-demo/`)
   - Demonstrates multi-agent coordination capabilities
   - Git worktree setup for Claude Code instances
   - Shared workspace for file exchange between agents

3. **Agent Framework** (planned)
   - Base classes for specialized AI agents
   - MCP client implementation
   - State management and communication layers

### Key Design Patterns

1. **Event-Driven Architecture**
   - All agent communication is asynchronous
   - Message Queue server handles pub/sub patterns
   - Channel-based communication (US-007)

2. **Task Dependency Management**
   - Directed Acyclic Graph (DAG) for task dependencies
   - Automatic dependency resolution
   - Status tracking: PENDING → IN_PROGRESS → COMPLETED/FAILED

3. **Platform Abstraction**
   - Core infrastructure is platform-agnostic
   - Cursor: Limited to 40 tools, GUI-based
   - Claude Code: Unlimited tools, CLI-based, better for backend/automation

### Testing Strategy

1. **Test-Driven Development (TDD)**
   - Write tests first (Red phase)
   - Implement minimum code (Green phase)  
   - Refactor while keeping tests passing
   - **CRITICAL**: 85% minimum coverage required

2. **Test Markers**
   - `@pytest.mark.us003` - Message Queue tests
   - `@pytest.mark.us006` - Task Coordinator tests
   - `@pytest.mark.us007` - Channel Management tests
   - `@pytest.mark.coordination` - Multi-agent tests

3. **Virtual Environment Usage**
   - **ALWAYS** activate the appropriate venv before running Python code
   - Each MCP server has its own venv to avoid dependency conflicts
   - Use absolute paths when calling Python from Makefile

### Important Implementation Notes

1. **Python Virtual Environments**
   - MANDATORY for all Python development
   - Each component has its own venv
   - Never use system Python directly

2. **Error Handling**
   - All MCP servers must handle protocol errors gracefully
   - Circuit breakers for fault tolerance
   - Comprehensive logging with correlation IDs

3. **Performance Considerations**
   - File operations: ~24,000 files/second
   - JSON processing: ~429,000 items/second
   - Memory usage: ~13MB per Python process
   - Use async/await for all I/O operations

4. **Git Workflow**
   - **NEVER** commit directly to main or develop branches
   - Use feature branches: `feature/`, `fix/`, `poc/`
   - Conventional commits: `feat:`, `fix:`, `test:`, `docs:`
   - Always run `make ci-check` before committing

### Current Implementation Status

**Completed:**
- ✅ US-001: Basic MCP Server Template
- ✅ US-003: Message Queue Implementation
- ✅ US-006: Task Coordinator with Dependencies
- ✅ US-007: Channel Management (in progress)

**Next Priorities:**
- Implement production message queue (Redis/RabbitMQ)
- Create base agent framework
- Develop BA/PM orchestrator agent

### MCP SDK Usage

**IMPORTANT**: Always use the official MCP Python SDK for new servers and when refactoring existing ones.

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

# Current MCP servers status:
# ✅ health-monitor/ - Uses official MCP SDK
# ✅ template/ - Uses official MCP SDK (standalone)
# ✅ message-queue/ - Uses official MCP SDK (standalone)
# ✅ task-coordinator/ - Uses official MCP SDK (standalone)
```

**Benefits of MCP SDK:**
- Better type safety and IDE support
- Consistent patterns across all servers
- Future compatibility with MCP protocol updates
- Cleaner, more maintainable code

**Test Coverage for MCP SDK Servers:**
- Target: 85% minimum coverage for business logic
- Note: MCP SDK decorator functions (@server.list_tools, @server.call_tool) cannot be easily unit tested
- Focus coverage on business logic methods, data processing, and error handling
- Current coverage: ~75-85% is typical for MCP SDK implementations due to framework code

### Working with User Stories (GitHub Issues)

User stories are managed as GitHub issues. Use the `gh` CLI to interact with them:

```bash
# List all open user stories
gh issue list --label "user-story"

# View a specific user story
gh issue view <issue-number>

# List user stories by status
gh issue list --label "in-progress"
gh issue list --label "completed"

# Create a new user story
gh issue create --title "US-XXX: Title" --label "user-story"

# Update user story status
gh issue edit <issue-number> --add-label "in-progress"
gh issue comment <issue-number> --body "Implementation started"
```

### Common Development Tasks

1. **Adding a New MCP Server**
   - Copy `mcp-servers/health-monitor/` as starting point (uses official MCP SDK)
   - Create dedicated virtual environment with `pip install mcp`
   - Implement using official MCP SDK patterns
   - Add comprehensive tests (85% coverage)
   - Update Makefile with new targets

2. **Implementing New Features**
   - Check related user story: `gh issue view <US-number>`
   - Create feature branch from develop
   - Write tests first (TDD approach)
   - Implement with clean, typed Python code and official MCP SDK
   - Run full CI check: `make ci-check`
   - Create PR with clean commit message (no automated signatures)
   - Link PR to issue: `gh pr create --body "Closes #<issue-number>"`

3. **Debugging MCP Communication**
   - Check server logs for protocol errors
   - Use correlation IDs to trace messages
   - Verify MCP protocol compliance
   - Test with `make health-check`

### Tips for Claude Code

- Use `make help` to see all available commands
- Always work within virtual environments
- Run tests frequently during development
- Use type hints for all Python functions
- Follow existing code patterns and conventions
- Check `.cursorrules` for detailed development guidelines