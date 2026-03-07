# Implementation Plan Summary (Task Table -> Workflow Blob)

note: Partially implemented, but keep going.

1. Decision to lock first

- Treat this as two strategies only:
  - `task_based` (current `TaskModel` table)
  - `blob_based` (new workflow blob table)

2. Primary schema change

- Add `workflow_blob_storage` (1 row per process instance):
  - `process_instance_id` (unique FK)
  - `workflow_data` (`JSONB`)
  - `serializer_version`
  - `created_at_in_seconds`, `updated_at_in_seconds`
- Keep `human_task` table for assignments/ownership/completion UX.

3. Storage abstraction

- Add `WorkflowStorageService` with interface like:
  - `load_workflow(process_instance_id)`
  - `save_workflow(process_instance_id, workflow_dict)`
  - `get_task(task_guid, process_instance_id)` (synthetic task view in blob mode)
  - `list_tasks(process_instance_id, filters)`
- Back it by feature flag:
  - `SPIFFWORKFLOW_BACKEND_WORKFLOW_STORAGE_STRATEGY=task_based|blob_based`

4. Read path migration

- Update key endpoints/services to read via storage service first:
  - process-instance task list (diagram coloring path)
  - task data by guid
  - manual complete task
  - task submit/complete flow
- In `blob_based`, construct synthetic task objects expected by current API serializers.

5. Write path migration

- In processor/task service flows, replace direct `TaskModel` persistence with blob save.
- Keep transaction semantics with existing queue/dequeue and process-instance locking so concurrent writes remain safe.

6. Human task integration

- Continue creating/updating `HumanTaskModel` from runtime tasks.
- Keep `task_guid` as stable join key into blob-derived task records.
- Ensure “complete human task” still resolves correct blob task and state.

7. Compatibility and rollout

- Phase 1: add table + service, no behavior change (`task_based` default).
- Phase 2: dual-read capability in code, still writing old way.
- Phase 3: enable `blob_based` for selected process instances/tenants.
  - Add a nullable `workflow_storage_strategy` column on `process_instance`; resolve strategy as per-instance override first, global env default second.
  - For selected instances, write and verify blob data, then set `workflow_storage_strategy='blob_based'`.
  - Roll back an instance by setting `workflow_storage_strategy='task_based'` without changing global defaults.
- Phase 4: migrate old instances, validate parity, deprecate `TaskModel` writes.
- Phase 5: remove `TaskModel` reads when confidence is high.

8. Testing focus

- API parity tests for task list, task details, submit, manual complete.
- Diagram endpoint parity (including multi-instance/runtime_info behavior).
- Concurrency tests around simultaneous completion/update.
- Migration tests: same instance before/after strategy switch.

9. Known trade-offs

- Pure blob reduces schema complexity and duplication.
- Querying individual tasks may be slower unless mitigated by:
  - caching hot task projections
  - targeted JSONB indexing if needed
- Start simple; optimize only after measured bottlenecks.

10. Success criteria

- No API contract changes for clients.
- Human task flows unchanged for end users.
- Diagram/task-state endpoints match current behavior.
