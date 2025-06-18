# Marshmallow Refactoring Checklist

This document outlines the steps to systematically remove the Marshmallow serialization library from the codebase, replacing it with custom serialization and deserialization logic.

## Guiding Principles

- **No New Dependencies:** The refactoring should not introduce new third-party serialization libraries like Pydantic. The preference is to use Python's standard library features, such as `dataclasses`.
- **Backwards Compatibility:** All custom serialization (`to_dict`) and deserialization (`from_dict`) logic must be fully backwards compatible with existing data formats and API contracts.
- **Incremental Refactoring:** The process is designed to be incremental, file by file, to ensure the application remains stable and functional throughout the refactoring effort.
- **Thorough Testing:** Each change must be accompanied by comprehensive testing to prevent regressions.
- **Clean Code:** The resulting code should be clean, maintainable, and easy to understand.

## Refactoring Scope

### Python Files to Refactor

- [x] `src/spiffworkflow_backend/models/secret_model.py`: Remove marshmallow usage and replace with custom serialization/deserialization logic.
- [x] `src/spiffworkflow_backend/models/reference_cache.py`: Remove marshmallow usage and replace with custom serialization/deserialization logic.
- [ ] `src/spiffworkflow_backend/models/process_instance.py`: Remove marshmallow usage and replace with custom serialization/deserialization logic.
- [ ] `src/spiffworkflow_backend/models/process_model.py`: Remove marshmallow usage and replace with custom serialization/deserialization logic.
- [ ] `src/spiffworkflow_backend/models/task.py`: Remove marshmallow usage and replace with custom serialization/deserialization logic.
- [ ] `src/spiffworkflow_backend/models/process_group.py`: Remove marshmallow usage and replace with custom serialization/deserialization logic.

### Dependency Management Files

- [ ] `pyproject.toml`: Remove the `marshmallow` dependency once it's no longer used in any Python files.
- [ ] `uv.lock`: This file will be updated automatically after changes in `pyproject.toml` and subsequent dependency resolution. No direct manual edit is needed for this file regarding marshmallow removal itself, but it's part of the final cleanup.

## General Refactoring Process (Per File)

For each file listed under "Python Files to Refactor," follow these steps:

1. **Analyze Current Marshmallow Usage:**

   - Identify all points where the Marshmallow schema for the current model is instantiated or used (e.g., `YourSchema().load(data)`, `YourSchema().dump(obj)`).
   - Understand the expected input/output formats at these integration points (e.g., API request bodies, response payloads, internal data passing).
   - Map Marshmallow fields to the corresponding attributes in the Python model and their expected types.

2. **Convert to Dataclass (if applicable):**

   - Modify the model class definition to be a `dataclass` by adding `@dataclass` from the `dataclasses` module. This simplifies attribute management and provides `dataclasses.asdict` for straightforward serialization.
   - Ensure compatibility with SQLAlchemy models if the class inherits from `SpiffworkflowBaseDBModel` or similar ORM base classes.

3. **Implement Custom Serialization as needed (`to_dict`):**

   - Add a `to_dict(self) -> dict` method to the model class.
   - For `dataclass` models, leverage `dataclasses.asdict(self)` as a starting point.
   - Handle complex types (e.g., `datetime` objects, nested custom objects, enums) by converting them to a JSON-serializable format (e.g., ISO 8601 string for `datetime`, calling `to_dict()` on nested custom objects, `value` for enums).
   - Ensure the output dictionary matches the exact JSON structure expected by API consumers or other parts of the system.

4. **Implement Custom Deserialization as needed (`from_dict`):**

   - Add a `classmethod from_dict(cls, data: dict) -> Self` (or `-> YourModelClass`) to the model class.
   - This method should take a dictionary (e.g., from a JSON request body) and construct an instance of the model.
   - Utilize `typing.get_type_hints(cls)` to dynamically determine expected types for fields, which can aid in recursive deserialization of nested objects.
   - Perform necessary type conversions (e.g., string to `datetime`, dictionary to nested custom object, string to enum).
   - Implement robust data validation, including handling missing required fields, incorrect types, and invalid values. Raise appropriate exceptions (e.g., `ValueError`, `TypeError`) for invalid input.
   - Ensure the deserialization logic is backwards compatible with existing data formats if necessary.

5. **Replace Marshmallow Calls:**

   - Update all code locations that previously used Marshmallow schemas (e.g., `YourSchema().load(data)`, `YourSchema().dump(obj)`) to use the new `from_dict` and `to_dict` methods.
   - Verify that API endpoints, internal services, and other consumers correctly use the new custom methods.
   - There is no need to remove usage of serialized() function calls. this is custom serialization logic unrelated to marshmallow, and new serialized functions can be implemented if helpful to replace marshmallow.

6. **Testing:**

   - Run existing unit and integration tests to ensure no regressions have been introduced.
   - Add new unit tests specifically for the `to_dict` and `from_dict` methods, covering various data scenarios, edge cases, and error handling.
   - Use the `run_test_command` tool to verify changes locally.

7. **Database Model Considerations:**
   - Remember that the custom (de)serialization logic you are building is primarily for API/JSON interaction, which is separate from how SQLAlchemy's ORM persists and retrieves data from the database.
   - Ensure your changes do not inadvertently affect how SQLAlchemy interacts with the database. When using `dataclasses.asdict`, be mindful of attributes that are ORM-specific and might not need to be serialized to JSON.

## Final Steps (After all files are refactored)

Once all individual files have been refactored and tested:

1. **Remove Marshmallow Dependency:**
   - Edit `pyproject.toml` to remove `marshmallow` from your project's dependencies.
2. **Update Lock File:**
   - Run your dependency manager's lock command (e.g., `uv lock` or `pip-compile`) to update `uv.lock` and reflect the removal of Marshmallow.
3. **Comprehensive Testing:**
   - Perform a final, comprehensive test run to ensure stability and correctness across all integrated components.
