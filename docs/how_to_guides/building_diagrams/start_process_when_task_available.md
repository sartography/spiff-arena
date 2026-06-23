# Start a Process When a Human Task Becomes Available

Spiff Arena can start another process model when a human task becomes available.
This works for User Tasks and Manual Tasks.

Use this when task availability should trigger related workflow, such as assigning follow-up work, creating an audit record, sending a message, or starting a task-specific integration process.

## How It Works

When Arena creates a new waiting human task, it checks the task for the `spiffworkflow:processModelToStartOnTaskAvailable` BPMN extension.
If the extension has a value, Arena starts that process model as a separate process instance.

The started process receives only one injected data value:

| Variable | Description |
| --- | --- |
| `task_guid` | The runtime task GUID for the newly available User Task or Manual Task. This is the identifier used in Arena task URLs and task helper scripts; it is not the BPMN task id or the human task database row id. |

The started process can use script helpers to look up any other information it needs from that task GUID.

## Configure the Task Hook

1. Create the process model that should be started when the task becomes available.
   The process should use a none start event that can be started by Arena.
2. In the source process model, select the User Task or Manual Task.
3. In the properties panel, open **Task Hooks**.
4. Set **Process Model to Start on Task Available** to the target process model identifier.
   This is the process model path, such as `task-hooks/task-available`.
5. Save the source process model and start a new process instance.

Adding the hook to a task that is already waiting will not retrigger the hook.
Start a new source process instance to test a new configuration.

## BPMN XML

The modeler writes the hook as a SpiffWorkflow extension element:

```xml
<bpmn:userTask id="ReviewRequest" name="Review request">
  <bpmn:extensionElements>
    <spiffworkflow:processModelToStartOnTaskAvailable>task-hooks/task-available</spiffworkflow:processModelToStartOnTaskAvailable>
  </bpmn:extensionElements>
</bpmn:userTask>
```

Manual Tasks use the same extension inside the task's `<bpmn:extensionElements>`.
For the full extension naming reference, see [Spiff-Flavored BPMN](/reference/spiff_flavored_bpmn).

## Get Task Details in the Started Process

Because only the runtime task GUID is injected, use scripts in the started process to derive the details needed for that workflow.

For example:

```python
task_url = get_url_for_task(task_guid)
public_task_url = get_url_for_task(task_guid, public=True)
potential_owners = get_task_potential_owners(task_guid)
usernames = potential_owners["users"]
groups = potential_owners["groups"]
```

`get_url_for_task(task_guid)` returns the full Arena URL for the task, which is appropriate to include in a user notification so the user can go directly to the exact piece of work they need to complete.
Use the `public=True` option only when the task is configured for public completion.
`get_task_potential_owners(task_guid)` returns the usernames and group identifiers that can complete the task.
