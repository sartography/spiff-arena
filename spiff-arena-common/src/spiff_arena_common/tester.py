import io
import json
import os
import unittest

from collections import namedtuple

from spiff_arena_common.runner import advance_workflow, specs_from_xml

Test = namedtuple("Test", ["file", "specs"])
TestCtx = namedtuple("TestCtx", ["files", "specs", "tests", "test_cases"])
TestRun = namedtuple("TestRun", ["ctx", "result", "output"])

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
        self.specs = json.loads(self.specs)
        for id in ids:
            specs = json.loads(self.specs_by_id[id])
            subprocess_specs = self.specs["subprocess_specs"]
            subprocess_specs[id] = specs["spec"]
            subprocess_specs.update(specs["subprocess_specs"])
        self.specs = json.dumps(self.specs)

    def runTest(self):
        iters = 0
        while iters < 100:
            iters = iters + 1
            r = json.loads(advance_workflow(self.specs, self.state, None, "unittest", None))
            self.state = r["state"]
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

def files_to_parse(dir):
    for root, dirs, files in os.walk(dir, topdown=True):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        yield from [os.path.join(root, f) for f in files if f.endswith(".bpmn")] # TODO: dmn

def slurp(file):
    with open(file) as f:
        return f.read()

def testCtx(parsed):
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

def runTests(parsed):
    ctx = testCtx(parsed)
    suite = unittest.TestSuite()
    suite.addTests(ctx.test_cases)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(suite)
    return TestRun(ctx, result, stream.getvalue())
    
def runTestsInDir(dir):
    parsed = []
    for file in files_to_parse(dir):
        specs, err = specs_from_xml([(file, slurp(file))])
        assert not err
        parsed.append((file, specs))
    return runTests(parsed)
