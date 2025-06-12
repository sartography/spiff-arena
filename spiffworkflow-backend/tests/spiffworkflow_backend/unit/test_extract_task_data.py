import pytest

from collections import namedtuple

from spiffworkflow_backend.scripts.extract_from_task_data import ExtractFromTaskData
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext

@pytest.mark.parametrize("in_task_data, out_task_data, pred, expected", [
    ({}, {}, None, {})
])
def test_extracts(in_task_data, out_task_data, pred, expected) -> None:
    script_attributes_context = ScriptAttributesContext(
        task=namedtuple("MockTask", ["data"])(in_task_data),
        environment_identifier="testing",
        process_instance_id=1,
        process_model_identifier="my_test",
    )

    extracted = ExtractFromTaskData().run(script_attributes_context, pred)
    assert extracted == expected
    assert script_attributes_context.task.data == out_task_data
