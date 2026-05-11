import io
import json
import os
import contextlib
import unittest

from collections import namedtuple

import jsonschema

from spiff_arena_common.runner import advance_workflow, SpiffJsonEncoder, spiff_json_object_hook, specs_from_xml

Test = namedtuple("Test", ["file", "specs"])
TestCtx = namedtuple("TestCtx", ["files", "specs", "tests", "test_cases"])
TestRun = namedtuple("TestRun", ["ctx", "result", "output"])
RecordingTest = namedtuple("RecordingTest", ["file", "recording_file", "schema_file"])

class BpmnTestCase(unittest.TestCase):
    def __init__(self, file, specs, specs_by_id):
        self.file = file
        self.specs = specs
        self.specs_by_id = specs_by_id
        self.state = {}
        self.output = ""
        self.testsRun = 0
        self.wasSuccessful = False
        super().__init__()

    def lazy_load(self, ids):
        self.specs = json.loads(self.specs, object_hook=spiff_json_object_hook)
        for id in ids:
            specs = json.loads(self.specs_by_id[id], object_hook=spiff_json_object_hook)
            subprocess_specs = self.specs["subprocess_specs"]
            subprocess_specs[id] = specs["spec"]
            subprocess_specs.update(specs["subprocess_specs"])
        self.specs = json.dumps(self.specs, cls=SpiffJsonEncoder)

    def runTest(self):
        iters = 0
        r = None
        while iters < 100:
            iters = iters + 1
            r = json.loads(advance_workflow(self.specs, self.state, None, "unittest", None), object_hook=spiff_json_object_hook)
            self.state = r["state"]

            # Check for errors after each advance
            if r.get("status") != "ok":
                error_msg = f"Test file: {self.file}\n"
                error_msg += f"Error during workflow execution (iteration {iters}):\n"
                error_msg += f"Message: {r.get('message', 'No message')}\n"
                if r.get("error_tasks"):
                    error_tasks = r.get("error_tasks")
                    if error_tasks:
                        error_msg += f"\nFailed task: {error_tasks[0].get('task_spec', {}).get('bpmn_name', 'unknown')}\n"
                        error_msg += f"Task ID: {error_tasks[0].get('task_spec', {}).get('bpmn_id', 'unknown')}\n"
                self.fail(error_msg)

            lazy_loads = r.get("lazy_loads")
            if not lazy_loads:
                break
            self.lazy_load(lazy_loads)

        self.assertEqual(r.get("status"), "ok")
        completed = r.get("completed")
        
        if completed:
            self.assertIn("result", r)
            data = r["result"]
        else:
            self.assertIn("pending_tasks", r)
            pending = r["pending_tasks"]
            if len(pending) == 0:
                # This indicates a workflow logic issue (not completed but no pending tasks)
                error_msg = f"Test file: {self.file}\n"
                error_msg += "Expected pending tasks but found none (workflow not completed but stuck).\n"
                response_copy = dict(r)
                if 'state' in response_copy:
                    del response_copy['state']  # Exclude large state object
                error_msg += f"Response:\n{json.dumps(response_copy, indent=2)}\n"
                self.fail(error_msg)
            self.assertGreater(len(pending), 0)
            self.assertIn("data", pending[0])
            data = pending[0]["data"]

        stack = data.get("spiff_testFixture", {}).get("pendingTaskStack", [])
        self.assertEqual(stack, [])
        
        self.assertIn("spiff_testResult", data)
        result = data["spiff_testResult"]
        self.assertIn("output", result)
        self.assertIn("testsRun", result)
        self.assertIn("wasSuccessful", result)
        
        self.output = result["output"]
        self.testsRun = result["testsRun"]
        self.wasSuccessful = completed and result["wasSuccessful"]
        self.assertTrue(self.wasSuccessful)


class BpmnRecordingTestCase(unittest.TestCase):
    def __init__(self, file, specs, specs_by_id, recording_file, schema_file=None):
        self.file = file
        self.specs = specs
        self.coverage_spec_id = json.loads(specs)["spec"]["name"]
        self.specs_by_id = specs_by_id
        self.recording_file = recording_file
        self.schema_file = schema_file
        self.state = {}
        self.output = ""
        self.testsRun = 0
        self.wasSuccessful = False
        super().__init__()

    def lazy_load(self, ids):
        self.specs = json.loads(self.specs, object_hook=spiff_json_object_hook)
        for id in ids:
            specs = json.loads(self.specs_by_id[id], object_hook=spiff_json_object_hook)
            subprocess_specs = self.specs["subprocess_specs"]
            subprocess_specs[id] = specs["spec"]
            subprocess_specs.update(specs["subprocess_specs"])
        self.specs = json.dumps(self.specs, cls=SpiffJsonEncoder)

    def _workflow_data(self, response):
        completed = response.get("completed")
        if completed:
            self.assertIn("result", response)
            return response["result"]

        self.assertIn("pending_tasks", response)
        pending = response["pending_tasks"]
        if len(pending) == 0:
            error_msg = f"Test file: {self.file}\n"
            error_msg += "Expected pending tasks but found none (workflow not completed but stuck).\n"
            response_copy = dict(response)
            if "state" in response_copy:
                del response_copy["state"]
            error_msg += f"Response:\n{json.dumps(response_copy, indent=2)}\n"
            self.fail(error_msg)
        self.assertIn("data", pending[0])
        return pending[0]["data"]

    def _validate_schema(self, data):
        if not self.schema_file:
            return
        with open(self.schema_file) as f:
            schema = json.load(f)
        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as e:
            last_task_data_schema = schema.get("properties", {}).get("last_task_data")
            if last_task_data_schema:
                try:
                    jsonschema.validate(data, last_task_data_schema)
                    return
                except jsonschema.ValidationError:
                    pass
            self.fail(f"Schema validation failed for {self.schema_file}: {e.message}")

    def runTest(self):
        iters = 0
        r = None
        self.lazy_load([id for id in self.specs_by_id if id != self.coverage_spec_id])
        start_params = {"data": {"spiff_testFixture_file": self.recording_file}}
        while iters < 100:
            iters = iters + 1
            with contextlib.redirect_stdout(io.StringIO()):
                r = json.loads(
                    advance_workflow(self.specs, self.state, None, "unittest", start_params),
                    object_hook=spiff_json_object_hook,
                )
            start_params = None
            self.state = r["state"]

            if r.get("status") != "ok":
                error_msg = f"Test file: {self.file}\n"
                error_msg += f"Recording file: {self.recording_file}\n"
                error_msg += f"Error during workflow execution (iteration {iters}):\n"
                error_msg += f"Message: {r.get('message', 'No message')}\n"
                if r.get("error_tasks"):
                    error_tasks = r.get("error_tasks")
                    if error_tasks:
                        error_msg += f"\nFailed task: {error_tasks[0].get('task_spec', {}).get('bpmn_name', 'unknown')}\n"
                        error_msg += f"Task ID: {error_tasks[0].get('task_spec', {}).get('bpmn_id', 'unknown')}\n"
                self.fail(error_msg)

            lazy_loads = r.get("lazy_loads")
            if not lazy_loads:
                break
            self.lazy_load(lazy_loads)

        self.assertEqual(r.get("status"), "ok")
        self._validate_schema(self._workflow_data(r))
        self.testsRun = 1
        self.wasSuccessful = True

def files_to_parse(dir):
    for root, dirs, files in os.walk(dir, topdown=True):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        yield from [os.path.join(root, f) for f in files if f.endswith(".bpmn")] # TODO: dmn

def slurp(file):
    with open(file) as f:
        return f.read()

def test_ctx(parsed):
    ctx = TestCtx([], {}, [], [])
    for (file, specs) in parsed:
        if file.endswith("_test.bpmn"):
            ctx.tests.append(Test(file, specs))
            ctx.test_cases.append(BpmnTestCase(file, specs, ctx.specs))
        else:
            d = json.loads(specs)
            id = d["spec"]["name"]
            assert id not in ctx.specs
            ctx.files.append((id, file))
            ctx.specs[id] = specs
    ctx.files.sort(key=lambda f: f[1])
    ctx.tests.sort()
    return ctx

def _recording_test(recording):
    if len(recording) == 2:
        file, recording_file = recording
        schema_file = None
    elif len(recording) == 3:
        file, recording_file, schema_file = recording
    else:
        raise ValueError("Recording tests must be (file, recording_file) or (file, recording_file, schema_file)")
    return RecordingTest(file, recording_file, schema_file)

def _specs_by_file(parsed):
    return {file: specs for file, specs in parsed}

def run_tests(parsed):
    ctx = test_ctx(parsed)
    suite = unittest.TestSuite()
    suite.addTests(ctx.test_cases)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(suite)
    return TestRun(ctx, result, stream.getvalue())
    
def run_tests_in_dir(dir):
    parsed = []
    for file in files_to_parse(dir):
        specs, err = specs_from_xml([(file, slurp(file))])
        assert not err
        parsed.append((file, specs))
    return run_tests(parsed)

def run_tests_with_recordings(parsed, recordings):
    ctx = test_ctx(parsed)
    specs_by_file = _specs_by_file(parsed)
    for recording in recordings:
        recording_test = _recording_test(recording)
        if recording_test.file not in specs_by_file:
            raise ValueError(f"No parsed BPMN specs found for recording test file: {recording_test.file}")
        ctx.test_cases.append(
            BpmnRecordingTestCase(
                recording_test.file,
                specs_by_file[recording_test.file],
                ctx.specs,
                recording_test.recording_file,
                recording_test.schema_file,
            )
        )

    suite = unittest.TestSuite()
    suite.addTests(ctx.test_cases)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(suite)
    return TestRun(ctx, result, stream.getvalue())

def run_test_cases(tests):
    suite = unittest.TestSuite()
    suite.addTests(tests)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(suite)

    return {
        "testsRun": result.testsRun,
        "wasSuccessful": result.wasSuccessful(),
        "output": stream.getvalue(),
    }
