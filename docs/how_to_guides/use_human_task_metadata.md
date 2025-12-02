# Use Human Task Metadata

This guide will walk you through the steps to create a process model that attaches custom metadata to human tasks.
This metadata can be used to provide additional information to front-end applications, for example, to display a custom icon or link.
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
VITE_TASK_METADATA='[{"name":"icon","label": "Icon","description":""},{"name": "my_link","description": "This link will be included when end users complete the task"}]'
```

When developing locally, use `VITE_TASK_METADATA`.
In production environments, or even if you are using a built docker image of spiffworkflow-frontend, specify `SPIFFWORKFLOW_FRONTEND_RUNTIME_CONFIG_TASK_METADATA`.

Once configured, these metadata fields will be available in the properties panel as the "Task Metadata" group when you select a User Task.

## Step 2: Add Metadata to User Tasks

In your BPMN diagram, select the User Task to which you want to add metadata.
In the properties panel, go to the "Task Metadata" group.
If the system has been configured to allow `icon` and `my_link`, these two fields will be available to fill out.

### Static Metadata

For static metadata, the `value` is a literal string. For example, to add a static icon to a task, you could define the following:

```xml
<spiffworkflow:taskMetadataValues>
  <spiffworkflow:taskMetadataValue name="'icon'" value="'fa-solid fa-user'" />
</spiffworkflow:taskMetadataValues>
```

Note the single quotes around both the name and the value.

### Dynamic Metadata

For dynamic metadata, the `value` is an expression that will be evaluated when the task is created. For example, to add a dynamic link to a task, you could define the following:

```xml
<spiffworkflow:taskMetadataValues>
  <spiffworkflow:taskMetadataValue name="'my_link'" value="f'https://example.com/details/{my_var}'" />
</spiffworkflow:taskMetadataValues>
```

In this example, `my_var` is a process variable that will be substituted into the URL.

Here is a complete example showing the underlying XML format with both static and dynamic metadata:

```xml
<bpmn:userTask id="Activity_1gqykqt" name="User Task with Metadata">
  <bpmn:extensionElements>
    <spiffworkflow:taskMetadataValues>
      <spiffworkflow:taskMetadataValue name="'icon'" value="'fa-solid fa-user'" />
      <spiffworkflow:taskMetadataValue name="'my_link'" value="f'https://example.com/details/{my_var}'" />
    </spiffworkflow:taskMetadataValues>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_0b04rbg</bpmn:incoming>
  <bpmn:outgoing>Flow_13mlau2</bpmn:outgoing>
</bpmn:userTask>
```

Once you've added metadata to your tasks, it will be available in the frontend application, where it can be used to customize the display of human tasks.
