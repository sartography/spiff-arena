# Orphaned Children Bug - Visual Analysis

## The Bug: How Orphaned Child References Are Created

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NORMAL EXECUTION PATH                                │
│                         (When everything works)                              │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │ Start Process│
    └──────┬───────┘
           │
           ▼
    ┌──────────────────────┐
    │  Execute BPMN Tasks  │
    │  (spiff_task.run())  │
    └──────┬───────────────┘
           │
           ▼
    ┌────────────────────────────────────────┐
    │  SpiffWorkflow creates child tasks     │
    │  in memory:                            │
    │                                        │
    │  Parent Task:                          │
    │    properties_json["children"] =       │
    │      ["child-guid-1", "child-guid-2"]  │
    │                                        │
    │  Child Tasks created in memory:        │
    │    - child-guid-1 (READY state)        │
    │    - child-guid-2 (READY state)        │
    └────────────────┬───────────────────────┘
                     │
                     ▼
    ┌──────────────────────────────────────────┐
    │  Save to Database                        │
    │  - Parent task saved with child refs     │
    │  - Child tasks saved                     │
    │  ✅ All references valid!                │
    └──────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         BUG SCENARIO PATH                                    │
│                    (Service task fails mid-execution)                        │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │ Start Process│
    └──────┬───────┘
           │
           ▼
    ┌──────────────────────┐
    │  Execute BPMN Tasks  │
    │  (spiff_task.run())  │
    └──────┬───────────────┘
           │
           ▼
    ┌────────────────────────────────────────────────────────┐
    │  SpiffWorkflow creates/predicts child tasks:           │
    │                                                        │
    │  Service Task (STARTED):                               │
    │    properties_json["children"] =                       │
    │      ["gateway-guid", "predicted-1", "predicted-2"]    │
    │                                                        │
    │  Child Tasks in SpiffWorkflow memory:                  │
    │    - gateway-guid (FUTURE state)                       │
    │    - predicted-1 (MAYBE state - PREDICTED_MASK)        │
    │    - predicted-2 (LIKELY state - PREDICTED_MASK)       │
    └────────────────┬───────────────────────────────────────┘
                     │
                     ▼
             ┌───────────────┐
             │  💥 ERROR!     │
             │  Service Task │
             │  Fails        │
             └───────┬───────┘
                     │
                     ▼
    ┌──────────────────────────────────────────────────────────┐
    │  Exception Handler (finally block)                       │
    │  workflow_execution_service.py:588-595                   │
    │                                                          │
    │  Calls: execution_strategy.add_object_to_db_session()    │
    └────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
    ┌──────────────────────────────────────────────────────────┐
    │  TaskModelSavingDelegate.add_object_to_db_session()      │
    │  workflow_execution_service.py:373-385                   │
    │                                                          │
    │  for task in get_tasks(WAITING|READY|MAYBE|LIKELY|...): │
    │      task_service.update_task_model_with_spiff_task()    │
    │                      ⬆️                                   │
    │              ⚠️  IMPORTANT: Does NOT call                │
    │                 process_spiff_task_children()!           │
    └────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
    ┌──────────────────────────────────────────────────────────┐
    │  update_task_model_with_spiff_task()                     │
    │  task_service.py:198-264                                 │
    │                                                          │
    │  ├─ Calls: update_task_model(task_model, spiff_task)    │
    │  │           ⬇️                                          │
    │  └─────► Serializes task with serializer.to_dict()      │
    │           ⬇️                                             │
    │          Copies properties_json["children"] array        │
    │          INCLUDING ALL CHILD GUIDs from SpiffWorkflow    │
    │          (no filtering of PREDICTED tasks!)              │
    └────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
    ┌──────────────────────────────────────────────────────────┐
    │  Save to Database                                        │
    │  task_service.py:141-146                                 │
    │                                                          │
    │  db.session.bulk_save_objects(self.task_models.values())│
    └────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
    ┌──────────────────────────────────────────────────────────┐
    │  DATABASE STATE - INCONSISTENT! 🐛                       │
    │                                                          │
    │  ✅ Service Task (ERROR state)                           │
    │     guid: "service-123"                                  │
    │     properties_json["children"]: [                       │
    │       "gateway-guid",                                    │
    │       "predicted-1",  ◄─── ORPHANED!                     │
    │       "predicted-2"   ◄─── ORPHANED!                     │
    │     ]                                                    │
    │                                                          │
    │  ✅ Gateway Task (FUTURE state)                          │
    │     guid: "gateway-guid"                                 │
    │     (exists in DB)                                       │
    │                                                          │
    │  ❌ predicted-1 (NOT IN DATABASE)                        │
    │     Filtered out because MAYBE has PREDICTED_MASK        │
    │                                                          │
    │  ❌ predicted-2 (NOT IN DATABASE)                        │
    │     Filtered out because LIKELY has PREDICTED_MASK       │
    └──────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                    THE UNUSED FILTERING CODE                                 │
│              (This code EXISTS but is NEVER CALLED!)                         │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────┐
    │  process_parents_and_children_and_save_to_database()     │
    │  task_service.py:151-157                                 │
    │                                                          │
    │  ⚠️  NEVER CALLED IN CODEBASE! ⚠️                        │
    │                                                          │
    │  This would call:                                        │
    │    ├─ process_spiff_task_children()                      │
    │    │   └─ Filters PREDICTED tasks!                       │
    │    └─ save_objects_to_database()                         │
    └──────────────────────────────────────────────────────────┘
                             │
                             ▼
    ┌──────────────────────────────────────────────────────────┐
    │  process_spiff_task_children()                           │
    │  task_service.py:159-172                                 │
    │                                                          │
    │  for child in spiff_task.children:                       │
    │      if child.has_state(TaskState.PREDICTED_MASK):       │
    │          # Remove from parent's children array!          │
    │          remove_spiff_task_from_parent(child)            │
    │          continue  ◄──── THIS NEVER RUNS!                │
    │                                                          │
    │      # Save non-PREDICTED children                       │
    │      update_task_model_with_spiff_task(child)            │
    └──────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                          KEY CODE LOCATIONS                                  │
└─────────────────────────────────────────────────────────────────────────────┘

📍 workflow_execution_service.py:547-596 (_run_and_save)
   ├─ try:
   │    └─ Execute tasks
   └─ finally:  ◄─── ALWAYS RUNS, even on error!
        └─ execution_strategy.add_object_to_db_session()
           └─ Saves ALL tasks to database

📍 workflow_execution_service.py:365-388 (add_object_to_db_session)
   └─ for task in get_tasks(WAITING|READY|MAYBE|LIKELY|FUTURE|ERROR):
        └─ task_service.update_task_model_with_spiff_task(task)
           └─ Does NOT filter PREDICTED children!

📍 task_service.py:198-264 (update_task_model_with_spiff_task)
   └─ update_task_model(task_model, spiff_task)
        └─ properties_json = serializer.to_dict(spiff_task)
           └─ Includes ALL children from SpiffWorkflow

📍 task_service.py:159-172 (process_spiff_task_children) ⚠️ NEVER CALLED
   └─ if child.has_state(TaskState.PREDICTED_MASK):
        └─ remove_spiff_task_from_parent()
           └─ This would prevent orphaned children!

📍 task_service.py:538-548 (remove_spiff_task_from_parent)
   └─ parent_task_model.properties_json["children"].remove(child_guid)
        └─ This cleanup never happens!


┌─────────────────────────────────────────────────────────────────────────────┐
│                        TASK STATE ANALYSIS                                   │
└─────────────────────────────────────────────────────────────────────────────┘

TaskState Values (from SpiffWorkflow):
┌────────────────┬───────┬──────────┬─────────────┬─────────────────────┐
│ State          │ Value │ Binary   │ Has         │ Saved to DB?        │
│                │       │          │ PREDICTED?  │                     │
├────────────────┼───────┼──────────┼─────────────┼─────────────────────┤
│ MAYBE          │   1   │ 0b001    │ ✅ Yes      │ ✅ Yes (line 377)   │
│ LIKELY         │   2   │ 0b010    │ ✅ Yes      │ ✅ Yes (line 378)   │
│ PREDICTED_MASK │   3   │ 0b011    │ (it's       │ N/A                 │
│                │       │          │  the mask)  │                     │
│ FUTURE         │   4   │ 0b100    │ ❌ No       │ ✅ Yes (line 379)   │
│ WAITING        │   8   │ 0b1000   │ ❌ No       │ ✅ Yes (line 374)   │
│ READY          │  16   │ 0b10000  │ ❌ No       │ ✅ Yes (line 376)   │
│ STARTED        │  32   │ 0b100000 │ ❌ No       │ ✅ Yes (line 380)   │
│ ERROR          │ 128   │ 0b...    │ ❌ No       │ ✅ Yes (line 381)   │
└────────────────┴───────┴──────────┴─────────────┴─────────────────────┘

⚠️  PROBLEM: Tasks with PREDICTED_MASK (MAYBE, LIKELY) ARE saved to DB!
    But parent task references might include children that get filtered
    somewhere else, or never fully created.


┌─────────────────────────────────────────────────────────────────────────────┐
│                          REPRODUCTION SCENARIO                               │
└─────────────────────────────────────────────────────────────────────────────┘

Most likely scenario to reproduce:

1. Parallel Gateway
   └─ Branch A: Success
   └─ Branch B: Service Task (fails) → Exclusive Gateway → Routes
   └─ Branch C: Success

When Service Task runs:
  ├─ SpiffWorkflow predicts the Exclusive Gateway will execute
  ├─ Creates gateway and its children (MAYBE/LIKELY states)
  ├─ Adds child GUIDs to service task's children array
  └─ 💥 Service task fails

In finally block:
  ├─ Service task (ERROR) gets saved with children array
  ├─ Gateway (FUTURE) gets saved
  ├─ MAYBE/LIKELY children: ?
  │   └─ Might be filtered somewhere
  │   └─ Might not be fully initialized
  │   └─ Result: Parent references them but they don't exist!
  └─ Commit to database = INCONSISTENT STATE


┌─────────────────────────────────────────────────────────────────────────────┐
│                           POTENTIAL FIXES                                    │
└─────────────────────────────────────────────────────────────────────────────┘

Option 1: Call the existing filtering logic
───────────────────────────────────────────
In workflow_execution_service.py:365-388, change:

  for waiting_spiff_task in bpmn_process_instance.get_tasks(...):
      self.task_service.update_task_model_with_spiff_task(waiting_spiff_task)

      # ADD THIS:
      self.task_service.process_spiff_task_children(waiting_spiff_task)


Option 2: Filter children before save
──────────────────────────────────────
In task_service.py:save_objects_to_database(), add:

  def save_objects_to_database(self, save_process_instance_events: bool = True):
      # Validate child references before saving
      task_guids = set(self.task_models.keys())

      for task_model in self.task_models.values():
          if "children" in task_model.properties_json:
              valid_children = [
                  c for c in task_model.properties_json["children"]
                  if c in task_guids
              ]
              if len(valid_children) != len(task_model.properties_json["children"]):
                  # Remove orphaned references
                  new_props = copy.copy(task_model.properties_json)
                  new_props["children"] = valid_children
                  task_model.properties_json = new_props

      # Continue with normal save...


Option 3: Post-process cleanup (migration)
───────────────────────────────────────────
For existing database:

  def cleanup_orphaned_child_references():
      """Remove child references that don't exist in database."""

      for process_instance in ProcessInstanceModel.query.all():
          tasks = TaskModel.query.filter_by(
              process_instance_id=process_instance.id
          ).all()

          existing_guids = {t.guid for t in tasks}

          for task in tasks:
              if "children" in task.properties_json:
                  children = task.properties_json["children"]
                  valid_children = [c for c in children if c in existing_guids]

                  if len(valid_children) != len(children):
                      task.properties_json["children"] = valid_children
                      db.session.add(task)

          db.session.commit()


Option 4: Re-serialize parents after processing children
─────────────────────────────────────────────────────────
In task_service.py:process_spiff_task_children(), add:

  def process_spiff_task_children(self, spiff_task: SpiffTask) -> None:
      for child_spiff_task in spiff_task.children:
          if child_spiff_task.has_state(TaskState.PREDICTED_MASK):
              self.__class__.remove_spiff_task_from_parent(...)
              continue
          self.update_task_model_with_spiff_task(child_spiff_task)
          self.process_spiff_task_children(child_spiff_task)

      # ADD THIS: Re-serialize parent to ensure children array is accurate
      if str(spiff_task.id) in self.task_models:
          parent_task_model = self.task_models[str(spiff_task.id)]
          new_properties = self.serializer.to_dict(spiff_task)
          parent_task_model.properties_json = new_properties


┌─────────────────────────────────────────────────────────────────────────────┐
│                         DIAGNOSTIC COMMANDS                                  │
└─────────────────────────────────────────────────────────────────────────────┘

Check for orphaned children in your database:

  # Using the diagnostic script:
  FLASK_APP=src.spiffworkflow_backend python check_orphaned_children.py <process_id>

  # Direct SQL query (MySQL):
  WITH task_guids AS (
    SELECT guid FROM task WHERE process_instance_id = <PROCESS_ID>
  )
  SELECT
    t.guid as parent_guid,
    t.state as parent_state,
    td.bpmn_identifier as parent_task,
    JSON_EXTRACT(t.properties_json, '$.children') as children
  FROM task t
  JOIN task_definition td ON t.task_definition_id = td.id
  WHERE t.process_instance_id = <PROCESS_ID>
    AND JSON_LENGTH(JSON_EXTRACT(t.properties_json, '$.children')) > 0;

  # Then manually verify each child GUID exists in task_guids


┌─────────────────────────────────────────────────────────────────────────────┐
│                              SUMMARY                                         │
└─────────────────────────────────────────────────────────────────────────────┘

ROOT CAUSE:
  The finally block in workflow_execution_service.py saves tasks directly
  without calling the PREDICTED children filtering logic that exists in
  task_service.py:process_spiff_task_children()

RESULT:
  Parent tasks can be saved with properties_json["children"] containing
  GUIDs of child tasks that don't exist in the database

WHY TESTS DON'T REPRODUCE:
  - Timing dependent
  - Requires specific SpiffWorkflow prediction behavior
  - May depend on database transaction boundaries
  - Tests use SQLite, production uses MySQL

RECOMMENDED FIX:
  Option 2 (validation before save) is safest - prevents the issue and
  cleans up any existing inconsistencies without changing execution flow
