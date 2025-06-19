### Plan to remove marshmallow from `src/spiffworkflow_backend/models/process_model.py`

1.  **Identify marshmallow usage:** The file `src/spiffworkflow_backend/models/process_model.py` uses marshmallow to define `ProcessModelInfoSchema`.

2.  **Analyze `ProcessModelInfoSchema`:**
    *   **Fields:** The schema defines fields for `id`, `display_name`, `description`, `primary_file_name`, `primary_process_id`, `files`, `fault_or_suspend_on_exception`, `exception_notification_addresses`, and `metadata_extraction_paths`.
    *   **Nested Schema:** It uses a nested schema for the `files` field, which is a list of `File` objects.
    *   **Custom Logic:** The `make_spec` method simply instantiates a `ProcessModelInfo` object with the loaded data.

3.  **Replacement Strategy:**
    *   Create a `from_dict` class method on the `ProcessModelInfo` dataclass.
    *   This method will take a dictionary and return a `ProcessModelInfo` instance.
    *   The `from_dict` method will handle the nested `files` by calling a `File.from_dict()` method on each item in the list. This implies I'll need to create a `from_dict` method on the `File` class.

4.  **Step-by-step Implementation:**
    1.  Define a `from_dict` method on the `ProcessModelInfo` class.
    2.  In this method, handle the instantiation of the `ProcessModelInfo` object.
    3.  For the `files` field, iterate through the list of dictionaries and call `File.from_dict()` on each one to create `File` objects.
    4.  Search the codebase for usages of `ProcessModelInfoSchema`.
    5.  Replace any instance of `ProcessModelInfoSchema().load(data)` with `ProcessModelInfo.from_dict(data)`.
    6.  Once all references are removed, delete the `ProcessModelInfoSchema` class and the marshmallow import.
