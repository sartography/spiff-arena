import json
from typing import Any

import jsonschema
from referencing.exceptions import Unresolvable

from spiffworkflow_backend.exceptions.api_error import ApiError


def validate_instance_against_schema(
    instance: Any,
    schema: dict | bool | str | None,
    error_code: str,
    error_prefix: str = "Data validation failed",
) -> None:
    if schema is None:
        return

    # Parsed editor JSON may be any value; jsonschema rejects non-schemas such as null or [] below.
    parsed_schema: Any = schema
    if isinstance(schema, str):
        # An empty editor value means no schema. Non-empty invalid JSON must fail closed.
        if schema == "":
            return
        try:
            parsed_schema = json.loads(schema)
        except json.JSONDecodeError as error:
            raise ApiError(
                error_code=error_code,
                message=f"{error_prefix}: Invalid JSON schema: {error.msg}",
                status_code=400,
            ) from error

    # Boolean schemas are valid JSON Schema: false rejects everything, true accepts everything.

    try:
        jsonschema.validate(
            instance=instance,
            schema=parsed_schema,
            format_checker=jsonschema.FormatChecker(),
        )
    except jsonschema.exceptions.ValidationError as validation_error:
        error_message = f"{error_prefix}: {validation_error.message}"
        if validation_error.path:
            error_message += f" at path: {'.'.join(str(p) for p in validation_error.path)}"

        raise ApiError(error_code=error_code, message=error_message, status_code=400) from validation_error
    except (jsonschema.exceptions.SchemaError, TypeError, Unresolvable) as error:
        error_message = f"{error_prefix}: Invalid JSON schema: {str(error)}"
        raise ApiError(error_code=error_code, message=error_message, status_code=400) from error
