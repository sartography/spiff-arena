---
name: ntl_code_review
description: Use this skill when reviewing implementation changes for the current task.
---

# ntl_code_review

Use this skill when reviewing implementation changes for the current task.

# Shared Context

Repository: /home/spiffuser/spiff-arena
Spec file: spiffworkflow-backend/spec.md
Frontend involved: yes
Backend involved: yes

## Spec Excerpt
Messages are saved on the process group - but you can't dictate on which process group.
So when you are in the message modal, it shows the current location based on the process group where the message is saved.
But as you can see, the location is also stored in the db.
We should be able to update the location for an existing message.
And if a message already exists at a certain parent location, and you are editing a process model that is in a child directory, it should assume you want to use the message in the parent directory (but you should be able to override this assumption).
This involves frontend, and will require testing in a browser.
The API may not know that things are being updated on a particular message (and therefore might naively just create a new message at a new location, instead of updating as intended).
Perhaps there is a new interface for editing messages, since it is kind of confusing to edit them from the context of a particular process model when in fact messages are specific to a process group and potentially shared across multiple process models.

> mysql -uroot spiffworkflow_backend_local_development -e 'select \* from message'
> +------+--------------------------------------------+-------------------------------------+--------+-----------------------+-----------------------+
> | id | identifier | location | schema | updated_at_in_seconds | created_at_in_seconds |
> +------+--------------------------------------------+-------------------------------------+--------+-----------------------+-----------------------+
> | 1439 | awesome-order-start | order | {} | 1771903745 | 1771903745 |
> | 1440 | document-uploaded | order | {} | 1771903745 | 1771903745 |
> | 1441 | request-for-information-received | order | {} | 1771903745 | 1771903745 |
> | 1442 | survey-request-fulfilled | order | {} | 1771903745 | 1771903745 |
> | 1443 | title-search-completed | order | {} | 1771903745 | 1771903745 |
> | 1444 | request-for-information-received | order/request-for-information | {} | 1771903745 | 1771903745 |
> | 1445 | reuest-for-information-received | order/request-for-information | {} | 1771903745 | 1771903745 |
> | 1446 | document-uploaded | order/order-survey | {} | 1771903745 | 1771903745 |
> | 1447 | order-survey-endpoint | order/order-survey | {} | 1771903745 | 1771903745 |
> | 1448 | survey-request-fulfilled | order/order-survey | {} | 1771903745 | 1771903745 |
> | 1449 | request-for-information-received | order/residential | {} | 1771903745 | 1771903745 |
> | 1450 | reuest-for-information-received | order/residential | {} | 1771903745 | 1771903745 |
> | 1451 | title-search-completed | order/order-title-search | {} | 1771903745 | 1771903745 |
> | 1452 | awesome-hello-world | training-and-prototypes | {} | 1771903745 | 1771903745 |
> | 1453 | decision | training-and-prototypes | {} | 1771903745 | 1771903745 |
> | 1454 | documents | training-and-prototypes | {} | 1771903745 | 1771903745 |
> | 1455 | lilimessages | training-and-prototypes | {} | 1771903745 | 1771903745 |
> | 1456 | process-documents | training-and-prototypes | {} | 1771903745 | 1771903745 |
> | 1457 | awesome-order-survey-start | shared/order-survey | {} | 1771903745 | 1771903745 |
> | 1458 | awesome-order-title-search-start | shared/order-title-search | {} | 1771903745 | 1771903745 |
> | 1459 | start-message-diagram-edit-acceptance-test | system/diagram-edit-acceptance-test | {} | 1771903745 | 1771903745 |
> +------+--------------------------------------------+-------------------------------------+--------+-----------------------+-----------------------+


## Mockups
- (none)

## AGENTS Guidance
## AGENTS.md
# Agent Instructions

## Quick Start

For agent environments, use these convenience scripts:

- `./bin/agents/setup.sh` - Complete setup (backend + frontend + Playwright)  
- `./bin/agents/run_playwright.sh` - Run Playwright tests (auto-starts/stops servers)

## Detailed Instructions

See spiffworkflow-backend/AGENTS.md and spiffworkflow-frontend/AGENTS.md


## spiffworkflow-backend/AGENTS.md
# Agent Instructions for spiffworkflow-backend

This document provides instructions for AI agents working in the `spiffworkflow-backend` directory.

## Environment Setup

### Automated Setup (Recommended)

For agent environments, unless the file `agent_setup_script_has_completed_successfully` exists, use the automated setup script
in the spiffworkflow-backend directory:

```bash
./bin/agents/backend_setup.sh
```

This script handles system dependencies, Python packages, database setup, and verification tests.

### Manual Setup

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

   Also install from root:

   ```bash
   (cd .. && uv sync)
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

  ```bash
  ../bin/run_pyl
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
  uv run pytest -

## spiffworkflow-frontend/AGENTS.md
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


## Clarifications
1. Q: Based on the spec, I believe both backend and frontend changes will be required. Correct? (yes/no)
   A: yes
2. Q: When a user edits an existing message’s location, should we update that same DB row (`message.id`) in place, or create a new row and relink references?
   A: update same db row based on message.id
3. Q: For the “child directory should assume parent message” rule, should we always pick the nearest ancestor location match (e.g., `order/request-for-information` prefers `order` over root), and only fall back further up if no nearer match exists?
   A: yes, always pick the nearest ancestor location
4. Q: In the modal UX, do you want explicit controls for both actions: `Use existing shared message` vs `Create/override at current location`?
   A: `Use existing shared message` only
5. Q: Should `identifier + location` be enforced as unique at the backend/database level after this change, and if duplicates already exist, what resolution policy should we apply?
   A: that unique key already exists in the database

## Verification Policy
Run unit tests and lint always; run browser/e2e checks when frontend_involved=yes.

## Browser Testing Instructions
- Use Chrome DevTools MCP for browser testing.
- Backend status at `localhost:7000/v1.0/status`; frontend at `localhost:7001`.
- Sign in with `admin / admin`.


# Review Task

Review the recent implementation changes with critical focus on correctness, regressions, security, and maintainability.
Use the repository skill `ntl_code_review` for review process and output structure.
Skill location: `.agents/skills/ntl_code_review/SKILL.md`

Base review prompt from harness standard template:
(provided by harness standard review template)

Output JSON only with this schema (single line, no prose):
{
  "summary": "short overall",
  "action_required": [
    {
      "id": "R1",
      "title": "short title",
      "details": "actionable details",
      "files": ["path:line"],
      "severity": "critical|high|medium|low"
    }
  ]
}

Rules:
- Include ONLY actionable findings that require code changes. No praise or informational notes.
- If no changes are required, return an empty array for "action_required".
- Include file references in "files" when possible.
- Do not include any other keys.

