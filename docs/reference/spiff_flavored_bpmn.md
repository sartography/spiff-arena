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

## Python Scripting Environment

Scripts within SpiffWorkflow, whether in `<bpmn:script>` elements of Script Tasks, or in `<spiffworkflow:preScript>` and `<spiffworkflow:postScript>` elements, execute in a specialized Python environment.

**Key Characteristics:**

- **No `import` Statements:** You cannot use `import` statements directly within your scripts.
- **Pre-defined Globals:** A set of commonly used modules, functions, and objects are made available globally. This means you can use them directly without importing.
- **Task Data Context:** Scripts operate within the context of the current task's data. Variables in the task data are directly accessible and can be modified. New variables created in the script are added to the task data.

**Available Globals:**

The following modules and functions are typically available in the script execution environment. For the definitive list and any environment-specific variations, refer to the `default_globals` dictionary within the `CustomBpmnScriptEngine` class in `spiffworkflow-backend/src/spiffworkflow_backend/services/process_instance_processor.py`.

- `_strptime`: A helper module for parsing dates/times (from Python's internal `_strptime`).
- `dateparser`: The `dateparser` library for parsing dates in various string formats.
- `datetime`: The `datetime` module from the Python standard library (e.g., `datetime.datetime.now()`).
- `decimal`: The `Decimal` type from the Python standard library `decimal` module for fixed and floating-point arithmetic.
- `json`: The `json` module from the Python standard library for working with JSON data (e.g., `json.dumps()`, `json.loads()`).
- `pytz`: The `pytz` library for working with timezones.
- `time`: The `time` module from the Python standard library (e.g., `time.time()`).
- `timedelta`: The `timedelta` class from the Python standard library `datetime` module.
- `uuid`: The `uuid` module from the Python standard library for generating UUIDs (e.g., `uuid.uuid4()`).
- `random`: The `random` module from the Python standard library for generating random numbers.

**Built-in Functions and Types:**
Standard Python built-in functions and types are generally available, such as:

- `dict`, `list`, `set`, `str`, `int`, `float`, `bool`
- `enumerate`, `filter`, `format`, `len`, `map`, `min`, `max`, `print`, `range`, `sum`, `zip`

**Restricted Environment:**
By default, SpiffWorkflow uses `RestrictedPython` to execute scripts. This means that while many standard library features and built-ins are available, some potentially unsafe operations might be restricted. The `safe_globals` from `RestrictedPython` augment the available built-ins.

**Custom Helper Functions:**
Additionally, helper functions defined in `spiffworkflow_backend.services.jinja_service.JinjaHelpers` are also exposed globally in the script environment.

This curated environment provides a powerful yet controlled way to implement custom logic within your BPMN processes.

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

Service Tasks in SpiffWorkflow are extended to allow for specific operations, most notably calling external HTTP services. This is configured using the `spiffworkflow:serviceTaskOperator` element within `<bpmn:extensionElements>`.

**Core Extension: `spiffworkflow:serviceTaskOperator`**

This element defines the service operation.

- **`id`**: (Required) Identifies the operator. For HTTP POST requests, this is `http/PostRequestV2`. Other operators may exist for different HTTP methods or service types.
- **`resultVariable`**: (Optional) The name of the process variable where the response from the service call will be stored. If not provided, the response isn't stored in a specific variable. The response object typically contains:
  - `body`: The response body. Often a Python dictionary/list for JSON responses, otherwise a string.
  - `status_code`: Integer HTTP status code (e.g., `200`, `404`).
  - `headers`: A Python dictionary of response headers.

**Parameters: `spiffworkflow:parameters`**

This container holds all input parameters for the service operator.

- **`spiffworkflow:parameter`**: Defines each individual parameter.
  - **`id`**: (Required) The parameter's identifier (e.g., `url`, `headers`).
  - **`type`**: (Required) The expected data type (e.g., `str`, `any`). `any` is often used for dictionaries or complex objects.
  - **`value`**: (Required) The parameter's value.
    - **As a variable name**: Provide the variable name directly (e.g., `value="my_url_variable"`).
    - **As a string literal**: Enclose in double quotes within the XML attribute (e.g., `value="&#34;https://api.example.com&#34;"`).
    - **As a JSON string literal (for `type="any"`)**: Provide a JSON formatted string (e.g., `value="{&#34;Content-Type&#34;: &#34;application/json&#34;}"`).

**Common Parameters for `http/PostRequestV2`:**

1. **`url`** (`type="str"`): (Required) The target URL for the HTTP POST request.

   ```xml
   <spiffworkflow:parameter id="url" type="str" value="&#34;https://api.example.com/submit&#34;" />
   ```

2. **`headers`** (`type="any"`): (Optional) A dictionary of HTTP headers.

   ```xml
   <spiffworkflow:parameter id="headers" type="any" value="{&#34;X-API-Key&#34;: &#34;secretkey&#34;}" />
   ```

3. **`data`** (`type="any"`): (Optional) The payload/body of the POST request. Can be a dictionary (serialized to JSON if `Content-Type` is `application/json`) or a string.

   ```xml
   <spiffworkflow:parameter id="data" type="any" value="{&#34;message&#34;: &#34;Hello!&#34;}" />
   ```

4. **`basic_auth_username`** (`type="str"`): (Optional) Username for HTTP Basic Authentication.

   ```xml
   <spiffworkflow:parameter id="basic_auth_username" type="str" value="&#34;my_user&#34;" />
   ```

5. **`basic_auth_password`** (`type="str"`): (Optional) Password for HTTP Basic Authentication. Use SpiffWorkflow's secret management: `"SPIFF_SECRET:your_secret_name"`.

   ```xml
   <spiffworkflow:parameter id="basic_auth_password" type="str" value="&#34;SPIFF_SECRET:my_api_secret&#34;" />
   ```

**Example: HTTP POST Request Service Task**

```xml
<bpmn:serviceTask id="MyHttpPostTask" name="Send POST Request">
  <bpmn:extensionElements>
    <spiffworkflow:serviceTaskOperator id="http/PostRequestV2" resultVariable="post_response">
      <spiffworkflow:parameters>
        <spiffworkflow:parameter id="url" type="str" value="&#34;https://api.example.com/submit&#34;" />
        <spiffworkflow:parameter id="headers" type="any" value="my_headers_variable" /> <!-- my_headers_variable is a process variable -->
        <spiffworkflow:parameter id="data" type="any" value="{&#34;message&#34;: &#34;Hello, world!&#34;, &#34;user_id&#34;: current_user_id}" /> <!-- current_user_id is a process variable -->
        <spiffworkflow:parameter id="basic_auth_username" type="str" value="&#34;my_user&#34;" />
        <spiffworkflow:parameter id="basic_auth_password" type="str" value="&#34;SPIFF_SECRET:my_api_secret&#34;" />
      </spiffworkflow:parameters>
    </spiffworkflow:serviceTaskOperator>
    <spiffworkflow:postScript>
      # Example: Process the result stored in 'post_response'
      if post_response and post_response.status_code == 200:
          api_call_successful = True
          response_body = post_response.body
      else:
          api_call_successful = False
          error_message = f"API call failed with status: {post_response.status_code if post_response else 'N/A'}"
    </spiffworkflow:postScript>
  </bpmn:extensionElements>
</bpmn:serviceTask>
```

**Important Notes for Service Tasks:**

- **XML Escaping**: Ensure special XML characters in literal values are escaped (e.g., `&` becomes `&amp;`).
- **Secrets**: Always use `SPIFF_SECRET:` prefix for sensitive string literals or load them securely into variables.
- **Error Handling**: Consider BPMN error boundary events to manage exceptions from service calls (e.g., network issues, HTTP 4xx/5xx errors).
- Service Tasks can also utilize `spiffworkflow:preScript` and `spiffworkflow:postScript` for logic before and after the main service call.

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

## Condition Expressions

Python will be assumed for `conditionExpression` nodes, and they do not need type or language attributes.

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
