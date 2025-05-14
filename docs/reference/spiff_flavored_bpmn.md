# Spiff-Flavored BPMN

SpiffWorkflow uses the BPMN 2.0 specification to implement extensions that provide functionality to help run your processes, particularly with Script Tasks, Service Tasks, and User Tasks. These extensions are typically defined within the `<bpmn:extensionElements>` tag of a BPMN element.

## Namespace

SpiffWorkflow extensions use the `spiffworkflow` namespace. Ensure this namespace is defined in your BPMN XML:
`xmlns:spiffworkflow="http://spiffworkflow.org/bpmn/schema/1.0/core"`

## Common Extensions

### `spiffworkflow:preScript` and `spiffworkflow:postScript`

Many task types, including User Tasks and Service Tasks, can include pre-scripts and post-scripts. These are Python scripts executed before and after the main task logic, respectively. They operate within the task's data context, meaning variables defined or modified in these scripts become part of the task's data.

Example:

```xml
<bpmn:task id="MyTaskWithScripts" name="Task with Pre/Post Scripts">
  <bpmn:extensionElements>
    <spiffworkflow:preScript>
      # Code to run before the task's main logic
      my_custom_task_status = 'pending'  # This variable is now in the task data
    </spiffworkflow:preScript>
    <spiffworkflow:postScript>
      # Code to run after the task's main logic
      my_custom_task_status = 'completed' # This updates the variable in task data
    </spiffworkflow:postScript>
  </bpmn:extensionElements>
  <!-- ... other task definitions ... -->
</bpmn:task>
```

## Script Tasks (`bpmn:scriptTask`)

A standard BPMN Script Task executes a script. SpiffWorkflow expects this script to be Python.

**Attributes:**

- `scriptFormat`: `text/x-python`
- The script content is placed directly within the `<bpmn:script>` tag.

**Execution Context:**
The script is executed within the context of the task's data. Variables are directly accessible and can be modified within the script's scope. For example, if `input_value` exists in the task data, you can use it directly and assign new variables like `calculated_value = input_value + 5`. These new or modified variables become part of the task's data.

Example:

```xml
<bpmn:scriptTask id="MyScriptTask" name="Execute Python Script" scriptFormat="python">
  <bpmn:script>
    # Access and modify task data
    calculated_value = input_value + 5  # Assuming input_value is already in the task's data
  </bpmn:script>
</bpmn:scriptTask>
```

Script Tasks can also utilize `spiffworkflow:preScript` and `spiffworkflow:postScript` as described above, which run before and after the main `<bpmn:script>` respectively.

## Service Tasks (`bpmn:serviceTask`)

While standard BPMN defines Service Tasks abstractly, SpiffWorkflow provides specific extensions to define their behavior, typically for calling external services.

**Core Extension: `spiffworkflow:serviceTaskOperator`**

This element, placed within `<bpmn:extensionElements>`, defines the operation to be performed.

- `id` (or `operationRef`): Corresponds to an `operation_name` that the script engine uses to identify the service or function to call.
- `resultVariable` (optional): Specifies the variable name in the task's data where the result of the service call will be stored.

**Parameters: `spiffworkflow:parameters`**

Nested within `spiffworkflow:serviceTaskOperator`, this element contains one or more `spiffworkflow:parameter` sub-elements to define the inputs to the service.

- `spiffworkflow:parameter`:
  - `id` (or `name`): The name of the parameter as expected by the service.
  - `type`: The data type of the parameter (e.g., `str`, `int`, `bool`).
  - `value`: An expression (Python) evaluated using variables from the task's data context to provide the parameter's value. For example, `selected_product_id` would use the value of the `selected_product_id` variable.

Example:

```xml
<bpmn:serviceTask id="CallProductLookup" name="Lookup Product Information">
  <bpmn:extensionElements>
    <spiffworkflow:serviceTaskOperator id="lookup_product_info" resultVariable="product_details">
      <spiffworkflow:parameters>
        <spiffworkflow:parameter id="product_id_param" type="str" value="selected_product_id"/> <!-- Assumes selected_product_id is a variable -->
        <spiffworkflow:parameter id="include_stock_param" type="bool" value="True"/>
      </spiffworkflow:parameters>
    </spiffworkflow:serviceTaskOperator>
    <spiffworkflow:postScript>
      # Example: Process the result stored in 'product_details'
      if product_details:  # product_details is now directly in the scope
          units_available = product_details.get('unit_available', 0) # Assign to a new variable
    </spiffworkflow:postScript>
  </bpmn:extensionElements>
</bpmn:serviceTask>
```

The SpiffWorkflow script engine's `call_service(task, operation_name, **operation_params)` method (or similar, depending on the engine version) is responsible for interpreting the `operation_name` and the evaluated `operation_params`. The result of this call is assigned to the variable specified by `resultVariable` in the task's data.

## User Tasks (`bpmn:userTask`) and Manual Tasks (`bpmn:manualTask`)

**`spiffworkflow:instructionsForEndUser`**

For User Tasks and Manual Tasks, this extension allows embedding instructions for the end-user. The content is often a Jinja2 template that can be rendered using the task's data.

Example:

```xml
<bpmn:userTask id="ReviewOrderItem" name="Review Order Item">
  <bpmn:extensionElements>
    <spiffworkflow:instructionsForEndUser>
      Please review the details for product: {{ product_name | default('N/A') }}.
      Quantity: {{ quantity | default(1) }}
      Notes: {{ customer_notes | default('None') }}
    </spiffworkflow:instructionsForEndUser>
  </bpmn:extensionElements>
</bpmn:userTask>
```

**`spiffworkflow:properties` for Form Configuration**

User Tasks can be configured to display dynamic forms using JSON Schema for data structure and validation, and optionally a UI Schema for layout and presentation. This is done via `spiffworkflow:property` elements nested within `spiffworkflow:properties`.

- `spiffworkflow:property`:
  - `name`: Specifies the type of schema file. Common values are:
    - `formJsonSchemaFilename`: The filename of the JSON Schema.
    - `formUiSchemaFilename`: The filename of the UI Schema (optional).
  - `value`: The actual filename (e.g., `my_form_schema.json`). These files are typically expected to be co-located with the BPMN process model or in a predefined location accessible to the frontend.

Example:

```xml
<bpmn:userTask id="CollectUserData" name="Collect User Data">
  <bpmn:extensionElements>
    <spiffworkflow:properties>
      <spiffworkflow:property name="formJsonSchemaFilename" value="user_data_schema.json" />
      <spiffworkflow:property name="formUiSchemaFilename" value="user_data_uischema.json" />
    </spiffworkflow:properties>
    <spiffworkflow:instructionsForEndUser>
      Please fill out the form below.
    </spiffworkflow:instructionsForEndUser>
  </bpmn:extensionElements>
</bpmn:userTask>
```

This configuration tells the SpiffWorkflow frontend to render a form based on `user_data_schema.json` and `user_data_uischema.json` when this User Task becomes active. The data submitted through this form becomes part of the task's data.

## Error Definitions (`bpmn:error`)

When defining Error Events, SpiffWorkflow allows specifying a variable name whose value should be captured as part of the error's payload when the error is thrown.

**`spiffworkflow:variableName`**

Used within a `<bpmn:error>` element's `<bpmn:extensionElements>`.

Example:

```xml
<bpmn:error id="CustomApplicationError" name="Application Error" errorCode="APP_ERR_101">
  <bpmn:extensionElements>
    <spiffworkflow:variableName>failed_item_id</spiffworkflow:variableName>
  </bpmn:extensionElements>
</bpmn:error>
```

When an error with this definition is thrown (e.g., from a Script Task or Service Task), the value of the variable `failed_item_id` from the throwing task's context can be included in the `BpmnEvent` payload, making it available to the catching error event.

This document provides an overview of common SpiffWorkflow-specific BPMN extensions. For detailed behavior, advanced configurations, and other extensions, refer to the official SpiffWorkflow documentation and examples.

## Process Model Directory

SpiffWorkflow stores process models in diretories.
Each directory contains a bpmn file (or files, in the case of call activities), JSON files representing for schemas and UI schemas, and a process_model.json file with metadata for the process model itself.

Example `process_model.json`:

```json
{
  "description": "This process model defines the how time off request and approval works",
  "display_name": "Time Off Request",
  "exception_notification_addresses": [],
  "fault_or_suspend_on_exception": "fault",
  "metadata_extraction_paths": [
    { "key": "time_off_date", "path": "time_off_date" }
  ],
  "primary_file_name": "time_off.bpmn",
  "primary_process_id": "time_off"
}
```

The `primary_file_name` must be in the same directory, and the `primary_process_id` must be found in that file, in order for the engine to know where to start execution.
The `metadata_extraction_paths` should match variables that are generated when the process runs, and these values will be indexed for reporting.
