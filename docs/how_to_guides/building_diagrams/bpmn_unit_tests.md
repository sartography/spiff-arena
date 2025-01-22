# BPMN Unit Tests
BPMN Unit Tests enable authors to validate their process models through automated testing. These tests help ensure that your models function correctly by providing faster feedback, mocking inputs for user tasks, service tasks, and script tasks, and simulating various execution scenarios.
Here's why you should use unit tests:
- **Quick Feedback:** Test your models faster than manual execution.
- **Mock Inputs:** Simulate form inputs and service task outputs.
- **Branch Coverage:** Test various branches of your process model by providing different inputs.
- **Confidence:** Validate initial functionality and ensure future changes don’t break the process.

Lets take a look at in-depth discussion on the two ways of creating BPMN Unit Tests: through a test JSON file and via the properties panel. 

## Creating Unit Tests with a Test JSON File
This method involves manually creating a JSON file to define unit tests for your BPMN process. It is especially useful when you want more control over the test configuration or need to test multiple scenarios simultaneously.

### Steps to Create Unit Tests with JSON

1. **Create the JSON File:**
   - Navigate to your BPMN model and create a JSON file named based on your BPMN file.
   - Example: For `example_process.bpmn`, create `test_example_process.json`.

2. **Define the Test Cases:**
   - Structure the JSON file to include:
     - Test names.
     - Tasks to test (with input data).
     - Expected output.

3. **Example JSON File:**

   ```json
   {
     "test_case_1": {
       "tasks": {
         "ServiceTaskProcess:service_task_one": {
           "data": [{ "the_result": "mocked_service_result" }]
         }
       },
       "expected_output_json": {
         "the_result": "mocked_service_result"
       }
     },
     "test_case_2": {
       "tasks": {
         "user_task_1": {
           "data": [{ "input_field": "user_input" }]
         }
       },
       "expected_output_json": {
         "input_field": "user_input"
       }
     }
   }
   ```
**`test_case_1`**:
  - Mocks a Service Task (`service_task_one`) output as `"mocked_service_result"`.
  - Verifies that the process completes with the expected output: `"mocked_service_result"`.

**`test_case_2`**:
  - Simulates a User Task (`user_task_1`) where the user enters `"user_input"`.
  - Ensures the process captures this input correctly in the output.

## Creating Unit Tests Through the Properties Panel
This method uses the BPMN editor’s **properties panel** to create unit tests for specific tasks directly in the UI. It is especially useful for **script tasks** or when you prefer an intuitive, UI-driven approach.

### Steps to Create Unit Tests via Properties Panel

1. **Select the Task to Test:**
    - Open your BPMN model and select the specific task (e.g., Script Task or Service Task).

2. **Locate the Unit Tests Section:**
    - In the properties panel, look for the **“Unit Tests”** section.

![model_convention](/images/unit_test_properties_panel.png)

3. **Define the Test:**
    - Click the **`+`** button to add a new unit test.
    - Provide:
      - **ID**: A unique identifier for the test.
      - **Input JSON**: Mock the input data for the task.
      - **Expected Output JSON**: Define the expected result after the task executes.

4. **Example Using a Script Task:**

**Task Details**:
  - **Script Code:** `a = 1`.

**Unit Test Configuration**:
  - **Input JSON:** `{ "a": 2 }`
  - **Expected Output JSON:** `{ "a": 2 }`

The test checks whether the process maintains the value of `a` as `2` despite the script setting `a = 1`. This validates data integrity and ensures that the task does not overwrite the expected result.

## Comparing Both Methods

| Feature                        | JSON File Method                                    | Properties Panel Method                          |
|--------------------------------|----------------------------------------------------|-------------------------------------------------|
| **Complexity**                 | Suitable for large, complex processes              | Ideal for isolated tasks (e.g., Script Tasks)   |
| **Flexibility**                | Supports multiple test cases in one file           | Limited to task-specific tests                  |
| **User-Friendliness**          | Requires familiarity with JSON syntax              | More intuitive and UI-driven                    |
| **Scalability**                | Excellent for testing multiple BPMN models         | Focused on individual tasks                     |

This documentation comprehensively explains both methods, their use cases, and how to implement them with practical examples. Let me know if further refinements are needed!