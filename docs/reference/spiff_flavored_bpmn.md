# SpiffWorkflow BPMN Extensions

SpiffWorkflow extends the standard BPMN 2.0 specification to provide enhanced functionality, particularly for automated tasks like Script Tasks and Service Tasks. These extensions are typically defined within the `<bpmn:extensionElements>` tag of a BPMN element.

## Namespace

SpiffWorkflow extensions typically use the `spiffworkflow` namespace. Ensure this namespace is defined in your BPMN XML, for example:
`xmlns:spiffworkflow="http://spiffworkflow.org/bpmn/extensions/1.0"`

## Common Extensions

### `spiffworkflow:preScript` and `spiffworkflow:postScript`

Many task types, including User Tasks and Service Tasks, can include pre-scripts and post-scripts. These are Python scripts executed before and after the main task logic, respectively. They operate within the task's data context.

Example:

```xml
<bpmn:task id="MyTaskWithScripts" name="Task with Pre/Post Scripts">
  <bpmn:extensionElements>
    <spiffworkflow:preScript>
      # Code to run before the task's main logic
      my_custom_task_status = 'pending'
    </spiffworkflow:preScript>
    <spiffworkflow:postScript>
      # Code to run after the task's main logic
      my_custom_task_status = 'completed'
    </spiffworkflow:postScript>
  </bpmn:extensionElements>
  <!-- ... other task definitions ... -->
</bpmn:task>
```

## Script Tasks (`bpmn:scriptTask`)

A standard BPMN Script Task executes a script. SpiffWorkflow expects this script to be Python.

**Attributes:**

- `scriptFormat`: Should be `text/python` or a similar Python identifier (e.g., `application/x-python`).
- The script content is placed directly within the `<bpmn:script>` tag.

**Execution Context:**
The script is executed within the context of the task's data. Variables in `task.data` (a dictionary-like object) are directly accessible and can be modified.

Example:

```xml
<bpmn:scriptTask id="MyScriptTask" name="Execute Python Script" scriptFormat="text/python">
  <bpmn:script>
    # Access and modify task data
    data['calculated_value'] = data.get('input_value', 0) + 5
    print(f"Calculated value: {data['calculated_value']}")
  </bpmn:script>
</bpmn:scriptTask>
```

Script Tasks can also utilize `spiffworkflow:preScript` and `spiffworkflow:postScript` as described above, which run before and after the main `<bpmn:script>` respectively.

## Service Tasks (`bpmn:serviceTask`)

While standard BPMN defines Service Tasks abstractly, SpiffWorkflow provides specific extensions to define their behavior, typically for calling external services or functions defined within the SpiffWorkflow script engine.

**Core Extension: `spiffworkflow:serviceTaskOperator`**

This element, placed within `<bpmn:extensionElements>`, defines the operation to be performed.

- `id` (or `operationRef`): Corresponds to an `operation_name` that the script engine uses to identify the service or function to call.
- `resultVariable` (optional): Specifies the variable name in the task's data where the result of the service call will be stored.

**Parameters: `spiffworkflow:parameters`**

Nested within `spiffworkflow:serviceTaskOperator`, this element contains one or more `spiffworkflow:parameter` sub-elements to define the inputs to the service.

- `spiffworkflow:parameter`:
  - `id` (or `name`): The name of the parameter as expected by the service.
  - `type`: The data type of the parameter (e.g., `str`, `int`, `bool`). While SpiffWorkflow's Python script engine is flexible with types, specifying can be good for clarity.
  - `value`: An expression (Python) to be evaluated against the task's data to provide the parameter's value.

Example:

```xml
<bpmn:serviceTask id="CallProductLookup" name="Lookup Product Information">
  <bpmn:extensionElements>
    <spiffworkflow:serviceTaskOperator id="lookup_product_info" resultVariable="product_details">
      <spiffworkflow:parameters>
        <spiffworkflow:parameter id="product_name" type="str" value="data['selected_product_id']"/>
        <spiffworkflow:parameter id="include_stock" type="bool" value="True"/>
      </spiffworkflow:parameters>
    </spiffworkflow:serviceTaskOperator>
    <spiffworkflow:postScript>
      # Example: Process the result stored in 'product_details'
      if data.get('product_details'):
          print(f"Service returned: {data['product_details']}")
          data['stock_available'] = data['product_details'].get('stock_level', 0)
    </spiffworkflow:postScript>
  </bpmn:extensionElements>
</bpmn:serviceTask>
```

The SpiffWorkflow script engine's `call_service(task_data, operation_name, operation_params)` method is responsible for interpreting the `operation_name` and the evaluated `operation_params`. The result of this call is typically assigned to the `resultVariable` in the task's data.

## User Tasks (`bpmn:userTask`) and Manual Tasks (`bpmn:manualTask`)

**`spiffworkflow:instructionsForEndUser`**

For User Tasks and Manual Tasks, this extension allows embedding instructions for the end-user. The content is often a Jinja2 template that can be rendered using the task's data.

Example:

```xml
<bpmn:userTask id="ReviewOrderItem" name="Review Order Item">
  <bpmn:extensionElements>
    <spiffworkflow:instructionsForEndUser>
      Please review the details for product: {{ data.get('product_name', 'N/A') }}.
      Quantity: {{ data.get('quantity', 1) }}
      Notes: {{ data.get('customer_notes', 'None') }}
    </spiffworkflow:instructionsForEndUser>
  </bpmn:extensionElements>
</bpmn:userTask>
```

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
