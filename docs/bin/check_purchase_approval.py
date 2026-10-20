#!/usr/bin/env python3
"""Check the tutorial's downloadable model using Arena's test runner.

From the repository root, with backend dependencies installed:
    spiffworkflow-backend/.venv/bin/python docs/bin/check_purchase_approval.py

No database or running Arena server is required.
"""

import json
import shutil
import tempfile
from pathlib import Path
from xml.etree import ElementTree

from flask import Flask
from jinja2 import Environment, StrictUndefined
from jsonschema import Draft7Validator
from spiffworkflow_backend.services.process_model_test_runner_service import ProcessModelTestRunner


EXAMPLE = Path(__file__).resolve().parents[1] / "tutorials/examples/purchase-approval"
NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "spiff": "http://spiffworkflow.org/bpmn/schema/1.0/core",
}


def run_model(directory):
    runner = ProcessModelTestRunner("purchase-approval", str(directory))
    runner.run()
    return runner


def check():
    cases = json.loads((EXAMPLE / "test_purchase-approval.json").read_text())
    diagram = ElementTree.parse(EXAMPLE / "purchase-approval.bpmn")
    templates = Environment(undefined=StrictUndefined, autoescape=True)
    for task in diagram.findall(".//bpmn:userTask", NS):
        properties = {
            prop.attrib["name"]: prop.attrib["value"]
            for prop in task.findall(".//spiff:property", NS)
        }
        schema = json.loads((EXAMPLE / properties["formJsonSchemaFilename"]).read_text())
        Draft7Validator.check_schema(schema)
        validator = Draft7Validator(schema)
        assert not validator.is_valid({}), "The form must require input"
        assert json.loads((EXAMPLE / properties["formUiSchemaFilename"]).read_text()) == {}
        for case in cases.values():
            validator.validate(case["tasks"][task.attrib["id"]]["data"][0])
        if task.attrib["id"] == "review_request":
            assert not validator.is_valid({"decision": "maybe", "review_note": "Test"})
        else:
            for amount in [0, -1, "85"]:
                assert not validator.is_valid({"item": "Keyboard", "amount": amount, "reason": "Test"})

    for case in cases.values():
        request = case["tasks"]["submit_request"]["data"][0]
        review = case["tasks"]["review_request"]["data"][0]
        for task_id, data in [
            ("review_request", request),
            ("show_approval", request | review),
            ("show_decline", request | review),
        ]:
            instructions = diagram.find(f".//*[@id='{task_id}']//spiff:instructionsForEndUser", NS)
            rendered = templates.from_string(instructions.text).render(data)
            assert "Keyboard" in rendered and "85" in rendered

    with Flask(__name__).app_context():
        runner = run_model(EXAMPLE)
        assert len(runner.passing_tests()) == 2, runner.failing_tests_formatted()
        assert not runner.failing_tests(), runner.failing_tests_formatted()
        # Verify that a regression in the approval outcome is caught.
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "purchase-approval"
            shutil.copytree(EXAMPLE, directory)
            bpmn = directory / "purchase-approval.bpmn"
            bpmn.write_text(bpmn.read_text().replace('outcome = "approved"', 'outcome = "declined"'))
            mutated = run_model(directory)
            assert [case.test_case_identifier for case in mutated.failing_tests()] == ["approve_request"]
    print("Purchase approval: both paths pass; schemas, instructions, and deliberate failure checked.")


if __name__ == "__main__":
    check()
