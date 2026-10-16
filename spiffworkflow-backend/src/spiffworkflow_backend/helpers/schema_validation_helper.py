import json
from typing import Any

import jsonschema

from spiffworkflow_backend.exceptions.api_error import ApiError


def validate_instance_against_schema(
    instance: Any,
    schema: dict | str | None,
    error_code: str,
    error_prefix: str = "Data validation failed",
) -> None:
    if schema is None:
        return

    if isinstance(schema, str):
        if not schema or schema.strip() == "{}":
            return
        try:
            schema = json.loads(schema)
        except Exception:
            return

    if not schema or schema == {}:
        return

    try:
        jsonschema.validate(
            instance=instance,
            schema=schema,
            format_checker=jsonschema.FormatChecker(),
        )
    except jsonschema.exceptions.ValidationError as validation_error:
        error_message = f"{error_prefix}: {validation_error.message}"
        if validation_error.path:
            error_message += f" at path: {'.'.join(str(p) for p in validation_error.path)}"

        raise ApiError(
            error_code=error_code, message=error_message, status_code=400
        ) from validation_error
    except (jsonschema.exceptions.SchemaError, TypeError) as error:
        error_message = f"{error_prefix}: {str(error)}"
        raise ApiError(
            error_code=error_code, message=error_message, status_code=400
        ) from error
