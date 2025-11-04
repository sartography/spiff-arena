# GitHub Copilot Instructions for spiff-arena

## Project Overview

SpiffArena is a low(ish)-code software development platform for building, running, and monitoring executable diagrams. It supports BPMN-based workflow execution and provides both backend (Python) and frontend (React/TypeScript) components.

## Repository Structure

This is a monorepo containing:

- **spiffworkflow-backend**: Python/Flask backend with BPMN workflow engine
- **spiffworkflow-frontend**: React/TypeScript frontend with Vite
- **spiff-arena-common**: Shared Python libraries
- **connector-proxies**: Service connector implementations
- **docs**: Documentation (Sphinx-based)

## Development Setup

### Quick Start for AI Agents

For automated environment setup, use:
```bash
./bin/agents/setup.sh          # Complete setup (backend + frontend + Playwright)
./bin/agents/run_playwright.sh # Run Playwright tests
```

### Backend Setup

1. Install system dependencies (PostgreSQL and MySQL development headers):
   ```bash
   sudo apt-get install -y libpq-dev libmysqlclient-dev mysql-client
   ```

2. Install Python dependencies using `uv`:
   ```bash
   cd spiffworkflow-backend
   uv sync
   ```

3. Set up databases:
   ```bash
   ./bin/recreate_db clean                                      # MySQL for dev
   SPIFFWORKFLOW_BACKEND_DATABASE_TYPE=sqlite ./bin/recreate_db clean  # SQLite for tests
   ```

4. Run the server:
   ```bash
   ./bin/run_server_locally
   ```

See `spiffworkflow-backend/AGENTS.md` for detailed backend instructions.

### Frontend Setup

1. Install Node.js (check `.tool-versions` for recommended version)
2. Install dependencies:
   ```bash
   cd spiffworkflow-frontend
   npm install
   ```

3. Run development server:
   ```bash
   npm start
   ```

See `spiffworkflow-frontend/AGENTS.md` for detailed frontend instructions.

### Docker Development

Alternative to local setup:
```bash
make              # Build images, install deps, start servers, run tests
make start-dev    # Start servers
make stop-dev     # Stop servers
```

## Testing and Quality

### Run All Tests and Linters

From repository root:
```bash
./bin/run_pyl
```

This runs pre-commit hooks and the full Python test suite.

### Backend Tests

```bash
cd spiffworkflow-backend

# Run all backend tests
uv run pytest

# Run a specific test file
uv run pytest tests/spiffworkflow_backend/integration/test_process_model_milestones.py

# Run a specific test function
uv run pytest -k test_process_instance_list_filter
```

### Frontend Tests

```bash
cd spiffworkflow-frontend

# Run unit tests
npm test

# Run linter
npm run lint

# Fix linting issues
npm run lint:fix
```

### End-to-End Tests

Playwright tests are located in `spiffworkflow-frontend/test/browser`:
```bash
./bin/agents/run_playwright.sh  # Automated: starts servers and runs tests
```

## Code Style and Standards

### Python (Backend)

- **Python Version**: 3.10+ (backend requires `>=3.10`, root requires `>=3.11,<3.13`)
- **Package Manager**: `uv` (not pip or poetry)
- **Linting**: Ruff (configured in `pyproject.toml`)
- **Pre-commit**: Configured in `.pre-commit-config.yaml`
- **Testing**: pytest with SQLite database for tests

### TypeScript/JavaScript (Frontend)

- **Framework**: React with TypeScript
- **Build Tool**: Vite
- **Package Manager**: npm (not yarn or pnpm)
- **Linting**: ESLint
- **Testing**: Vitest for unit tests, Playwright for E2E

## Important Guidelines

### Making Code Changes

1. **Minimal Changes**: Make the smallest possible changes to achieve the goal
2. **Don't Break Existing Code**: Preserve working functionality unless fixing bugs
3. **Test Your Changes**: Run relevant tests before committing
4. **Follow Existing Patterns**: Match the coding style of surrounding code
5. **Update Documentation**: If changing functionality, update related docs

### Common Pitfalls to Avoid

- Don't use `poetry` - this project uses `uv` for Python dependency management
- Don't modify database schema without migrations
- Don't commit `node_modules` or Python virtual environments
- Don't disable tests without understanding why they're failing
- Don't change Docker configurations unless specifically required
- Port 7000 is used by backend (may conflict with macOS AirPlay)
- Backend requires MySQL/PostgreSQL for dev, SQLite for tests

### Working with the Monorepo

- Backend changes go in `spiffworkflow-backend/`
- Frontend changes go in `spiffworkflow-frontend/`
- Shared Python code goes in `spiff-arena-common/`
- This is a git subtree-based monorepo (see `bin/*subtree*` scripts)

## Key Files and Directories

- `bin/run_pyl` - Run all linters and tests
- `bin/agents/` - Agent automation scripts
- `Makefile` - Docker-based development commands
- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `AGENTS.md` - Quick reference for AI agents
- `CONTRIBUTING.rst` - Contribution guidelines
- `README.md` - Getting started guide

## Useful Commands

```bash
# Run all quality checks
./bin/run_pyl

# Setup agent environment
./bin/agents/setup.sh

# Run Playwright tests
./bin/agents/run_playwright.sh

# Docker development
make dev-env      # Setup environment
make start-dev    # Start servers
make be-tests-par # Run backend tests in parallel
make fe-lint-fix  # Fix frontend linting

# Backend database
cd spiffworkflow-backend
./bin/recreate_db clean

# Frontend development
cd spiffworkflow-frontend
npm install
npm start
npm test
npm run lint
```

## Getting Help

- **Documentation**: https://spiff-arena.readthedocs.io/
- **Discord**: https://discord.gg/BYHcc7PpUC
- **Issues**: https://github.com/sartography/spiff-arena/issues
- **Website**: https://www.spiffworkflow.org

## License

Main components are published under LGPL Version 3.
