# Spiff Arena and Ed Documentation Gap Audit

This audit covers public documentation for Spiff Arena and Ed.
It intentionally excludes SpiffWorkflow Engine internals.

Baseline:

- PR 2828, "Documentation Updates", merged on 2026-05-26.
- Current Sphinx docs in `docs/`.
- Current public Ed page before this pass: `docs/how_to_guides/ed_editor.md`.
- Ed implementation notes from the separate Ed source tree and AI tool definitions.

## Summary of Gaps

| Area | Status | Gap | Draft destination |
| --- | --- | --- | --- |
| Ed public docs | Missing structure | Ed was documented as one short how-to page, which made it hard to find product overview, authoring, forms, run/debug, AI, and sync guidance. | `aggregate-connector-proxy/ed/docs/index.md` and child pages |
| Ed vs Spiff Arena | Missing | Users need a clear distinction between authoring in Ed and production execution/admin in Spiff Arena. | `aggregate-connector-proxy/ed/docs/arena_vs_ed.md` |
| Ed workspace model | Missing | Existing docs did not explain workspace/process/file organization or schema/UI schema pairing. | `aggregate-connector-proxy/ed/docs/workspaces_files.md` |
| Ed BPMN authoring | Missing | Existing docs did not summarize Spiff-specific BPMN authoring checks in Ed. | `aggregate-connector-proxy/ed/docs/author_bpmn.md` |
| Ed forms | Missing | PR 2828 documented RJSF enhancements, but not how Ed authors should use the form builder and validate schema/UI schema pairs. | `aggregate-connector-proxy/ed/docs/forms.md` |
| Ed run/debug | Missing | Existing docs did not document the authoring loop of running diagrams, inspecting task data, and debugging forms or gateways. | `aggregate-connector-proxy/ed/docs/run_debug.md` |
| Ed GitHub sync | Too dense in one page | Existing sync details were mixed into the only Ed page. They needed a dedicated page and safer secret-handling guidance. | `aggregate-connector-proxy/ed/docs/github_sync.md` |
| Ed AI assistant | Missing | Ed AI capabilities and user expectations were not publicly documented. | `aggregate-connector-proxy/ed/docs/ai_assistant.md` |
| Navigation | Incomplete | Ed was buried under How-to Guides instead of being a first-level public documentation area. | `docs/index.md`, `docs/ed/index.md`, `docs/how_to_guides/index.md` |
| Naming consistency | Inaccurate | Several pages use `SpiffArena`; new and touched text should prefer `Spiff Arena`. | Ongoing cleanup |
| FAQ and deployment freshness | Partially stale | External link checking found stale GitHub line anchors, a removed SpiffWorkflow service-task page, a local preview URL rendered as a public link, and an unreliable sample API link. | FAQ, deployment guides, contribution guide, script-task reference |
| Deprecated form pattern | Partially addressed | PR 2828 marks `options_from_task_data_var:...` as deprecated and replaces examples with Jinja-rendered schema patterns. Remaining mentions should either explain legacy support or be converted. | Existing form and data-store docs |

## Draft Text Added

The implementation moves ready-to-review public Ed text into standalone Ed documentation for:

- Ed overview and product boundary.
- Getting started with Ed.
- Workspace, process, and file organization.
- BPMN authoring checklist.
- Form authoring and RJSF/Jinja checks in Ed.
- Running and debugging diagrams while authoring.
- GitHub sync configuration.
- AI assistant usage and review expectations.
- Spiff Arena vs Ed comparison.
The Spiff Arena documentation keeps a concise Ed landing page and includes FAQ/deployment cleanup for broken external links, stale line anchors, and a few deployment statements that had become too specific to old setups.

## Follow-up Recommendations

- Continue replacing casual `SpiffArena` mentions with `Spiff Arena` as nearby pages are edited.
- Review FAQ entries for outdated claims about script imports, service task behavior, and deployment examples.
- Split `Use User Tasks and Forms` into smaller pages if it grows further: dynamic forms, widgets, validation, layout, and guest tasks are now large enough to stand alone.
- Add or refresh screenshots in the standalone Ed docs when stable product screenshots are available.
- Add a periodic docs audit task when new RJSF widgets, Ed tools, or authoring workflows are added.

## Acceptance Checks

- Ed appears as a top-level Spiff Arena documentation section.
- The old Ed how-to URL still resolves and points readers to the standalone Ed docs.
- Spiff Arena and Ed are described as related but distinct products.
- The new Codex/agent guidance tells agents to check docs while working on BPMN, RJSF, Arena, or Ed tasks and to keep detailed Ed content in the standalone Ed docs.
- No new SpiffWorkflow Engine documentation is introduced.
