# Agent Instructions

## Quick Start

For agent environments, use these convenience scripts:

- `./bin/agents/setup.sh` - Complete setup (backend + frontend + Playwright)  
- `./bin/agents/run_playwright.sh` - Run Playwright tests (auto-starts/stops servers)

## Detailed Instructions

See spiffworkflow-backend/AGENTS.md and spiffworkflow-frontend/AGENTS.md

## Documentation Check

When working on BPMN diagrams, RJSF forms, Spiff Arena behavior, Ed behavior, AI-assisted Ed workflows, or examples that teach process-authoring patterns, check whether the public documentation covers the steps, approach, variations, and edge cases you discover.

- If the docs are missing, stale, or misleading, call that out in the final response.
- When the task already touches related Spiff Arena docs or the documentation gap is small and clear, update the docs in the same change.
- Detailed Ed documentation lives outside this repository. If Ed docs are missing, stale, or misleading, call that out or update the standalone Ed docs source when it is in scope.
- For this rule, focus on Spiff Arena documentation and standalone Ed documentation. Do not expand into SpiffWorkflow Engine documentation unless the user explicitly asks for engine docs.
