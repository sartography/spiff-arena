# BPMN Unit Tests

Software engineers test their code.
Now, with this feature, BPMN authors can also test their creations.
These tests can provide faster feedback than you would get by simply running your process model, and they allow you to mock out form input and service task connections as well as provide specific input to exercise different branches of your process model.
BPMN unit tests are designed to instill greater confidence that your process models will function as intended when they are deployed in real-world scenarios, both initially and after subsequent modifications.

## Creating BPMN Unit Tests

First, create a process model that you want to test.
Navigate to the process model and add a JSON file based on the name of one of the BPMN files.
For example, if your process model includes a file named `awesome_script_task.bpmn`, your test JSON file would be named `test_awesome_script_task.json`.
If you have multiple BPMN files you want to test, you can create multiple test JSON files.
The BPMN files you test do not need to be marked as the primary file for the process model in question.
The structure of your JSON should be as follows:

    {
      "test_case_1": {
        "tasks": {
          "ServiceTaskProcess:service_task_one": {
            "data": [{ "the_result": "result_from_service" }]
          }
        },
        "expected_output_json": { "the_result": "result_from_service" }
      }
    }

The top-level keys should be names of unit tests.
In this example, the unit test is named "test_case_1."
Under that, you can specify "tasks" and "expected_output_json."

Under "tasks," each key is the BPMN id of a specific task.
If you're testing a file that uses Call Activities and therefore calls other processes, there can be conflicting BPMN ids.
In such cases, you can specify the unique activity by prepending the Process id (in the above example, that is "ServiceTaskProcess").
For simpler processes, "service_task_one" (for example) would suffice as the BPMN id.
For User Tasks, the "data" (under a specific task) represents the data that will be entered by the user in the form.
For Service Tasks, the data represents the data that will be returned by the service.
Note that all User Tasks and Service Tasks must have their BPMN ids mentioned in the JSON file (with mock task data as desired), as otherwise, we won't know what to do when the flow arrives at these types of tasks.

The "expected_output_json" represents the state of the task data that you expect when the process completes.
When the test is run, if the actual task data differs from this expectation, the test will fail.
The test will also fail if the process never completes or if an error occurs.

## Running BPMN Unit Tests

Go to a process model and either click “Run Unit Tests” to run all tests for the process model or click on the “play icon” next to a "test_something.json" file.
Next, you will see either a green check mark or a red x.
You can click on these colored icons to get more details about the passing or failing test.
