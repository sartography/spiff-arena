# Spiff-Flavored BPMN

SpiffWorkflow uses the BPMN 2.0 specification to implement extensions that provide functionality to help run your processes, particularly with Script Tasks, Service Tasks, and User Tasks. These extensions are typically defined within the `<bpmn:extensionElements>` tag of a BPMN element.

## Namespace

SpiffWorkflow extensions use the `spiffworkflow` namespace. Ensure this namespace is defined in your BPMN XML:
`xmlns:spiffworkflow="http://spiffworkflow.org/bpmn/schema/1.0/core"`

## XML Extension Name Reference

This section lists the `spiffworkflow` XML names that Spiff Arena uses.
It is meant as a quick naming reference, not a full behavior guide.

The usual pattern is lower camel case for XML element and attribute names.
For example, the modeler moddle type `PreScript` serializes as `<spiffworkflow:preScript>`.
Generic Arena task configuration is usually stored as lower-camel-case `name` values inside `<spiffworkflow:property>`.

SpiffWorkflow parses direct `spiffworkflow:*` elements inside `<bpmn:extensionElements>` into `task_spec.extensions`.
Some names are interpreted by SpiffWorkflow itself; others are Arena conventions that SpiffWorkflow only carries as extension data.

In the tables below:

- "Extension element with text" means an element whose value is the text between the opening and closing XML tags, such as `<spiffworkflow:preScript>...</spiffworkflow:preScript>`.
- "Nested under ..." means the element is only used inside another `spiffworkflow` element, not directly under `<bpmn:extensionElements>`.
- "Extension attribute" means a `spiffworkflow:*` attribute on a BPMN element. Those rows are the only attribute rows.
- "Engine behavior" means the SpiffWorkflow library has parser or runtime code that interprets the value. "Parsed extension data" means the library exposes the value in `task_spec.extensions`, but Arena owns the behavior. "Arena/modeler only" means the name is used by Arena or `bpmn-js-spiffworkflow`, not by SpiffWorkflow engine code.

### Elements and Attributes

These names are `spiffworkflow` XML elements or namespace attributes used by Arena.
Extension elements appear under `<bpmn:extensionElements>` unless the form says they are nested under another element.

| XML name | Form | Arena use | SpiffWorkflow library support |
| --- | --- | --- | --- |
| `spiffworkflow:preScript` | Extension element with text | Python to run before an activity or event task. | Engine behavior. |
| `spiffworkflow:postScript` | Extension element with text | Python to run after an activity or event task. | Engine behavior. |
| `spiffworkflow:calledDecisionId` | Extension element with text | DMN decision id for a business rule task. | Engine behavior. |
| `spiffworkflow:instructionsForEndUser` | Extension element with text | Markdown/Jinja instructions rendered by Arena for human-facing tasks. | Parsed extension data. Defined by the SpiffWorkflow library schema, but rendered by Arena. |
| `spiffworkflow:messagePayload` | Extension element with text | Python expression for message payload data. | Engine behavior. |
| `spiffworkflow:messageVariable` | Extension element with text | Process variable name for received message payload data. | Engine behavior. |
| `spiffworkflow:payloadExpression` | Extension element with text | Payload expression on signal, error, and escalation definitions. | Engine behavior. |
| `spiffworkflow:variableName` | Extension element with text | Variable name for user task form output or event payload output. | Engine behavior. |
| `spiffworkflow:processVariableCorrelation` | Extension element containing `propertyId` and `expression` | Message correlation against process data. | Engine behavior. |
| `spiffworkflow:propertyId` | Nested under `spiffworkflow:processVariableCorrelation`; text value | Correlation property id. | Engine behavior. |
| `spiffworkflow:expression` | Nested under `spiffworkflow:processVariableCorrelation`; text value | Correlation expression. | Engine behavior. |
| `spiffworkflow:properties` | Extension element containing `property` rows | Generic name/value task configuration container. | Parsed extension data. |
| `spiffworkflow:property` | Nested under `spiffworkflow:properties`; has `name` and `value` attributes | One generic task configuration value. | Parsed extension data; property names are application conventions. |
| `spiffworkflow:serviceTaskOperator` | Extension element with `id`, `resultVariable`, `parameters`, and optional `retry` | Connector/operator configuration for service tasks. | Engine behavior. |
| `spiffworkflow:parameters` | Nested under `spiffworkflow:serviceTaskOperator` | Parameter container. | Engine behavior. |
| `spiffworkflow:parameter` | Nested under `spiffworkflow:parameters`; has `id`, `type`, and optional `value` attributes | One connector/operator parameter. | Engine behavior. |
| `spiffworkflow:retry` | Nested under `spiffworkflow:serviceTaskOperator`; has `retries` and `backoff_base` attributes | Retry settings for the service task operator. | Engine behavior. |
| `spiffworkflow:unitTests` | Extension element containing `unitTest` rows | Script task unit test container. | Parsed extension data. |
| `spiffworkflow:unitTest` | Nested under `spiffworkflow:unitTests`; has `id` attribute | One script task unit test. | Parsed extension data. |
| `spiffworkflow:inputJson` | Nested under `spiffworkflow:unitTest`; text value | Unit test input JSON. | Parsed extension data. |
| `spiffworkflow:expectedOutputJson` | Nested under `spiffworkflow:unitTest`; text value | Unit test expected output JSON. | Parsed extension data. |
| `spiffworkflow:taskMetadataValues` | Extension element containing `taskMetadataValue` rows | Human task metadata container. | Parsed extension data. |
| `spiffworkflow:taskMetadataValue` | Nested under `spiffworkflow:taskMetadataValues`; has `name` and `value` attributes | One evaluated human task metadata expression. | Parsed extension data. |
| `spiffworkflow:scriptsOnInstances` | Extension attribute on `bpmn:multiInstanceLoopCharacteristics` or `bpmn:standardLoopCharacteristics` | Run pre/post scripts on each loop instance instead of only the outer loop task. | Engine behavior. |
| `spiffworkflow:allowGuest` | Extension element with boolean text | Allows a message start or user task to be completed through Arena public routes. | Parsed extension data; Arena owns the behavior. |
| `spiffworkflow:guestConfirmation` | Extension element with text | Markdown/Jinja confirmation shown after public completion. | Parsed extension data; Arena owns the behavior. |
| `spiffworkflow:signalButtonLabel` | Extension element with text | Label for Arena signal event action buttons. | Parsed extension data; Arena owns the behavior. |
| `spiffworkflow:processModelToStartOnTaskAvailable` | Extension element with text | Process model to start when an Arena user or manual task becomes available. | Parsed extension data; Arena owns the behavior. |
| `spiffworkflow:category` | Extension element with text on a data object | Arena data object category used for process data display and access decisions. | Arena/frontend behavior. |
| `spiffworkflow:isMatchingCorrelation` | Extension attribute on message-capable events/tasks | Tells Arena message tooling that process-variable correlation matching is enabled. | Arena/modeler only. |
| `spiffworkflow:isOutputSynced` | Extension attribute on a multi-instance subprocess/activity | Tells Arena/modeler whether multi-instance output data should be synchronized. | Arena/modeler only. |
| `spiffworkflow:jsonSchemaId` | Extension attribute on `bpmn:message` | Links a BPMN message to an Arena message JSON schema. | Arena/modeler only. |

Extension attributes are valid BPMN extension points, but for new Arena task settings the safer default is usually a named element inside `<bpmn:extensionElements>`.
That path is parsed by the SpiffWorkflow library and gives the XML name its own domain meaning.
Use an extension attribute only when the value is a small flag or identifier that naturally belongs directly on an existing BPMN element and both the modeler and runtime code explicitly support it.

### Property Names

SpiffWorkflow parses `<spiffworkflow:properties>` into a generic dictionary.
Arena uses that generic SpiffWorkflow extension point for Arena-specific configuration values.
These are not separate XML elements; they are `name` attributes on `<spiffworkflow:property>`.

| Property name | Example XML | Arena use | SpiffWorkflow library support |
| --- | --- | --- | --- |
| `formJsonSchemaFilename` | `<spiffworkflow:property name="formJsonSchemaFilename" value="request-schema.json" />` | JSON Schema file for a user task form. | SpiffWorkflow parses the generic property; Arena owns this property name and behavior. |
| `formUiSchemaFilename` | `<spiffworkflow:property name="formUiSchemaFilename" value="request-uischema.json" />` | UI Schema file for a user task form. | SpiffWorkflow parses the generic property; Arena owns this property name and behavior. |

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

The following modules and functions are typically available in the script execution environment.

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

Notably, `print` is not available.
Instead, getting information to humans can be handled via `instructionsForEndUser` in human tasks and manual tasks.

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

- **`id`**: (Required) Identifies the operator. For HTTP POST requests, this is `http/PostRequest`. Other operators may exist for different HTTP methods or service types.
- **`resultVariable`**: (Optional) The name of the process variable where the response from the service call will be stored. If not provided, the response isn't stored in a specific variable. The response stored in `resultVariable` is a dict that contains the following:
  - `body`: The response body. Often a Python dictionary/list for JSON responses, otherwise a string.
  - `status_code`: Integer HTTP status code (e.g., `200`, `404`).

So if your `resultVariable` is `hotResponse`, you can access the body with `hotResponse["body"]` and the status code with `hotResponse["status_code"]`.

**Parameters: `spiffworkflow:parameters`**

This container holds all input parameters for the service operator.

- **`spiffworkflow:parameter`**: Defines each individual parameter.
  - **`id`**: (Required) The parameter's identifier (e.g., `url`, `headers`).
  - **`type`**: (Required) The expected data type (e.g., `str`, `any`). `any` is often used for dictionaries or complex objects.
  - **`value`**: (Required) The parameter's value.
    - **As a variable name**: Provide the variable name directly (e.g., `value="my_url_variable"`).
    - **As a string literal**: Enclose in double quotes within the XML attribute (e.g., `value="&#34;https://api.example.com&#34;"`).
    - **As a JSON string literal (for `type="any"`)**: Provide a JSON formatted string (e.g., `value="{&#34;Content-Type&#34;: &#34;application/json&#34;}"`).

**Common Parameters for `http/PostRequest`:**

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
    <spiffworkflow:serviceTaskOperator id="http/PostRequest" resultVariable="post_response">
      <spiffworkflow:parameters>
        <spiffworkflow:parameter id="url" type="str" value="&#34;https://api.example.com/submit&#34;" />
        <spiffworkflow:parameter id="headers" type="any" value="my_headers_variable" /> <!-- my_headers_variable is a dict process variable -->
        <spiffworkflow:parameter id="data" type="any" value="request_data_var" /> <!-- request_data_var is a dict process variable -->
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

- **Parameter values**: It's probably better to assign dictionary values for headers and data in script tasks or pre scripts and then referencing these vars rather than using escaped dictionary values inline in the parameter node attribute.
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

Before the frontend receives a User Task form, Spiff Arena renders the referenced JSON Schema and UI Schema files through Jinja using the task data for that task.
This allows process authors to build dynamic form labels, options, visibility settings, and schema fragments without using custom frontend code.

The final rendered schema must be valid JSON.
Use the `tojson` filter when injecting strings, lists, dictionaries, booleans, or numbers into JSON Schema or UI Schema files.

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
