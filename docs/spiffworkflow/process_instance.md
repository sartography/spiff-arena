# Navigating Spiffworkflow

## What is a Process Instance

A process instance refers to a specific occurrence. Think of a process instance as an individual journey through a predefined set of steps and rules that make up a larger process. For example, let's consider a purchase order process. Each time a purchase order is initiated and goes through the required steps, such as approval, payment, and fulfillment, it represents a distinct process instance and will have a specific id and data specific to the instance. 

Each Process Instance would have started at the starting point and moved on to subsequent steps. The data it collects along its path is unique to that instance. You therefor have to know how to locate a process instance. 

Follow the following steps to understand how to locate a process instance:
% [How to find an Instance assigned to someone else](/how_to/find_an_Instance_assigned_to_someone_else)
% [How to find an Instance assigned to myself](https://github.com/sartography/spiff-arena/blob/main/docs/how_to/find_an_Instance_assigned_to_myself.md)

## ℹ Information associated with an instance

| Field Name | Description |
|------------|-------------|
| **Started By** | Specifies the initiator or originator of the process instance. wWould usually be a a username or email. |
| **Current Diagram** | Specifies the current diagram where the active process instance can be found. |
| **Started** | The timestamp of when the parent process was started.|
| **Updated At** | Specifies the current diagram where the active process instance can be found. |
| **Process model revision** | The timestamp of when the parent process was started.|
| **Status** | Specifies the current diagram where the active process instance can be found.|

---

## ✅ Statuses

The status of a process instance represents its current state or condition, reflecting its progress and execution. The process status is not necessarily bound to a chronological order and can transition between multiple statuses over time.

| Status    | Image     | Description |
|-----------|-----------------|-------|
| **User input required** |![Image description](images/user_input_required.png) |  When a process instance reaches a user task or a point in the process where user input is necessary, the status is set to "User input required." This status indicates that the process cannot proceed further until the user provides the required information or completes the assigned task.   |
| **Terminated**     |                  |       |
| **Completed**     |                  |       |
% | **Suspended**   |![Image description](images/suspended.png)              | During the suspension period, the process instance remains in a state of temporary pause, and the execution is halted. Once the cause of the suspension is resolved, the process instance can be manually updated to reflect a new location or metadata. A suspened process can be resumed: [How to resume a process](https://github.com/sartography/spiff-arena/blob/main/docs/how_to/resume_a_process.md)    |
| **Error**     |                  |  An error indicates that a process instance has encountered an error or exception during its execution. It signifies that there is an issue or problem that needs to be addressed before the process can proceed further.   |

---

## 🚫 Errors

When a process instance encounters an error, it is typically unable to continue executing as intended. The error could be caused by various factors, such as:

**Validation Failure:** If the process instance fails to meet certain validation criteria or encounters invalid data, it may result in an error status.

**System or Service Failure:** Errors can occur if there are technical issues with the underlying systems or services that the process relies upon. These could include connectivity problems, server failures, or service unavailability.

**Business Rule Violation:** If a process instance violates a predefined business rule or policy, it may trigger an error status.

**Exception Handling:** Certain exceptional scenarios, such as unexpected conditions or exceptional events, can lead to errors within the process instance.
