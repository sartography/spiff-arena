# Project Conventions for spiffworkflow-frontend

This document outlines the key conventions and practices for contributing to the `spiffworkflow-frontend` project. Adhering to these guidelines ensures consistency, maintainability, and efficient collaboration.

## Technology Stack

*   **Framework:** React (with Preact for optimization)
*   **Language:** TypeScript
*   **Build Tool:** Vite
*   **Package Manager:** npm

## Dependency Management

*   Dependencies are managed via `npm` and defined in `package.json`.
*   Use `npm install` to install or update dependencies.

## Development Environment

*   To start the development server, navigate to the `spiffworkflow-frontend` directory and run `npm start`.
*   The application will typically be available at `http://localhost:7001`.

## Code Quality and Linting

Maintaining high code quality is crucial. The project enforces several automated checks:

*   **ESLint:** Used for linting JavaScript/TypeScript code. The configuration is in `.eslintrc.cjs`.
    *   Run `npm run eslint` to check for linting issues.
    *   Run `npm run lint:fix` to automatically fix linting issues.
*   **Prettier:** Used for code formatting. While not explicitly run as a pre-commit hook in this specific frontend setup, it's good practice to run `npm run format` before committing to ensure consistent code style.
*   **TypeScript Type Checking:**
    *   Run `npm run typecheck` to perform static type checking.

Always ensure that all linting, formatting, and type checks pass before submitting code.

## Testing

*   **Unit/Component Tests:**
    *   `Vitest` is used for unit and component testing.
    *   Test files are typically located alongside the code they test, with a `.test.ts` or `.test.tsx` extension (e.g., `MyComponent.test.tsx`).
    *   Run tests with `npm test`.
*   **End-to-End (E2E) Tests:**
    *   `Cypress` is used for automated browser tests.
    *   Cypress configuration is in `cypress.config.js`.
    *   Refer to the root `bin/run_cypress_tests_locally` script for running Cypress tests.

## Architecture and Key Libraries

*   **Layers:** The frontend follows a layered architecture where `Routes` delegate work to `Services`.
*   **bpmn-js:** Used for rendering and editing BPMN diagrams.
*   **bpmn-js-spiffworkflow:** SpiffWorkflow extensions to `bpmn-js` for enhanced BPMN execution.
*   **React JSON Schema Form (`@rjsf/core`, `@rjsf/utils`, etc.):** Used to build forms from JSON schemas, enabling dynamic form rendering for User Tasks.
*   **@tanstack/react-query:** Used for data fetching, caching, and state management, particularly for permission calls.

## Project Structure

*   The main application source code is located in the `src/` directory.
*   Components, utilities, and other modules should be organized logically within `src/`.

## Deployment

*   The generated Docker image uses `nginx` to serve static HTML/CSS/JS files produced by the Vite build process.
*   These static files can also be hosted on a Content Delivery Network (CDN).

## General Guidelines

*   **Consistency:** Adhere to the existing coding style, naming conventions, and architectural patterns found in the surrounding code.
*   **Component-Based Development:** Favor small, reusable, and well-defined React components.
*   **State Management:** Follow established patterns for state management within the application.
*   **Error Handling:** Implement robust error handling for all new features and modifications, providing clear feedback to the user.
*   **Accessibility:** Ensure all UI components are accessible.
*   **Internationalization (i18n):** Utilize `i18next` for all user-facing text to support multiple languages.
*   **Comments:** Add comments sparingly, focusing on *why* a piece of code exists or *what* a complex algorithm does, rather than simply restating *what* the code does.
*   **Security:** Always consider security implications when writing or modifying code. Avoid hardcoding sensitive information.
*   **Review:** All code changes should be reviewed by at least one other team member.
