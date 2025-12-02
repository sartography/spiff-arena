# Use Human Task Metadata

This guide will walk you through the steps to create a process model that attaches metadata to human tasks. This metadata can be used to provide additional information to front-end applications, for example, to display a custom icon or link.

## Step 1: Define the Process Model

In your BPMN diagram, select the User Task to which you want to add metadata. In the properties panel, go to the "Extensions" tab and add a new "spiffworkflow:taskMetadataValues" extension.

Within this extension, you can add multiple `spiffworkflow:taskMetadataValue` elements, each with a `name` and a `value`.

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

Here is a complete example of a User Task with both static and dynamic metadata:

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

## Step 2: Configure the Frontend

To make use of this metadata in the frontend, you will need to configure the `REACT_APP_HUMAN_TASK_METADATA` environment variable. This variable should be set to a JSON string or a list of strings that defines the metadata to be displayed.

For example, to display the `icon` and `my_link` metadata, you would set the following environment variable:

```
REACT_APP_HUMAN_TASK_METADATA='["icon", "my_link"]'
```

This will make the metadata available in the frontend application, where it can be used to customize the display of human tasks.
