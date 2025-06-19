### Plan to remove marshmallow from `src/spiffworkflow_backend/models/process_group.py`

1.  **Identify marshmallow usage:** The file `src/spiffworkflow_backend/models/process_group.py` uses marshmallow to define `ProcessGroupSchema`. This schema is used to load data into a `ProcessGroup` dataclass.

2.  **Analyze `ProcessGroupSchema`:**
    *   **Fields:** The schema serializes `id`, `display_name`, `process_models`, `description`, `process_groups`, `messages`, and `correlation_properties`.
    *   **Nested Schemas:** It uses nested schemas for `process_models` (`ProcessModelInfoSchema`) and `process_groups` (`ProcessGroupSchema`). This implies a recursive structure for groups.
    *   **Custom Logic:** The `make_process_group` method contains significant data transformation logic:
        *   It converts a `messages` dictionary into a list of `Message` objects.
        *   It extracts `correlation_properties` from within the `messages` structure and merges them with top-level `correlation_properties`.

3.  **Replacement Strategy:**
    *   Create a `from_dict` class method in the `ProcessGroup` dataclass.
    *   This method will take a dictionary as input and be responsible for creating a `ProcessGroup` instance.
    *   The logic from `make_process_group` will be moved into this new `from_dict` method.
    *   For nested `process_models` and `process_groups`, the `from_dict` method will need to recursively call `ProcessModelInfo.from_dict()` and `ProcessGroup.from_dict()` on the items in those lists. This means I'll likely need to create `from_dict` methods on those classes first.

4.  **Step-by-step Implementation:**
    1.  Define a `from_dict` method on the `ProcessGroup` class.
    2.  Copy the logic from `ProcessGroupSchema.make_process_group` into `ProcessGroup.from_dict`.
    3.  Handle the nested `process_models` by calling a (to be created) `ProcessModelInfo.from_dict` on each element of the list.
    4.  Handle the nested `process_groups` by recursively calling `ProcessGroup.from_dict` on each element of the list.
    5.  Search the codebase for usages of `ProcessGroupSchema`.
    6.  Replace any instance of `ProcessGroupSchema().load(data)` with `ProcessGroup.from_dict(data)`.
    7.  Once all references to `ProcessGroupSchema` are removed, delete the `ProcessGroupSchema` class and the marshmallow import from the file.
