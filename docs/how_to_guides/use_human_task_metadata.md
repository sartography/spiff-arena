# Use Human Task Metadata

This guide will walk you through the steps to create a process model that attaches custom metadata to human tasks.
This metadata can be used to provide additional information to frontend applications.
For example, you could display a custom icon or link for each task the process requires someone to complete.
This feature would be configured by system administrators and would allow BPMN process authors to make use of that configuration to dynamically set the metadata.

## Step 1: Configure the Frontend

Before you can add metadata to your tasks, you need to configure the frontend to recognize which metadata fields are available.
Without this configuration, the metadata fields will not appear in the properties panel.

To configure the available metadata fields, you need to set a task metadata environment variable.
This variable should be set to a JSON string or a list of strings that defines the metadata fields that will be available.

For example, to make `icon` and `my_link` metadata fields available, you would set the following environment variable:

```
VITE_TASK_METADATA='["icon", "my_link"]'
```

You can also include titles and descriptions to help people building diagrams understand what each field is for:

```
VITE_TASK_METADATA='[{"name":"icon","label": "Icon","description": "Using font awesome icons. Something like fa-user"},{"name": "my_link","description": "This link will be included when end users complete the task"}]'
```

When developing locally, use the env var `VITE_TASK_METADATA`.
In production environments, or even if you are using a built docker image of spiffworkflow-frontend, specify `SPIFFWORKFLOW_FRONTEND_RUNTIME_CONFIG_TASK_METADATA`.

Once configured, these metadata fields will be available in the properties panel when configuring the diagram's user tasks.

## Step 2: Add Metadata to User Tasks

In your BPMN diagram, select the User Task to which you want to add metadata.
In the properties panel, go to the "Task Metadata" group.
If the system has been configured to allow `icon` and `my_link`, these two fields will be available to fill out.

When you fill out the values for each metadata variable in any given user task, you can do so with a static value or a dynamic value (which can use future running process instance data).

For static metadata, the `value` is a literal string, like `'fa-user'`.
For dynamic metadata, the `value` is an expression that will be evaluated when the task becomes available for completion, like `f'https://example.com/details/{my_var}'`.

In this example, `my_var` is a process variable that will be substituted into the URL.

For reference, this is an example of the resulting BPMN XML for both static and dynamic metadata:

```xml
<bpmn:userTask id="Activity_1gqykqt" name="User Task with Metadata">
  <bpmn:extensionElements>
    <spiffworkflow:taskMetadataValues>
      <spiffworkflow:taskMetadataValue name="icon" value="'fa-user'" />
      <spiffworkflow:taskMetadataValue name="my_link" value="f'https://example.com/details/{my_var}'" />
    </spiffworkflow:taskMetadataValues>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_0b04rbg</bpmn:incoming>
  <bpmn:outgoing>Flow_13mlau2</bpmn:outgoing>
</bpmn:userTask>
```

## Step 3: Start a process instance and observe the result

When the process instance executes, it will store each of the task metadata values in the system's database, associated with the appropriate human task.
When lists of human tasks are fetched via the API, the metadata keys and values will be returned.
