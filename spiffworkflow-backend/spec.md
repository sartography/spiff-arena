running a process model when a user task becomes available

how? via per-task process model

allow a configuration on each user task that indicates the process model that should be run when the user task becomes available. the extension is `spiffworkflow:processModelToStartOnTaskAvailable`, stored as a named extension element.

the task-available process instance should receive only `task_guid`. the triggered process model can derive related data with script helpers:

- `get_url_for_task(task_guid)` for the full frontend task url.
- `get_users_assigned_to_task(task_guid)` for assigned usernames.
- `get_groups_assigned_to_task(task_guid)` for assigned group identifiers/names.
- `get_usernames_waiting_for_task(task_guid)` for pending usernames that do not have users yet.

probably the process model should not start with a message start event, but just a normal none start event. then we can have code that "manually" injects the variables they might need.
