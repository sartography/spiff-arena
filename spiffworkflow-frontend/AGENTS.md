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

## Testing and Linting

- **Run unit tests:**

  ```bash
  npm test
  ```

- **Run linter:**

  ```bash
  npm run lint
  ```

## Playwright E2E Tests

This project contains Playwright tests for end-to-end testing. These tests require both the frontend and backend to be running.

- **Location:** The tests are located in the `spiffworkflow-frontend/test/browser` directory.
- **Setup:** The test environment requires Python and its own set of dependencies. A `README.md` file in the test directory contains setup instructions. A setup script `bin/agent_playwright_setup.sh` is also available at the root of the repository to automate the setup of the full testing environment.
- **Running tests:** Playwright tests can be run if requested by the user.
