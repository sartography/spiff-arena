### Plan to remove marshmallow from `src/spiffworkflow_backend/models/process_instance.py`

1.  **Identify marshmallow usage:** The file `src/spiffworkflow_backend/models/process_instance.py` defines two marshmallow schemas: `ProcessInstanceModelSchema` and `ProcessInstanceApiSchema`.

2.  **Analyze `ProcessInstanceModelSchema`:**
    *   **Fields:** It serializes a subset of the `ProcessInstanceModel` fields.
    *   **Custom Logic:** It has a `get_status` method, but this method just returns `obj.status`. The `serialized` method on the `ProcessInstanceModel` already handles serialization, so this schema might be redundant or used for a specific view of the data.

3.  **Analyze `ProcessInstanceApiSchema`:**
    *   **Fields:** It defines the fields for the `ProcessInstanceApi` class.
    *   **Custom Logic:** The `make_process_instance` method filters the input data to only include the expected keys and then instantiates a `ProcessInstanceApi` object. It uses `marshmallow.INCLUDE` for unknown fields.

4.  **Replacement Strategy:**

    *   **For `ProcessInstanceModelSchema`:**
        *   This schema seems to be used for serialization. I will examine where it is used. If its serialization logic is different from the `serialized` method on `ProcessInstanceModel`, I will create a new serialization method on `ProcessInstanceModel` to replicate its behavior. Otherwise, I will replace its usage with the existing `serialized` method.
        *   I will search for `ProcessInstanceModelSchema().dump(data)` and `ProcessInstanceModelSchema().dumps(data)` to find where it is used and then replace it.

    *   **For `ProcessInstanceApiSchema`:**
        *   Create a `from_dict` class method on the `ProcessInstanceApi` class.
        *   This method will take a dictionary and instantiate a `ProcessInstanceApi` object.
        *   The logic from `make_process_instance` will be moved into this new `from_dict` method, including the filtering of keys.

5.  **Step-by-step Implementation:**
    1.  Investigate the usage of `ProcessInstanceModelSchema`.
    2.  If necessary, create a new serialization method on `ProcessInstanceModel` that produces the same output as `ProcessInstanceModelSchema`.
    3.  Replace all uses of `ProcessInstanceModelSchema` with the appropriate serialization method.
    4.  Create a `from_dict` class method on the `ProcessInstanceApi` class.
    5.  Copy the key-filtering logic from `ProcessInstanceApiSchema.make_process_instance` into `ProcessInstanceApi.from_dict`.
    6.  Search the codebase for usages of `ProcessInstanceApiSchema`.
    7.  Replace `ProcessInstanceApiSchema().load(data)` with `ProcessInstanceApi.from_dict(data)`.
    8.  Once all references are removed, delete both marshmallow schemas and their imports from the file.
