### Plan to remove marshmallow from `src/spiffworkflow_backend/models/task.py`

1.  **Identify marshmallow usage:** The file `src/spiffworkflow_backend/models/task.py` defines five marshmallow schemas: `OptionSchema`, `ValidationSchema`, `FormFieldPropertySchema`, `FormFieldSchema`, and `TaskSchema`.

2.  **Analyze Schemas:**
    *   `TaskSchema`: This is the main schema. It serializes a `Task` object. It uses `marshmallow_enum.EnumField` for the `multi_instance_type` field. The `make_task` method instantiates a `Task` object.
    *   `FormFieldSchema`, `OptionSchema`, `ValidationSchema`, `FormFieldPropertySchema`: These schemas are for form fields and their components. They are nested within each other but don't seem to directly correspond to existing dataclasses in the file. The `FormSchema` is commented out, which might simplify things.

3.  **Replacement Strategy:**

    *   **For `TaskSchema`:**
        *   Create a `from_dict` class method on the `Task` class.
        *   This method will take a dictionary and instantiate a `Task` object.
        *   The logic will be similar to `TaskSchema.make_task`.
        *   The `multi_instance_type` field will need to be handled, converting the string from the dictionary to a `MultiInstanceType` enum.

    *   **For Form Field Schemas:**
        *   These schemas seem to be used for validating and serializing form field data. Since there are no corresponding dataclasses, I'll need to create them.
        *   Create `Option`, `Validation`, `FormFieldProperty`, and `FormField` dataclasses.
        *   Each of these dataclasses will have a `from_dict` class method to instantiate it from a dictionary.
        *   This will allow for structured data and remove the need for the marshmallow schemas.

4.  **Step-by-step Implementation:**
    1.  Create `Option`, `Validation`, `FormFieldProperty`, and `FormField` dataclasses with the fields defined in their respective marshmallow schemas.
    2.  Implement `from_dict` class methods on each of these new dataclasses.
    3.  Create a `from_dict` class method on the `Task` class.
    4.  Move the logic from `TaskSchema.make_task` into `Task.from_dict`.
    5.  Handle the `multi_instance_type` enum conversion within `Task.from_dict`.
    6.  If the `form` data is present, use the new `FormField.from_dict` method to process it.
    7.  Search the codebase for usages of all five schemas.
    8.  Replace `TaskSchema().load(data)` with `Task.from_dict(data)`.
    9.  Replace any usage of the form field schemas with direct instantiation or the `from_dict` methods of the new dataclasses.
    10. Once all references are removed, delete all five marshmallow schemas and their imports from the file.
