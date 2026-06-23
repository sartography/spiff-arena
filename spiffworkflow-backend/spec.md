running a process model when a human task becomes available

how? via per-task process model

allow a configuration on each user or manual task that indicates the process model that should be run when the task becomes available. the extension is `spiffworkflow:processModelToStartOnTaskAvailable`, stored as a named extension element.

the task-available process instance should receive only `task_guid`. the triggered process model can derive related data with script helpers:

- `get_url_for_task(task_guid)` for the full frontend task url.
- `get_task_potential_owners(task_guid)` for usernames and group identifiers of all users who can complete the task.

probably the process model should not start with a message start event, but just a normal none start event. then we can have code that "manually" injects the variables they might need.
