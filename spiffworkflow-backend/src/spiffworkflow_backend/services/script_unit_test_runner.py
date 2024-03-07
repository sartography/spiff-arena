import json
import sys
import traceback
from dataclasses import dataclass
from typing import Any

from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

from spiffworkflow_backend.services.process_instance_processor import CustomBpmnScriptEngine

PythonScriptContext = dict[str, Any]


@dataclass
class ScriptUnitTestResult:
    result: bool
    context: PythonScriptContext | None = None
    error: str | None = None
    line_number: int | None = None
    offset: int | None = None


class ScriptUnitTestRunner:
    _script_engine = CustomBpmnScriptEngine()

    @classmethod
    def run_with_script_and_pre_post_contexts(
        cls,
        script: str,
        input_context: PythonScriptContext,
        expected_output_context: PythonScriptContext,
    ) -> ScriptUnitTestResult:
        # make a new variable just for clarity, since we are going to update this dict in place
        # with the output variables from the script.
        context = input_context.copy()

        try:
            cls._script_engine.environment.clear_state()
            cls._script_engine.environment.execute(script, context, external_context=None)
        except SyntaxError as ex:
            return ScriptUnitTestResult(
                result=False,
                error=f"Syntax error: {str(ex)}",
                line_number=ex.lineno,
                offset=ex.offset,
            )
        except Exception as ex:
            if isinstance(ex, WorkflowTaskException):
                # we never expect this to happen, so we want to know about it.
                # if indeed we are always getting WorkflowTaskException,
                # we can simplify this error handling and replace it with the
                # except block from revision cccd523ea39499c10f7f3c2e3f061852970973ac
                raise ex
            error_message = f"{ex.__class__.__name__}: {str(ex)}"
            line_number = 0
            _cl, _exc, tb = sys.exc_info()
            # Loop back through the stack trace to find the file called
            # 'string' - which is the script we are executing, then use that
            # to parse and pull out the offending line.
            for frame_summary in traceback.extract_tb(tb):
                if frame_summary.filename == "<string>":
                    if frame_summary.lineno is not None:
                        line_number = frame_summary.lineno

            return ScriptUnitTestResult(
                result=False,
                line_number=line_number,
                error=f"Failed to execute script: {error_message}",
            )

        context = cls._script_engine.environment.last_result()
        result_as_boolean = context == expected_output_context

        script_unit_test_result = ScriptUnitTestResult(result=result_as_boolean, context=context)
        return script_unit_test_result

    @classmethod
    def run_test(
        cls,
        task: SpiffTask,
        test_identifier: str,
    ) -> ScriptUnitTestResult:
        # this is totally made up, but hopefully resembles what spiffworkflow ultimately does
        unit_tests = task.task_spec.extensions["unitTests"]
        unit_test = [unit_test for unit_test in unit_tests if unit_test["id"] == test_identifier][0]

        input_context = None
        expected_output_context = None
        try:
            input_context = json.loads(unit_test["inputJson"])
        except json.decoder.JSONDecodeError as ex:
            return ScriptUnitTestResult(
                result=False,
                error=f"Failed to parse inputJson: {unit_test['inputJson']}: {str(ex)}",
            )

        try:
            expected_output_context = json.loads(unit_test["expectedOutputJson"])
        except json.decoder.JSONDecodeError as ex:
            return ScriptUnitTestResult(
                result=False,
                error=f"Failed to parse expectedOutputJson: {unit_test['expectedOutputJson']}: {str(ex)}",
            )

        script = task.task_spec.script
        return cls.run_with_script_and_pre_post_contexts(script, input_context, expected_output_context)
