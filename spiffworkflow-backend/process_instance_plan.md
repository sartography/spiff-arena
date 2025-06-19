### Plan to Remove Marshmallow from `process_instance.py`

The file `src/spiffworkflow_backend/models/process_instance.py` contains two Marshmallow schemas that need to be removed: `ProcessInstanceModelSchema` and `ProcessInstanceApiSchema`.

**1. `ProcessInstanceModelSchema`**

*   **Current Implementation:**
    ```python
    class ProcessInstanceModelSchema(Schema):
        class Meta:
            model = ProcessInstanceModel
            fields = [
                "id", "process_model_identifier", "process_model_display_name",
                "process_initiator_id", "start_in_seconds", "end_in_seconds",
                "updated_at_in_seconds", "created_at_in_seconds", "status",
                "bpmn_version_control_identifier",
            ]
        status = marshmallow.fields.Method("get_status", dump_only=True)

        def get_status(self, obj: ProcessInstanceModel) -> str:
            return obj.status
    ```
*   **Analysis:**
    *   This schema is used for serializing the `ProcessInstanceModel` database model.
    *   It has a custom method `get_status` which simply returns the `status` attribute of the object. This is redundant since the `status` is already a field.
    *   The `ProcessInstanceModel` already has a `serialized()` method which serves a similar purpose, but `ProcessInstanceModelSchema` selects a different subset of fields.

*   **Proposed Change:**
    *   Remove the `ProcessInstanceModelSchema` class.
    *   If the exact field selection of the schema is still needed, create a new serialization method on the `ProcessInstanceModel` class, for example `to_schema_dict()`, that returns the specific dictionary. Otherwise, update the calling code to use the existing `serialized()` method or to construct the desired dictionary directly. Given the direct mapping of fields, a new method is likely the cleanest approach.

*   **`ProcessInstanceModel` Modification:**

    ```python
    # In ProcessInstanceModel class
    def to_schema_dict(self) -> dict:
        """Returns a dictionary with the same fields as the old ProcessInstanceModelSchema."""
        return {
            "id": self.id,
            "process_model_identifier": self.process_model_identifier,
            "process_model_display_name": self.process_model_display_name,
            "process_initiator_id": self.process_initiator_id,
            "start_in_seconds": self.start_in_seconds,
            "end_in_seconds": self.end_in_seconds,
            "updated_at_in_seconds": self.updated_at_in_seconds,
            "created_at_in_seconds": self.created_at_in_seconds,
            "status": self.status,
            "bpmn_version_control_identifier": self.bpmn_version_control_identifier,
        }
    ```

**2. `ProcessInstanceApiSchema`**

*   **Current Implementation:**
    ```python
    class ProcessInstanceApi:
        # ... __init__ ...

    class ProcessInstanceApiSchema(Schema):
        class Meta:
            model = ProcessInstanceApi
            fields = [...]
            unknown = INCLUDE
        @marshmallow.post_load
        def make_process_instance(self, data: dict, **kwargs) -> ProcessInstanceApi:
            # ... filtering logic ...
            return ProcessInstanceApi(**filtered_fields)
    ```
*   **Analysis:**
    *   This schema is paired with a plain Python class `ProcessInstanceApi`.
    *   The `post_load` hook filters the incoming data to only include the expected keys before creating a `ProcessInstanceApi` object.
    *   `unknown = INCLUDE` allows extra fields in the input data.

*   **Proposed Change:**
    *   Convert the `ProcessInstanceApi` class into a `dataclass`.
    *   Remove the `ProcessInstanceApiSchema`.
    *   Add `from_dict` and `to_dict` methods to the new `ProcessInstanceApi` dataclass. The `from_dict` method will replicate the filtering logic from the `post_load` hook.

*   **`ProcessInstanceApi` Dataclass Implementation:**

    ```python
    from dataclasses import dataclass, asdict

    @dataclass
    class ProcessInstanceApi:
        id: int
        status: str
        process_model_identifier: str
        process_model_display_name: str
        updated_at_in_seconds: int

        @classmethod
        def from_dict(cls, data: dict) -> "ProcessInstanceApi":
            """Creates a ProcessInstanceApi object from a dictionary, ignoring unknown fields."""
            field_names = {f.name for f in cls.__dataclass_fields__.values()}
            filtered_data = {k: v for k, v in data.items() if k in field_names}
            return cls(**filtered_data)

        def to_dict(self) -> dict:
            """Serializes the ProcessInstanceApi object to a dictionary."""
            return asdict(self)
    ```

**Execution Plan:**

1.  **Refactor `ProcessInstanceApi`:**
    *   Change `ProcessInstanceApi` from a regular class to a `dataclass`.
    *   Implement the `from_dict` and `to_dict` methods as described above.
2.  **Refactor `ProcessInstanceModel`:**
    *   Add the `to_schema_dict()` method to the `ProcessInstanceModel` class.
3.  **Update References:**
    *   Search the codebase for usages of `ProcessInstanceModelSchema` and `ProcessInstanceApiSchema`.
    *   Replace `ProcessInstanceModelSchema().dump(obj)` with `obj.to_schema_dict()`.
    *   Replace `ProcessInstanceApiSchema().load(data)` with `ProcessInstanceApi.from_dict(data)`.
    *   Replace `ProcessInstanceApiSchema().dump(obj)` with `obj.to_dict()`.
4.  **Remove Schemas:** After updating all references, delete `ProcessInstanceModelSchema` and `ProcessInstanceApiSchema` from the file.
5.  **Test:** Run the full test suite to validate the changes and ensure no functionality has been broken.
