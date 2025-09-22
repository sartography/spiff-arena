# Agent Instructions for spiffworkflow-backend

This document provides instructions for AI agents working in the `spiffworkflow-backend` directory.

## Environment Setup

Setting up the development environment requires several manual steps. A fully automated script is not available due to the requirement of a running MySQL server.

1. **Install System Dependencies:**
    This project requires development headers for PostgreSQL and MySQL. On a Debian-based system, you can install them with:

    ```bash
    sudo apt-get update
    sudo apt-get install -y libpq-dev libmysqlclient-dev mysql-client
    ```

2. **Install Python Dependencies:**
    Use `uv` to install the Python dependencies:

    ```bash
    uv sync
    ```

3. **Set up Databases:**
    - For local development, you need a running MySQL server. Then, run the following command to create and migrate the database:

      ```bash
      ./bin/recreate_db clean
      ```

    - For running the unit tests, a separate sqlite database is required. Create it with:

      ```bash
      SPIFFWORKFLOW_BACKEND_DATABASE_TYPE=sqlite ./bin/recreate_db clean
      ```

## Running Tests

- **Run all tests:**
  From the root of the repository, run:

  ```bash
  ./bin/run_pyl
  ```

  (This will run pre-commit hooks and the python test suite).

- **Run a single backend test file:**
  From the `spiffworkflow-backend` directory, run:

  ```bash
  uv run pytest tests/spiffworkflow_backend/integration/test_process_model_milestones.py
  ```

- **Run a single backend test function:**
  From the `spiffworkflow-backend` directory, run:

  ```bash
  uv run pytest -k test_process_instance_list_filter
  ```
