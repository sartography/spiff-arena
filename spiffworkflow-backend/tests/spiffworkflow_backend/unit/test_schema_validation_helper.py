import json
from typing import Any

import pytest

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.helpers.schema_validation_helper import validate_instance_against_schema


@pytest.mark.parametrize("schema", [None, "", {}, "{}", True, "true"])
def test_missing_and_permissive_schema(schema: Any) -> None:
    validate_instance_against_schema({"anything": True}, schema, "validation_error")


@pytest.mark.parametrize("schema", [False, "false"])
@pytest.mark.parametrize("error_code", ["task_data_validation_error", "message_data_validation_error"])
def test_false_schema_rejects_all_payloads(schema: Any, error_code: str) -> None:
    with pytest.raises(ApiError) as error:
        validate_instance_against_schema({}, schema, error_code)
    assert error.value.status_code == 400
    assert error.value.error_code == error_code


@pytest.mark.parametrize("schema", ["{broken json", " ", "null", "0", "[]", {"type": "invalid"}, {"$ref": "#/$defs/missing"}])
def test_invalid_schema_fails_closed(schema: Any) -> None:
    with pytest.raises(ApiError) as error:
        validate_instance_against_schema({}, schema, "validation_error")
    assert error.value.status_code == 400
    assert error.value.error_code == "validation_error"
    assert "Invalid JSON schema" in error.value.message


@pytest.mark.parametrize("serialized", [True, False])
def test_validation_preserves_format_checking_and_error_path(serialized: bool) -> None:
    schema: dict | str = {
        "type": "object",
        "properties": {
            "customer": {
                "type": "object",
                "properties": {"email": {"type": "string", "format": "email"}},
            }
        },
    }
    if serialized:
        schema = json.dumps(schema)
    validate_instance_against_schema({"customer": {"email": "customer@example.com"}}, schema, "validation_error")
    with pytest.raises(ApiError) as error:
        validate_instance_against_schema(
            {"customer": {"email": "invalid"}}, schema, "task_data_validation_error", "Task data validation failed"
        )
    assert error.value.error_code == "task_data_validation_error"
    assert error.value.message.startswith("Task data validation failed:")
    assert "at path: customer.email" in error.value.message
