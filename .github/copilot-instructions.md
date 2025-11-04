# GitHub Copilot Instructions for spiff-arena

SpiffArena is a BPMN workflow execution platform with Python/Flask backend and React/TypeScript frontend.

## Key Documentation

- See **`README.md`** for project overview and setup instructions
- See **`AGENTS.md`** for AI agent quick start (setup scripts, testing)
- See **`CONTRIBUTING.rst`** for contribution guidelines
- See **`spiffworkflow-backend/AGENTS.md`** for backend-specific instructions
- See **`spiffworkflow-frontend/AGENTS.md`** for frontend-specific instructions

## Critical Constraints

- **Python**: Use `uv` (not pip or poetry). Backend requires 3.10+; root workspace requires 3.11 or 3.12 (not 3.13)
- **JavaScript**: Use `npm` (not yarn or pnpm)
- **Testing**: Run `./bin/run_pyl` for all tests and linters before committing
- **Databases**: MySQL/PostgreSQL for dev, SQLite for tests
- **Monorepo**: This is a git subtree-based monorepo - backend, frontend, and shared libraries are separate components
