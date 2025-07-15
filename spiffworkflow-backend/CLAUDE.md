# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Installation
- Install dependencies: `uv sync`
- Database setup: `./bin/recreate_db clean`

### Running the Server
- Run the server locally: `./bin/run_server_locally`
- Run with Celery worker: `./bin/run_server_locally celery_worker`

### Testing
- Run lint and tests in parallel (this is all you need): `../bin/run_pyl`
- Run specific test: `uv run pytest tests/path/to/test_file.py -v`
- Run tests in parallel: `./bin/tests-par`
- Run type checking: `./bin/run_ci_session mypy`
- Run type guard: `./bin/run_ci_session typeguard`
- Run security checks: `./bin/run_ci_session safety`
- Run code coverage: `./bin/run_ci_session coverage`

### Linting and Code Quality
- Ruff linting is configured in pyproject.toml
- Pre-commit hooks are set up in .pre-commit-config.yaml
- Common linting rules: line length 130, Python 3.10+ target

## Code Architecture

### Core Components

1. **Flask/Connexion API Framework**
   - Uses Flask 3.1.1 with Connexion for API specification
   - API routes defined in api.yml
   - Routes defined in src/spiffworkflow_backend/routes/

2. **Database Models**
   - SQLAlchemy ORM with support for MySQL, PostgreSQL, and SQLite
   - Models defined in src/spiffworkflow_backend/models/
   - Migration management with Flask-Migrate

3. **Process Engine (SpiffWorkflow)**
   - Integrates with SpiffWorkflow library for BPMN process execution
   - Process models, instances, and tasks managed in database
   - Background processing via APScheduler and Celery

4. **Authentication**
   - JWT-based authentication with Flask-JWT-Extended
   - OpenID support with configurable providers
   - User/Group permission system

5. **Background Processing**
   - APScheduler for scheduled tasks
   - Celery for distributed task processing
   - Process instance execution can run in background

### Key Concepts

- **Process Models**: BPMN process definitions
- **Process Instances**: Specific executions of process models
- **Human Tasks**: Tasks requiring user interaction
- **Message Events**: BPMN message event handling
- **Data Stores**: Key-value and JSON data storage for processes

### Configuration

- Environment-based configuration system
- Database connection settings (MySQL, PostgreSQL, SQLite)
- OpenID authentication settings
- File storage settings
- Encryption settings

### Important Files and Directories

- `app.py`: Flask application entry point
- `spiff_web_server.py`: Connexion app for uvicorn server
- `src/spiffworkflow_backend/__init__.py`: Application initialization
- `src/spiffworkflow_backend/models/`: Database models
- `src/spiffworkflow_backend/routes/`: API routes and controllers
- `src/spiffworkflow_backend/services/`: Business logic
- `bin/`: Scripts for common operations
- `migrations/`: Database migration files
