# Project Conventions for spiff-arena

This document outlines the key conventions and practices for contributing to the `spiff-arena` monorepo. Adhering to these guidelines ensures consistency, maintainability, and efficient collaboration.

## Architecture Overview

SpiffArena is composed of three main applications: `spiffworkflow-frontend`, `spiffworkflow-backend`, and optionally, a `connector proxy`. The frontend interacts with the backend via a REST API.

## Monorepo Structure

This project is a monorepo managed with `git subtrees`. It comprises several distinct components:

*   `spiffworkflow-backend`: The Python-based backend application.
*   `spiffworkflow-frontend`: The Node.js/React-based frontend application.
*   `spiff-arena-common`: Common utilities and shared code.
*   `connector-proxy-demo`: A demonstration of a connector proxy.
*   `docs`: Project documentation.

## Dependency Management

*   **Python:** `uv` is the primary tool for managing Python dependencies.
    *   Dependencies are defined in `pyproject.toml`.
    *   Locked dependencies are managed in `uv.lock`.
    *   Use `uv sync` to install/update Python dependencies.
*   **Node.js (Frontend):** `npm` is used for managing frontend dependencies.
    *   Dependencies are defined in `package.json`.
    *   Use `npm install` to install/update Node.js dependencies.

## Development Environment

Several options are available for setting up the development environment:

1.  **Make-based Docker Setup:** This is the recommended approach for active development, spinning up Docker containers that allow editing based on the latest source.
2.  **Docker Compose Setup:** Runs Docker containers based on the latest release, suitable for quick deployment without local editing.
3.  **Non-Docker Setup:** Allows running Python and React applications directly on your machine. Refer to the main `spiff-arena README` for detailed instructions.

Docker Compose is extensively used to provide a consistent and isolated development environment. The `Makefile` at the root of the repository provides convenient targets for common development tasks:

*   `make dev-env`: Builds Docker images, sets up the backend database, and installs `npm` and `uv` dependencies.
*   `make start-dev`: Starts the frontend and backend servers.
*   `make stop-dev`: Stops the frontend and backend servers.
*   `make run-pyl`: Runs all frontend and backend linters, and backend unit tests.

Refer to the `Makefile` for a comprehensive list of available targets and their actions.

## Code Quality and Linting

Maintaining high code quality is crucial. The project enforces several automated checks:

*   **Pre-commit Hooks:** `pre-commit` is used to run checks before commits. The configuration is in `.pre-commit-config.yaml`.
*   **Python:**
    *   `ruff`: Used for Python linting and formatting. Run with `ruff check --fix` or `make ruff`.
    *   `mypy`: Used for static type checking. Run with `make be-mypy`.
*   **Frontend (Node.js/JavaScript/TypeScript):**
    *   `eslint`: Used for linting. Run with `npm run lint:fix` (via `make fe-lint-fix`).

Always ensure that all linting and formatting checks pass before submitting code.

## Testing

*   **Backend (Python):**
    *   `pytest`: Used for unit and integration tests.
    *   Run backend tests with `make be-tests` or `make be-tests-par` (for parallel execution).
*   **Frontend (Cypress):**
    *   `Cypress`: Used for automated browser (end-to-end) tests.
    *   Refer to `bin/run_cypress_tests_locally` for running Cypress tests.

## Documentation

Project documentation is located in the `docs/` directory. When making changes that affect functionality or setup, ensure the documentation is updated accordingly.

## General Guidelines

*   **Consistency:** Adhere to the existing coding style, naming conventions, and architectural patterns found in the surrounding code.
*   **Error Handling:** Implement robust error handling for all new features and modifications.
*   **Comments:** Add comments sparingly, focusing on *why* a piece of code exists or *what* a complex algorithm does, rather than simply restating *what* the code does.
*   **Security:** Always consider security implications when writing or modifying code. Avoid hardcoding sensitive information.
*   **Review:** All code changes should be reviewed by at least one other team member.
