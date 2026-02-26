# Agent Instructions for spiffworkflow-frontend

This document provides instructions for AI agents working in the `spiffworkflow-frontend` directory.

This is a React application built with Vite and using `npm` as the package manager.

## Environment Setup

1. **Install Dependencies:**
    From the `spiffworkflow-frontend` directory, run:

    ```bash
    npm install
    ```

## Development

- **Run the development server:**

  ```bash
  npm start
  ```

  This will start the Vite development server.

## Building

- **Build for production:**

  ```bash
  npm run build
  ```

## Testing and Code Quality

- **Run unit tests:**

  ```bash
  npm test
  ```

- **Run type checks + lint fixes + tests:**

  ```bash
  npm run check
  ```

## Playwright E2E Tests

This project contains Playwright tests for end-to-end testing. These tests require both the frontend and backend to be running.

- **Location:** The tests are located in the `spiffworkflow-frontend/test/browser` directory.
- **Setup:** The test environment requires Python and its own set of dependencies. A `README.md` file in the test directory contains setup instructions. Agent setup scripts are available:
  - `./bin/agents/setup.sh` (from root) - Complete environment setup (backend + frontend + Playwright)
  - `./bin/agents/setup.sh` (from frontend) - Frontend-only setup

- **Running tests:**
  - **Quick method:** Use `./bin/agents/run_playwright.sh` (from root) to automatically start servers and run tests
  - **Manual method:** From the `spiffworkflow-frontend` directory:
    ```bash
    cd test/browser
    uv run pytest [test_file.py] [-v]
    ```
    Example: `uv run pytest process_models/test_can_create_new_bpmn_dmn_json_files.py -v`
