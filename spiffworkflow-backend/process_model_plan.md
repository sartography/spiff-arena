### Plan to Remove Marshmallow from `process_model.py`

The file `src/spiffworkflow_backend/models/process_model.py` contains one Marshmallow schema, `ProcessModelInfoSchema`, which needs to be replaced.

**1. `ProcessModelInfoSchema`**

*   **Current Implementation:**
    ```python
    class ProcessModelInfoSchema(Schema):
        class Meta:
            model = ProcessModelInfo

        id = marshmallow.fields.String(required=True)
        display_name = marshmallow.fields.String(required=True)
        description = marshmallow.fields.String()
        primary_file_name = marshmallow.fields.String(allow_none=True)
        primary_process_id = marshmallow.fields.String(allow_none=True)
        files = marshmallow.fields.List(marshmallow.fields.Nested("File"))
        fault_or_suspend_on_exception = marshmallow.fields.String()
        exception_notification_addresses = marshmallow.fields.List(marshmallow.fields.String)
        metadata_extraction_paths = marshmallow.fields.List(
            marshmallow.fields.Dict(
                keys=marshmallow.fields.Str(required=False),
                values=marshmallow.fields.Str(required=False),
                required=False,
            )
        )

        @post_load
        def make_spec(self, data: dict[str, str | bool | int | NotificationType], **_: Any) -> ProcessModelInfo:
            return ProcessModelInfo(**data)
    ```

*   **Analysis:**
    *   This schema defines the serialization and deserialization for the `ProcessModelInfo` dataclass.
    *   It includes basic field validations (e.g., `required=True`).
    *   It uses `marshmallow.fields.Nested("File")` to handle the serialization of a list of `File` objects. This indicates a dependency on a `FileSchema` which will also need to be addressed.
    *   The `post_load` hook `make_spec` is responsible for converting the deserialized dictionary back into a `ProcessModelInfo` instance.

*   **Proposed Change:**
    *   Remove the `ProcessModelInfoSchema` class entirely.
    *   Implement `to_dict` and `from_dict` methods directly within the `ProcessModelInfo` dataclass to handle serialization and deserialization.

*   **`ProcessModelInfo` Dataclass Modification:**

    ```python
    from dataclasses import dataclass, asdict
    # ... other imports

    @dataclass(order=True)
    class ProcessModelInfo:
        # ... existing fields ...

        def to_dict(self) -> dict:
            """Serializes the ProcessModelInfo object to a dictionary."""
            data = asdict(self)
            # Handle nested File objects if they have their own serialization method
            if self.files:
                data['files'] = [file.to_dict() for file in self.files]
            return data

        @classmethod
        def from_dict(cls, data: dict) -> "ProcessModelInfo":
            """Creates a ProcessModelInfo object from a dictionary."""
            # We need to handle the nested 'files' data if it exists
            if 'files' in data and data['files'] is not None:
                # Assumes File class has a from_dict method
                from spiffworkflow_backend.models.file import File
                data['files'] = [File.from_dict(f) for f in data['files']]

            # Filter out keys that are not part of the dataclass fields
            valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
            filtered_data = {k: v for k, v in data.items() if k in valid_keys}

            return cls(**filtered_data)

    ```

**Execution Plan:**

1.  **Investigate `FileSchema`:** Before modifying `ProcessModelInfoSchema`, we must understand how `File` objects are serialized. We need to find the `FileSchema` and plan its removal, likely by adding `to_dict` and `from_dict` methods to the `File` class in `src/spiffworkflow_backend/models/file.py`.
2.  **Implement `to_dict` and `from_dict` in `File`:** Carry out the plan from step 1.
3.  **Implement `to_dict` and `from_dict` in `ProcessModelInfo`:** Add the methods as described above.
4.  **Refactor Usages:** Search the codebase for any instances where `ProcessModelInfoSchema` is used for loading or dumping data.
    *   Replace `ProcessModelInfoSchema().load(data)` with `ProcessModelInfo.from_dict(data)`.
    *   Replace `ProcessModelInfoSchema().dump(obj)` with `obj.to_dict()`.
5.  **Remove `ProcessModelInfoSchema`:** Once all references have been updated, delete the schema from `process_model.py`.
6.  **Run Tests:** Execute the test suite to ensure that all changes are backward-compatible and have not introduced any regressions.
