# Agent Instructions for spiffworkflow-frontend

This document provides instructions for AI agents working in the `spiffworkflow-frontend` directory.

This is a React application built with Vite and using `bun` as the package manager.

## Environment Setup

1.  **Install `bun`:**
    If you don't have `bun` installed, you will need to install it first. Follow the instructions at https://bun.sh/docs/installation.

2.  **Install Dependencies:**
    From the `spiffworkflow-frontend` directory, run:
    ```bash
    bun install
    ```

## Development

-   **Run the development server:**
    ```bash
    bun start
    ```
    This will start the Vite development server.

## Building

-   **Build for production:**
    ```bash
    bun run build
    ```

## Testing and Linting

-   **Run unit tests:**
    ```bash
    bun test
    ```

-   **Run linter:**
    ```bash
    bun run lint
    ```

-   **Run Cypress E2E tests:**
    There is no explicit script in `package.json` for Cypress, but you can use the script in the `bin` directory:
    ```bash
    ./bin/run_cypress_tests_locally
    ```
