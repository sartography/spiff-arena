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
   - For serialization, implement `to_dict()` or similar methods on the model classes that return a dictionary representation of the object.
   - For deserialization, implement `from_dict()` or similar class methods or factory functions that take a dictionary and return an instance of the model.
   - Handle data validation and type conversion manually as needed. Ensure that the new implementation is backwards compatible with existing data formats if necessary.
4. **Replace Marshmallow Schema Instantiation and Usage:** Update the code to use the new custom (de)serialization logic instead of Marshmallow schemas (`load`, `dump`, `validate`).
5. **Testing:** Thoroughly test the changes to ensure that (de)serialization works as expected and that no functionality is broken using the run_test_command tool. Pay close attention to edge cases and error handling.
6. **dataclass:** consider how dataclass (from dataclasses import dataclass) can assist with serialization, as this is used elsewhere in the app

This checklist will help track the progress of removing Marshmallow from the project.
