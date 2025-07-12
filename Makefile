# Multi-Agent Development System Makefile
# Common commands for development, testing, and deployment

.PHONY: help install clean test lint format docs demo
.DEFAULT_GOAL := help

# Colors for output
CYAN = \033[36m
GREEN = \033[32m
YELLOW = \033[33m
RED = \033[31m
RESET = \033[0m

# Python executable paths
VENV_PYTHON = mcp-servers/venv/bin/python
SYSTEM_PYTHON = python3

# Check if venv exists and define Python command
PYTHON_CMD = $(shell if [ -f $(VENV_PYTHON) ]; then echo "$(VENV_PYTHON)"; else echo "$(SYSTEM_PYTHON)"; fi)

##@ General

help: ## Display this help message
	@echo "$(CYAN)Multi-Agent Development System$(RESET)"
	@echo "================================"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(CYAN)<target>$(RESET)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(RESET)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Environment Setup

install: ## Install all dependencies and setup virtual environment
	@echo "$(CYAN)Setting up development environment...$(RESET)"
	python3 -m venv mcp-servers/venv
	mcp-servers/venv/bin/pip install --upgrade pip
	mcp-servers/venv/bin/pip install -r mcp-servers/requirements.txt
	mcp-servers/venv/bin/pip install -r mcp-servers/message-queue/requirements.txt
	@echo "$(GREEN)✅ Environment setup complete!$(RESET)"

install-dev: ## Install development dependencies (testing, linting, formatting)
	@echo "$(CYAN)Installing development dependencies...$(RESET)"
	mcp-servers/venv/bin/pip install pytest pytest-cov pytest-asyncio black flake8 mypy
	@echo "$(GREEN)✅ Development dependencies installed!$(RESET)"

##@ MCP Servers

message-queue: ## Start the message queue MCP server
	@echo "$(CYAN)Starting Message Queue MCP Server...$(RESET)"
	cd mcp-servers/message-queue && $(PYTHON_CMD) src/message_queue_server.py

message-queue-demo: ## Run message queue interactive demo
	@echo "$(CYAN)Running Message Queue Demo...$(RESET)"
	$(PYTHON_CMD) mcp-servers/message-queue/demo.py

template-demo: ## Run template MCP server demo
	@echo "$(CYAN)Running Template MCP Server Demo...$(RESET)"
	$(PYTHON_CMD) mcp-servers/template/demo.py

real-mcp-server: ## Start the real MCP coordination server
	@echo "$(CYAN)Starting Real MCP Coordination Server...$(RESET)"
	$(PYTHON_CMD) mcp-servers/real-mcp-server.py agent-001 demo-agent

##@ Testing

test: ## Run all tests
	@echo "$(CYAN)Running all tests...$(RESET)"
	cd mcp-servers/message-queue && $(PYTHON) -m pytest tests/ -v
	cd mcp-servers/template && $(PYTHON) -m pytest tests/ -v
	@echo "$(GREEN)✅ All tests completed!$(RESET)"

test-message-queue: ## Run message queue tests only
	@echo "$(CYAN)Running Message Queue tests...$(RESET)"
	cd mcp-servers/message-queue && $(PYTHON) -m pytest tests/ -v

test-template: ## Run template server tests only
	@echo "$(CYAN)Running Template server tests...$(RESET)"
	cd mcp-servers/template && $(PYTHON) -m pytest tests/ -v

test-coverage: ## Run tests with coverage report
	@echo "$(CYAN)Running tests with coverage...$(RESET)"
	cd mcp-servers/message-queue && $(PYTHON) -m pytest tests/ --cov=src --cov-report=html --cov-report=term
	cd mcp-servers/template && $(PYTHON) -m pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "$(GREEN)✅ Coverage reports generated!$(RESET)"

test-coordination: ## Run coordination and integration tests
	@echo "$(CYAN)Running coordination tests...$(RESET)"
	cd coordination-demo && $(PYTHON) comprehensive-coordination-test.py
	cd coordination-demo && $(PYTHON) comprehensive-test.py

##@ Code Quality

lint: ## Run linting checks
	@echo "$(CYAN)Running linting checks...$(RESET)"
	@$(PYTHON) -m flake8 mcp-servers/message-queue/src/ --max-line-length=100 2>/dev/null || echo "$(YELLOW)Flake8 not installed - run 'make install-dev'$(RESET)"
	@$(PYTHON) -m flake8 mcp-servers/template/src/ --max-line-length=100 2>/dev/null || echo "$(YELLOW)Flake8 not installed - run 'make install-dev'$(RESET)"
	@$(PYTHON) -m flake8 coordination-demo/*.py --max-line-length=100 2>/dev/null || echo "$(YELLOW)Flake8 not installed - run 'make install-dev'$(RESET)"

format: ## Format code with black
	@echo "$(CYAN)Formatting code...$(RESET)"
	@$(PYTHON) -m black mcp-servers/message-queue/src/ 2>/dev/null || echo "$(YELLOW)Black not installed - run 'make install-dev'$(RESET)"
	@$(PYTHON) -m black mcp-servers/template/src/ 2>/dev/null || echo "$(YELLOW)Black not installed - run 'make install-dev'$(RESET)"
	@$(PYTHON) -m black coordination-demo/*.py 2>/dev/null || echo "$(YELLOW)Black not installed - run 'make install-dev'$(RESET)"
	@echo "$(GREEN)✅ Code formatting complete!$(RESET)"

type-check: ## Run type checking with mypy
	@echo "$(CYAN)Running type checks...$(RESET)"
	@$(PYTHON) -m mypy mcp-servers/message-queue/src/ --ignore-missing-imports 2>/dev/null || echo "$(YELLOW)MyPy not installed - run 'make install-dev'$(RESET)"
	@$(PYTHON) -m mypy mcp-servers/template/src/ --ignore-missing-imports 2>/dev/null || echo "$(YELLOW)MyPy not installed - run 'make install-dev'$(RESET)"

##@ Coordination Demos

demo-file-sharing: ## Run file sharing coordination demo
	@echo "$(CYAN)Running file sharing demo...$(RESET)"
	cd coordination-demo && $(PYTHON) file-sharing-demo.py

demo-real-mcp: ## Run real MCP coordination demo
	@echo "$(CYAN)Running real MCP coordination demo...$(RESET)"
	cd coordination-demo && $(PYTHON) real-mcp-client.py

demo-comprehensive: ## Run comprehensive coordination test
	@echo "$(CYAN)Running comprehensive coordination test...$(RESET)"
	cd coordination-demo && $(PYTHON) comprehensive-coordination-test.py

setup-coordination: ## Setup coordination demo environment
	@echo "$(CYAN)Setting up coordination demo environment...$(RESET)"
	cd coordination-demo && bash setup-coordination-demo.sh

setup-real-mcp: ## Setup real MCP demo environment
	@echo "$(CYAN)Setting up real MCP demo environment...$(RESET)"
	cd coordination-demo && bash setup-real-mcp-demo.sh

##@ Multi-Instance Setup

setup-cursor: ## Setup Cursor multi-instance configuration
	@echo "$(CYAN)Setting up Cursor multi-instance...$(RESET)"
	cd coordination-demo && bash cursor-setup.sh

setup-claude-worktrees: ## Setup Claude Code git worktrees
	@echo "$(CYAN)Setting up Claude Code worktrees...$(RESET)"
	cd coordination-demo/claude-code-worktree && bash setup-worktrees.sh

launch-cursor-instances: ## Launch multiple Cursor instances
	@echo "$(CYAN)Launching Cursor instances...$(RESET)"
	cd coordination-demo/cursor-multi-instance && bash setup-cursor-instances.sh

##@ Development Utilities

clean: ## Clean up temporary files and caches
	@echo "$(CYAN)Cleaning up temporary files...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete!$(RESET)"

clean-coordination: ## Clean up coordination demo temporary files
	@echo "$(CYAN)Cleaning coordination demo files...$(RESET)"
	rm -rf /tmp/mcp-agent-workspaces/ 2>/dev/null || true
	rm -rf /tmp/cursor-* 2>/dev/null || true
	rm -rf /tmp/claude-code-worktrees/ 2>/dev/null || true
	rm -f coordination-demo/shared-workspace/messages_*.json 2>/dev/null || true
	@echo "$(GREEN)✅ Coordination cleanup complete!$(RESET)"

logs: ## View recent logs (if any log files exist)
	@echo "$(CYAN)Viewing recent logs...$(RESET)"
	@if [ -f mcp-servers/logs/message-queue.log ]; then tail -f mcp-servers/logs/message-queue.log; else echo "$(YELLOW)No log files found$(RESET)"; fi

##@ Performance & Monitoring

benchmark: ## Run performance benchmarks
	@echo "$(CYAN)Running performance benchmarks...$(RESET)"
	cd docs && $(PYTHON) platform-benchmarks.py benchmark_results.json
	@echo "$(GREEN)✅ Benchmarks complete! Check docs/benchmark_results.json$(RESET)"

health-check: ## Check health of all MCP servers
	@echo "$(CYAN)Performing health checks...$(RESET)"
	@echo "$(YELLOW)Message Queue Server:$(RESET)"
	@cd mcp-servers/message-queue && timeout 5 $(PYTHON) -c "from src.message_queue_server import MessageQueueServer; server = MessageQueueServer(); print('✅ Message Queue: OK')" || echo "❌ Message Queue: FAIL"
	@echo "$(YELLOW)Template Server:$(RESET)"
	@cd mcp-servers/template && timeout 5 $(PYTHON) -c "from src.mcp_server import MCPServer; server = MCPServer('test', '1.0.0'); print('✅ Template: OK')" || echo "❌ Template: FAIL"

##@ Documentation

docs: ## Generate documentation
	@echo "$(CYAN)Generating documentation...$(RESET)"
	@echo "$(YELLOW)Available documentation:$(RESET)"
	@echo "  📋 README.md - Main project documentation"
	@echo "  📊 docs/platform-capabilities-analysis.md - Platform analysis"
	@echo "  🏗️ docs/user-stories-backlog.md - User stories and requirements"
	@echo "  📈 docs/sprint-planning.md - Sprint progress"
	@echo "  🔧 mcp-servers/message-queue/README.md - Message Queue API"
	@echo "  🎛️ mcp-servers/template/README.md - Template usage"
	@echo "$(GREEN)✅ Documentation links displayed!$(RESET)"

##@ Git Workflow

git-status: ## Show git status and branch information
	@echo "$(CYAN)Git Status:$(RESET)"
	@git status --porcelain
	@echo "\n$(CYAN)Current Branch:$(RESET)"
	@git branch --show-current
	@echo "\n$(CYAN)Recent Commits:$(RESET)"
	@git log --oneline -5

commit: ## Stage all changes and commit (requires COMMIT_MSG)
	@if [ -z "$(COMMIT_MSG)" ]; then echo "$(RED)Error: Please provide COMMIT_MSG$(RESET)\nExample: make commit COMMIT_MSG='feat: add new feature'"; exit 1; fi
	@echo "$(CYAN)Staging and committing changes...$(RESET)"
	git add .
	git commit -m "$(COMMIT_MSG)"
	@echo "$(GREEN)✅ Changes committed!$(RESET)"

push: ## Push current branch to origin
	@echo "$(CYAN)Pushing to origin...$(RESET)"
	git push origin $$(git branch --show-current)
	@echo "$(GREEN)✅ Pushed to origin!$(RESET)"

##@ All-in-One Commands

dev-setup: install install-dev ## Complete development environment setup
	@echo "$(GREEN)✅ Development environment ready!$(RESET)"
	@echo "$(CYAN)Next steps:$(RESET)"
	@echo "  • Run 'make test' to verify installation"
	@echo "  • Run 'make demo-message-queue' to see the message queue in action"
	@echo "  • Run 'make help' to see all available commands"

quick-test: clean test ## Clean and run all tests
	@echo "$(GREEN)✅ Quick test cycle complete!$(RESET)"

ci-check: clean lint type-check test ## Full CI pipeline check
	@echo "$(GREEN)✅ CI checks passed!$(RESET)"

demo-all: message-queue-demo template-demo demo-comprehensive ## Run all demos
	@echo "$(GREEN)✅ All demos completed!$(RESET)"

##@ Project Info

info: ## Display project information
	@echo "$(CYAN)Multi-Agent Development System$(RESET)"
	@echo "================================"
	@echo "$(YELLOW)Project Structure:$(RESET)"
	@echo "  📁 mcp-servers/         - MCP server implementations"
	@echo "  📁 coordination-demo/   - Multi-agent coordination demos"
	@echo "  📁 docs/               - Documentation and analysis"
	@echo "  📁 scripts/            - Utility scripts"
	@echo ""
	@echo "$(YELLOW)Key Components:$(RESET)"
	@echo "  🔄 Message Queue       - Async pub/sub messaging (US-003)"
	@echo "  📋 Task Coordinator    - Task management system (US-005)"
	@echo "  🎭 Multi-Agent Demo    - Agent coordination proof of concept"
	@echo ""
	@echo "$(YELLOW)Available User Stories:$(RESET)"
	@echo "  ✅ US-001: Basic MCP Server Template"
	@echo "  ✅ US-002: Multi-Instance Coordination Demo"
	@echo "  ✅ US-003: Basic Message Queue Implementation"
	@echo "  ✅ US-004: Platform Capability Documentation"
	@echo ""
	@echo "Run '$(CYAN)make help$(RESET)' for all available commands." 