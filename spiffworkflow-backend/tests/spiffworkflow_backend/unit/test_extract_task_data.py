from dataclasses import dataclass
from typing import Any

import pytest

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.extract_from_task_data import ExtractFromTaskData


@dataclass
class MockTask:
    data: dict


def islower(k: str) -> bool:
    return k.islower()


@pytest.mark.parametrize(
    "pred, in_task_data, expected, out_task_data",
    [
        (None, {}, {}, {}),
        (None, {"a": 1}, {"a": 1}, {}),
        (lambda k: True, {"a": 1}, {"a": 1}, {}),
        (lambda k: False, {"a": 1}, {}, {"a": 1}),
        (islower, {"a": 1, "B": 2, "c": 3}, {"a": 1, "c": 3}, {"B": 2}),
        (
            "efile_",
            {
                "efile_var_1": "efile_var_1",
                "efile_var_2": "efile_var_2",
                "efile_var_3": "efile_var_3",
                "efile_var_4": "efile_var_4",
                "efile_var_5": "efile_var_5",
            },
            {
                "efile_var_1": "efile_var_1",
                "efile_var_2": "efile_var_2",
                "efile_var_3": "efile_var_3",
                "efile_var_4": "efile_var_4",
                "efile_var_5": "efile_var_5",
            },
            {},
        ),
        (
            "efile_",
            {
                "efile_var_1": "efile_var_1",
                "var_2": "var_2",
            },
            {
                "efile_var_1": "efile_var_1",
            },
            {
                "var_2": "var_2",
            },
        ),
    ],
)
def test_extracts(pred: Any, in_task_data: Any, expected: Any, out_task_data: Any) -> None:
    script_attributes_context = ScriptAttributesContext(
        task=MockTask(in_task_data),
        environment_identifier="testing",
        process_instance_id=1,
        process_model_identifier="my_test",
    )

    extracted = ExtractFromTaskData().run(script_attributes_context, pred)
    assert extracted == expected
    assert script_attributes_context.task.data == out_task_data  # type: ignore
