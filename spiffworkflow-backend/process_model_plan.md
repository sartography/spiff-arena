# Plan to Remove Marshmallow from `process_model.py`

The file `src/spiffworkflow_backend/models/process_model.py` contains one Marshmallow schema, `ProcessModelInfoSchema`, which needs to be replaced.

---

### Phase 1: `ProcessModelInfoSchema`

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

*   **Analysis:** This schema is used in various places to serialize and deserialize `ProcessModelInfo` objects. It also has a nested `FileSchema` which needs to be handled.

*   **Proposed Change:** The `ProcessModelInfo` dataclass already exists. We will augment it with `to_dict` and `from_dict` methods to handle serialization and deserialization.

### Execution Plan:

1.  **Investigate `FileSchema`:** Before modifying `ProcessModelInfoSchema`, we must understand how `File` objects are serialized. We need to find the `FileSchema` and plan its removal, likely by adding `to_dict` and `from_dict` methods to the `File` class in `src/spiffworkflow_backend/models/file.py`.

2.  **Update `ProcessModelInfo` Dataclass:**
    *   Add `to_dict` and `from_dict` methods to the `ProcessModelInfo` dataclass.
    *   The `to_dict` method will handle the correct serialization of nested `File` objects by calling their `to_dict` method.
    *   The `from_dict` method will handle the deserialization of the nested `File` objects.

3.  **Refactor Usages:** Search the codebase for any instances where `ProcessModelInfoSchema` is used for loading or dumping data.
    *   Replace `ProcessModelInfoSchema().load(data)` with `ProcessModelInfo.from_dict(data)`.
    *   Replace `ProcessModelInfoSchema().dump(obj)` with `obj.to_dict()`.
    *   The following files will need to be updated:
        - `tests/spiffworkflow_backend/integration/test_process_api.py`
        - `tests/spiffworkflow_backend/integration/test_nested_groups.py`
        - `tests/spiffworkflow_backend/helpers/base_test.py`
        - `src/spiffworkflow_backend/routes/process_models_controller.py`
        - `src/spiffworkflow_backend/services/process_model_service.py`
        - `src/spiffworkflow_backend/models/process_group.py`

4.  **Remove `ProcessModelInfoSchema`:** Once all references have been updated, delete the schema from `process_model.py`.

By following this plan, we can systematically remove Marshmallow from `process_model.py` while maintaining the existing functionality.
