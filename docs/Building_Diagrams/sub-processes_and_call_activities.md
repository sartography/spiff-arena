# Sub-Processes and Call Activities

Sub-processes and call activities are both useful for simplifying and organizing complex workflows within larger processes.
They serve distinct purposes and are used in different scenarios.

**Reasons to use Sub-Processes or Call Activities:**

- Consolidate tasks that either have common features or collaboratively form a distinct functionality.
For example, a Notification Gateway, which includes script tasks and a service task, works together to construct and send a notification, such as an email.

- Group tasks where a Boundary Event can be efficiently applied to the entire group.
For instance, instead of individually assigning a condition or timer to each task, all tasks can be included within a sub-process or call activity, where the condition or timer inherently applies to all the contained tasks.

## Call Process

![active_call_process](images/active_call_process.png)

A Call Process is similar to a Sub-Process in that it encapsulates part of a workflow, but it is designed to be reused across multiple different processes.
It's essentially a stand-alone process that can be "called" into action as required by other processes.
Using a Call Process can help to eliminate redundancy and ensure consistent execution of the process steps.

**When to use a Call Process:**

- **Reusability:** When a set of activities is reused in multiple main processes, defining it as a call process allows for easy reuse by calling the process.

- **Reducing Complexity:** Breaking down a complex main process into smaller, manageable call processes can make it easier to understand and maintain.

- **Version Control:** If a process may undergo changes over time but is used in multiple places, defining it as a call process allows changes to be made in one place and propagated to all instances where the process is used.

- **Delegation:** When different individuals or teams are responsible for executing tasks within a process, a call activity can be assigned to the most appropriate person or team.

- **Access Control:** If a specific segment of a process should not be available to every user, converting it into a call process helps establish access control.
More information about this can be found in the [Admin and Permission](../DevOps_installation_integration/admin_and_permissions.md) section.

## Sub-Processes

**When to use a Sub-Process:**

- **Consolidate similar functionalities:** When you have a group of tasks that are closely related and work well together but don't need to be used or replicated elsewhere in other processes.

- **Call Activity is not required:** When these tasks don't meet the conditions needed for a call activity, a sub-process can achieve the same goal.

- **Conditions or events need to be applied:** When specific conditions or events, such as a timer event, need to be applied to a set of tasks, but these tasks do not collectively form a reusable workflow that can be called as a separate process.
