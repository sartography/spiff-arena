# Sub-Processes and Call Activities

Sub-processes and call activities are both useful for simplifying and organizing complex workflows within larger processes. They have distinct purposes and are used in different scenarios.

**Reasons to use a Sub-Process or Call Activity:**

- Consolidating tasks with common features or forming a distinct functionality, such as a Notification Gateway that constructs and sends notifications like emails.

- Grouping tasks where a boundary event can efficiently be applied to the entire group, avoiding the need to assign conditions or timers individually to each task.

## Call Process

![active_call_process](images/active_call_process.png)

A call process encapsulates part of a workflow and can be reused across multiple processes. It functions as a stand-alone process that can be called into action by other processes. Using a call process eliminates redundancy and ensures consistent execution of process steps.

**When to use a Call Process:**

- **Reusability:** When a set of activities is reused in multiple main processes, defining it as a call process allows for easy reuse by calling the process.

- **Reducing Complexity:** Breaking down a complex main process into smaller, manageable call processes can make it easier to understand and maintain.

- **Version Control:** If a process may undergo changes over time but is used in multiple places, defining it as a call process allows changes to be made in one place and propagated to all instances where the process is used.

- **Delegation:** When different individuals or teams are responsible for executing tasks within a process, a call activity can be assigned to the most appropriate person or team.

- **Access Control:** If a specific segment of a process should not be available to every user, converting it into a call process helps establish access control. More information about this can be found in the [Admin and Permission](../DevOps_installation_integration/admin_and_permissions.md) section.

## Sub-Processes

![active_subtask](images/active_subprocess.png)

Sub-processes are typically used within a single process and are not reusable across multiple processes like call activities. When the conditions for reusability are not necessary, a sub-process is usually the preferred option.

**When to use a Sub-Process:**

- **Consolidating Similar Functionalities:** When a group of tasks are closely related and work well together, but do not need to be used or replicated elsewhere in other processes.

- **Not Requiring a Call Activity:** When tasks do not meet the conditions required for a call activity, a sub-process can achieve the same goal.

- **Applying Conditions or Events:** When specific conditions or events, such as a timer event, need to be applied to a set of tasks that do not collectively form a reusable workflow that can be called as a separate process.
