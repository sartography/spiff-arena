# Marshmallow Refactoring Checklist

This document outlines the steps to remove the Marshmallow serialization library from the codebase.

## Python Files to Refactor

- [ ] `src/spiffworkflow_backend/models/process_group.py`: Remove marshmallow usage and replace with custom serialization/deserialization logic.
- [ ] `src/spiffworkflow_backend/models/process_model.py`: Remove marshmallow usage and replace with custom serialization/deserialization logic.
- [ ] `src/spiffworkflow_backend/models/reference_cache.py`: Remove marshmallow usage and replace with custom serialization/deserialization logic.
- [ ] `src/spiffworkflow_backend/models/secret_model.py`: Remove marshmallow usage and replace with custom serialization/deserialization logic.
- [ ] `src/spiffworkflow_backend/models/task.py`: Remove marshmallow usage and replace with custom serialization/deserialization logic.
- [ ] `src/spiffworkflow_backend/models/process_instance.py`: Remove marshmallow usage and replace with custom serialization/deserialization logic.

## Dependency Management Files

- [ ] `pyproject.toml`: Remove marshmallow dependency once it's no longer used in any Python files.
- [ ] `uv.lock`: This file will be updated automatically after changes in `pyproject.toml` and subsequent dependency resolution. (No direct manual edit needed for this file regarding marshmallow removal itself, but it's part of the final cleanup).

## General Guidelines for Refactoring Each File

1. **Understand Current Usage:** Analyze how Marshmallow schemas are used for serialization (object to dict/JSON) and deserialization (dict/JSON to object). Search for the code that being updated (marshmallow classes or similar) elsewhere in the codebase to understand how it used and what the updated code will need to support. Update the spec.md as necessary with details and ensure tests are passing after changes using the run_test_command tool.
2. **Identify Data Structures:** Determine the structure of the data being (de)serialized.
3. **Implement Custom (De)Serialization:**
   - For serialization, implement `to_dict()` or similar methods on the model classes. If the model can leverage a `dataclass`, `dataclasses.asdict` is a powerful tool for converting the object to a dictionary. For complex types not handled by default JSON encoders (e.g., `datetime`), you may need a custom encoder function passed to `json.dumps`.
   - For deserialization, implement `from_dict()` or similar class methods that take a dictionary and return an instance of the model. For `dataclass` models, you can inspect `typing.get_type_hints` to determine the expected type for each field and recursively deserialize nested objects.
   - Handle data validation and type conversion manually as needed. Ensure that the new implementation is backwards compatible with existing data formats if necessary.
4. **Replace Marshmallow Schema Instantiation and Usage:** Update the code to use the new custom (de)serialization logic instead of Marshmallow schemas (`load`, `dump`, `validate`).
5. **Testing:** Thoroughly test the changes to ensure that (de)serialization works as expected and that no functionality is broken using the run_test_command tool. Pay close attention to edge cases and error handling.
6. **dataclass:** Convert the models to `dataclasses` (using `from dataclasses import dataclass`). This will greatly assist with serialization via `dataclasses.asdict` and provides a clear structure for implementing deserialization logic by inspecting type hints.
7. **Database Models:** Be aware that many of these models are also SQLAlchemy models. The (de)serialization logic you are building is for converting these objects to and from JSON for API responses. This is separate from how SQLAlchemy persists them to the database. Ensure your changes do not break database operations. When using `asdict`, you will likely be serializing the same attributes that SQLAlchemy is persisting.

This checklist will help track the progress of removing Marshmallow from the project.
