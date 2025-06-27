# Project Conventions for spiffworkflow-backend

This document outlines the key conventions and practices for contributing to the `spiffworkflow-backend` project. Adhering to these guidelines ensures consistency, maintainability, and efficient collaboration.

## Technology Stack

*   **Framework:** Flask
*   **Language:** Python
*   **Dependency Management:** `uv`
*   **Database:** SQLAlchemy (supports MySQL, PostgreSQL, SQLite)

## Architecture and Layers

The backend is a Python Flask application functioning purely as a REST API. Requests are handled through a layered architecture:

*   **Controllers/Routes:** Entry point for incoming requests, mapped via `src/spiffworkflow_backend/api.yml` using the Connexion library. Controllers can use services (preferred) and models, but not other controllers.
*   **Services:** Contain most of the business logic. Services can use other services, but usage must be unidirectional (e.g., if ServiceA uses ServiceB, ServiceB cannot use ServiceA). Services can use models, but models cannot use services. Services cannot use controllers.
*   **Models:** Interact with the database via SQLAlchemy.

## Database

The backend uses SQLAlchemy to connect to a relational database (MySQL, PostgreSQL, or SQLite).

## Serialization

When serializing models to JSON:

*   Use `jsonify` (Flask) instead of `json.dumps`.
*   Prefer `@dataclass` on models over Marshmallow when possible.
*   For custom serialization, implement a `serialized` method on the model.

## Exceptions

*   Define all exception classes in a single file, or in files containing only exception class definitions, to avoid circular imports.
*   Avoid defining exceptions inside other classes.

## Deployment

*   The `Gunicorn` web server is used to serve the application in the default Dockerfile.
*   Environment variables for configuration are documented in `src/spiffworkflow_backend/config/default.py`.

## Dependency Management

*   Dependencies are managed via `uv` and defined in `pyproject.toml`.
*   Use `uv sync` to install or update dependencies.
*   External dependencies from Git repositories are specified in `[tool.uv.sources]` in `pyproject.toml`.

## Development Environment

*   The backend can be run locally using `uv` and `bin/run_server_locally` (after `cd spiffworkflow-backend` and `uv sync`).
*   Docker Compose is also used for development, with `dev.docker-compose.yml` defining the backend service.

## Code Quality and Linting

Maintaining high code quality is crucial. The project enforces several automated checks:

*   **Pre-commit Hooks:** `pre-commit` is used to run checks before commits. The configuration is in `.pre-commit-config.yaml`.
    *   `black`: Used for Python code formatting.
    *   `check-added-large-files`, `check-toml`, `check-yaml`, `end-of-file-fixer`, `trailing-whitespace`: General file checks.
*   **Ruff:** Used for Python linting and formatting. Configuration is in `pyproject.toml`.
    *   Run `ruff check --fix` or `make ruff` (from the monorepo root).
*   **MyPy:** Used for static type checking. Configuration is in `pyproject.toml`.
    *   Run `make be-mypy` (from the monorepo root).
*   **Safety:** Used for checking known security vulnerabilities in dependencies.

Always ensure that all linting, formatting, and type checks pass before submitting code.

## Testing

*   **Unit/Integration Tests:**
    *   `pytest` is used for unit and integration testing. Configuration is in `pyproject.toml`.
    *   Test files are located in the `tests/` directory, typically mirroring the `src/` directory structure.
    *   Run tests with `make be-tests` or `make be-tests-par` (for parallel execution) from the monorepo root.
    *   `conftest.py` contains fixtures and setup for tests.

## Project Structure

*   The main application source code is located in `src/spiffworkflow_backend/`.
*   Database migrations are managed in `migrations/`.
*   Process models are stored in `process_models/`.

## General Guidelines

*   **Consistency:** Adhere to the existing coding style, naming conventions (e.g., snake_case for Python), and architectural patterns found in the surrounding code.
*   **API Design:** Follow RESTful principles for API endpoints.
*   **Error Handling:** Implement robust error handling for all new features and modifications, returning appropriate HTTP status codes and informative error messages.
*   **Database Interactions:** Use SQLAlchemy ORM for database operations. Avoid raw SQL queries unless absolutely necessary.
*   **Security:** Always consider security implications when writing or modifying code. Pay attention to input validation, authentication, and authorization.
*   **Comments:** Add comments sparingly, focusing on *why* a piece of code exists or *what* a complex algorithm does, rather than simply restating *what* the code does.
*   **Review:** All code changes should be reviewed by at least one other team member.
