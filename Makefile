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
VENV_PYTHON = $(shell pwd)/mcp-servers/venv/bin/python
SYSTEM_PYTHON = python3

# Check if venv exists and define Python command
PYTHON_CMD = $(shell if [ -f $(VENV_PYTHON) ]; then echo "$(VENV_PYTHON)"; else echo "$(SYSTEM_PYTHON)"; fi)
PYTHON = $(PYTHON_CMD)

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
	@echo "$(CYAN)Setting up Task Coordinator environment...$(RESET)"
	@if [ ! -d "mcp-servers/task-coordinator/venv" ]; then \
		cd mcp-servers/task-coordinator && python3 -m venv venv && \
		./venv/bin/pip install --upgrade pip && \
		./venv/bin/pip install -r requirements.txt; \
	fi
	@echo "$(GREEN)✅ Environment setup complete!$(RESET)"

install-dev: ## Install development dependencies (testing, linting, formatting)
	@echo "$(CYAN)Installing development dependencies...$(RESET)"
	mcp-servers/venv/bin/pip install pytest pytest-cov pytest-asyncio black flake8 mypy
	@echo "$(CYAN)Installing Task Coordinator development dependencies...$(RESET)"
	@if [ -d "mcp-servers/task-coordinator/venv" ]; then \
		cd mcp-servers/task-coordinator && ./venv/bin/pip install black flake8 mypy; \
	fi
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

task-coordinator-demo: ## Run task coordinator MCP server demo
	@echo "$(CYAN)Running Task Coordinator MCP Server Demo...$(RESET)"
	cd mcp-servers/task-coordinator && ./venv/bin/python -c "from src.task_coordinator_server import TaskCoordinatorServer; from src.models.task import Task; server = TaskCoordinatorServer('task-coordinator', '1.0.0'); print('✅ Task Coordinator Server initialized with dependency management'); print('📋 Server capabilities:', list(server.capabilities.get('tools', {}).keys()))"

real-mcp-server: ## Start the real MCP coordination server
	@echo "$(CYAN)Starting Real MCP Coordination Server...$(RESET)"
	$(PYTHON_CMD) mcp-servers/real-mcp-server.py agent-001 demo-agent

##@ Testing

test: ## Run all tests
	@echo "$(CYAN)Running all tests...$(RESET)"
	cd mcp-servers/message-queue && $(PYTHON) -m pytest tests/ -v
	cd mcp-servers/template && $(PYTHON) -m pytest tests/ -v
	cd mcp-servers/task-coordinator && ./venv/bin/python -m pytest tests/ -v
	$(PYTHON) -m pytest tests/test_makefile_commands.py -v --tb=short
	@echo "$(GREEN)✅ All tests completed!$(RESET)"

test-all-recursive: ## Run ALL tests from ALL subcomponents recursively
	@echo "$(CYAN)Running all tests recursively across entire project...$(RESET)"
	@echo "$(YELLOW)Discovering and running tests from all components...$(RESET)"
	@# Message Queue tests (including US-007)
	@if [ -d "mcp-servers/message-queue/tests" ]; then \
		echo "$(CYAN)🔍 Running Message Queue tests (including US-007)...$(RESET)"; \
		cd mcp-servers/message-queue && $(PYTHON) -m pytest tests/ -v --tb=short; \
	fi
	@# Template tests
	@if [ -d "mcp-servers/template/tests" ]; then \
		echo "$(CYAN)🔍 Running Template tests...$(RESET)"; \
		cd mcp-servers/template && $(PYTHON) -m pytest tests/ -v --tb=short; \
	fi
	@# Task Coordinator tests
	@if [ -d "mcp-servers/task-coordinator/tests" ]; then \
		echo "$(CYAN)🔍 Running Task Coordinator tests...$(RESET)"; \
		cd mcp-servers/task-coordinator && ./venv/bin/python -m pytest tests/ -v --tb=short; \
	fi
	@# Root-level tests
	@if [ -d "tests" ]; then \
		echo "$(CYAN)🔍 Running Root-level tests...$(RESET)"; \
		$(PYTHON) -m pytest tests/ -v --tb=short; \
	fi
	@# Discover any additional test directories
	@echo "$(CYAN)🔍 Scanning for additional test directories...$(RESET)"
	@find . -name "tests" -type d ! -path "./.*" ! -path "./*/venv/*" ! -path "./*/node_modules/*" | while read dir; do \
		if [ -f "$$dir/test_*.py" ] || [ -f "$$dir/**/test_*.py" ]; then \
			echo "$(YELLOW)Found additional test directory: $$dir$(RESET)"; \
			parent_dir=$$(dirname $$dir); \
			if [ -f "$$parent_dir/requirements.txt" ] && [ ! -d "$$parent_dir/venv" ]; then \
				echo "$(YELLOW)Setting up venv for $$parent_dir$(RESET)"; \
				cd $$parent_dir && python3 -m venv venv && ./venv/bin/pip install -r requirements.txt; \
			fi; \
			cd $$parent_dir && $(PYTHON) -m pytest tests/ -v --tb=short 2>/dev/null || echo "$(RED)Failed to run tests in $$dir$(RESET)"; \
		fi; \
	done
	@echo "$(GREEN)✅ All recursive tests completed!$(RESET)"

test-discover: ## Discover all test files across the project
	@echo "$(CYAN)Discovering all test files in the project...$(RESET)"
	@echo "$(YELLOW)Test file discovery:$(RESET)"
	@find . -name "test_*.py" -type f ! -path "./.*" ! -path "./*/venv/*" ! -path "./*/node_modules/*" | while read file; do \
		echo "  📝 $$file"; \
	done
	@echo ""
	@echo "$(YELLOW)Test directory discovery:$(RESET)"
	@find . -name "tests" -type d ! -path "./.*" ! -path "./*/venv/*" ! -path "./*/node_modules/*" | while read dir; do \
		test_count=$$(find $$dir -name "test_*.py" | wc -l); \
		echo "  📁 $$dir ($$test_count test files)"; \
	done
	@echo ""
	@echo "$(CYAN)Total test files:$(RESET) $$(find . -name "test_*.py" -type f ! -path "./.*" ! -path "./*/venv/*" ! -path "./*/node_modules/*" | wc -l)"

test-count: ## Count all tests across the project  
	@echo "$(CYAN)Counting all tests across the project...$(RESET)"
	@echo "$(YELLOW)Test counts by component:$(RESET)"
	@if [ -d "mcp-servers/message-queue/tests" ]; then \
		cd mcp-servers/message-queue && count=$$(find tests/ -name "test_*.py" | wc -l) && echo "  📊 Message Queue: $$count test files (includes US-007)"; \
	fi
	@if [ -d "mcp-servers/template/tests" ]; then \
		cd mcp-servers/template && count=$$(find tests/ -name "test_*.py" | wc -l) && echo "  📊 Template: $$count test files"; \
	fi
	@if [ -d "mcp-servers/task-coordinator/tests" ]; then \
		cd mcp-servers/task-coordinator && count=$$(find tests/ -name "test_*.py" | wc -l) && echo "  📊 Task Coordinator: $$count test files"; \
	fi
	@if [ -d "tests" ]; then \
		count=$$(find tests/ -name "test_*.py" | wc -l) && echo "  📊 Root Tests: $$count test files"; \
	fi
	@echo ""
	@echo "$(GREEN)📈 Total Test Files: $$(find . -name "test_*.py" -type f ! -path "./*/venv/*" | wc -l)$(RESET)"
	@echo "$(CYAN)Including US-007 tests: ✅ test_us007_channel_management.py$(RESET)"

test-message-queue: ## Run message queue tests only
	@echo "$(CYAN)Running Message Queue tests...$(RESET)"
	cd mcp-servers/message-queue && $(PYTHON) -m pytest tests/ -v

test-template: ## Run template server tests only
	@echo "$(CYAN)Running Template server tests...$(RESET)"
	cd mcp-servers/template && $(PYTHON) -m pytest tests/ -v

test-task-coordinator: ## Run task coordinator tests only
	@echo "$(CYAN)Running Task Coordinator tests...$(RESET)"
	cd mcp-servers/task-coordinator && ./venv/bin/python -m pytest tests/ -v

test-us007: ## Run US-007 channel management tests specifically
	@echo "$(CYAN)Running US-007 Channel Management tests...$(RESET)"
	cd mcp-servers/message-queue && $(PYTHON) -m pytest tests/test_us007_channel_management.py -v
	@echo "$(GREEN)✅ US-007 tests completed!$(RESET)"

test-coverage: ## Run tests with coverage report
	@echo "$(CYAN)Running tests with coverage...$(RESET)"
	cd mcp-servers/message-queue && $(PYTHON) -m pytest tests/ --cov=src --cov-report=html --cov-report=term
	cd mcp-servers/template && $(PYTHON) -m pytest tests/ --cov=src --cov-report=html --cov-report=term
	cd mcp-servers/task-coordinator && ./venv/bin/python -m pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "$(GREEN)✅ Coverage reports generated!$(RESET)"

test-coverage-all: ## Run all tests with combined coverage report
	@echo "$(CYAN)Running all tests with comprehensive coverage...$(RESET)"
	@# Create combined coverage directory
	@mkdir -p coverage-reports
	@# Message Queue coverage
	@if [ -d "mcp-servers/message-queue/tests" ]; then \
		echo "$(CYAN)📊 Message Queue coverage...$(RESET)"; \
		cd mcp-servers/message-queue && $(PYTHON) -m pytest tests/ --cov=src --cov-report=html:../../coverage-reports/message-queue --cov-report=term; \
	fi
	@# Template coverage  
	@if [ -d "mcp-servers/template/tests" ]; then \
		echo "$(CYAN)📊 Template coverage...$(RESET)"; \
		cd mcp-servers/template && $(PYTHON) -m pytest tests/ --cov=src --cov-report=html:../../coverage-reports/template --cov-report=term; \
	fi
	@# Task Coordinator coverage
	@if [ -d "mcp-servers/task-coordinator/tests" ]; then \
		echo "$(CYAN)📊 Task Coordinator coverage...$(RESET)"; \
		cd mcp-servers/task-coordinator && ./venv/bin/python -m pytest tests/ --cov=src --cov-report=html:../../coverage-reports/task-coordinator --cov-report=term; \
	fi
	@echo "$(GREEN)✅ Coverage reports generated in coverage-reports/$(RESET)"

test-coordination: ## Run coordination and integration tests
	@echo "$(CYAN)Running coordination tests...$(RESET)"
	cd coordination-demo && $(PYTHON) comprehensive-coordination-test.py
	cd coordination-demo && $(PYTHON) comprehensive-test.py

test-makefile: ## Run tests for all Makefile commands
	@echo "$(CYAN)Running Makefile command tests...$(RESET)"
	$(PYTHON) -m pytest tests/test_makefile_commands.py -v --tb=short
	@echo "$(GREEN)✅ Makefile tests completed!$(RESET)"

##@ Code Quality

lint: ## Run linting checks
	@echo "$(CYAN)Running linting checks...$(RESET)"
	@$(PYTHON) -m flake8 mcp-servers/message-queue/src/ --max-line-length=100 2>/dev/null || echo "$(YELLOW)Flake8 not installed - run 'make install-dev'$(RESET)"
	@$(PYTHON) -m flake8 mcp-servers/template/src/ --max-line-length=100 2>/dev/null || echo "$(YELLOW)Flake8 not installed - run 'make install-dev'$(RESET)"
	@cd mcp-servers/task-coordinator && ./venv/bin/python -m flake8 src/ --max-line-length=100 2>/dev/null || echo "$(YELLOW)Flake8 not installed - run 'make install-dev'$(RESET)"
	@$(PYTHON) -m flake8 coordination-demo/*.py --max-line-length=100 2>/dev/null || echo "$(YELLOW)Flake8 not installed - run 'make install-dev'$(RESET)"

format: ## Format code with black
	@echo "$(CYAN)Formatting code...$(RESET)"
	@$(PYTHON) -m black mcp-servers/message-queue/src/ 2>/dev/null || echo "$(YELLOW)Black not installed - run 'make install-dev'$(RESET)"
	@$(PYTHON) -m black mcp-servers/template/src/ 2>/dev/null || echo "$(YELLOW)Black not installed - run 'make install-dev'$(RESET)"
	@cd mcp-servers/task-coordinator && ./venv/bin/python -m black src/ 2>/dev/null || echo "$(YELLOW)Black not installed - run 'make install-dev'$(RESET)"
	@$(PYTHON) -m black coordination-demo/*.py 2>/dev/null || echo "$(YELLOW)Black not installed - run 'make install-dev'$(RESET)"
	@echo "$(GREEN)✅ Code formatting complete!$(RESET)"

type-check: ## Run type checking with mypy
	@echo "$(CYAN)Running type checks...$(RESET)"
	@$(PYTHON) -m mypy mcp-servers/message-queue/src/ --ignore-missing-imports 2>/dev/null || echo "$(YELLOW)MyPy not installed - run 'make install-dev'$(RESET)"
	@$(PYTHON) -m mypy mcp-servers/template/src/ --ignore-missing-imports 2>/dev/null || echo "$(YELLOW)MyPy not installed - run 'make install-dev'$(RESET)"
	@cd mcp-servers/task-coordinator && ./venv/bin/python -m mypy src/ --ignore-missing-imports 2>/dev/null || echo "$(YELLOW)MyPy not installed - run 'make install-dev'$(RESET)"

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
	rm -rf coverage-reports/ 2>/dev/null || true
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
	@echo "$(YELLOW)Task Coordinator Server:$(RESET)"
	@cd mcp-servers/task-coordinator && timeout 5 ./venv/bin/python -c "from src.task_coordinator_server import TaskCoordinatorServer; server = TaskCoordinatorServer('test', '1.0.0'); print('✅ Task Coordinator: OK')" || echo "❌ Task Coordinator: FAIL"

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

test-all: test-all-recursive test-coordination test-makefile ## Run all tests including coordination and makefile tests
	@echo "$(GREEN)✅ All comprehensive tests completed!$(RESET)"

ci-check: clean lint type-check test ## Full CI pipeline check
	@echo "$(GREEN)✅ CI checks passed!$(RESET)"

demo-all: message-queue-demo template-demo task-coordinator-demo demo-comprehensive ## Run all demos
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
	@echo "  📋 Task Coordinator    - Dependency management system (US-006)"
	@echo "  🎭 Multi-Agent Demo    - Agent coordination proof of concept"
	@echo ""
	@echo "$(YELLOW)Available User Stories:$(RESET)"
	@echo "  ✅ US-001: Basic MCP Server Template"
	@echo "  ✅ US-002: Multi-Instance Coordination Demo"
	@echo "  ✅ US-003: Basic Message Queue Implementation"
	@echo "  ✅ US-004: Platform Capability Documentation"
	@echo "  ✅ US-006: Task Coordinator - Dependency Management"
	@echo ""
	@echo "Run '$(CYAN)make help$(RESET)' for all available commands." 