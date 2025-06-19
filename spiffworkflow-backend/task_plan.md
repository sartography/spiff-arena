# Plan to Remove Marshmallow from `task.py`

The file `src/spiffworkflow_backend/models/task.py` is the most complex file in terms of Marshmallow usage. It contains five schemas: `OptionSchema`, `ValidationSchema`, `FormFieldPropertySchema`, `FormFieldSchema`, and `TaskSchema`. The strategy will be to replace each of these with a dataclass and then update the parent containers.

---

### Phase 1: Simple Schemas

**1. `OptionSchema`**

*   **Current Implementation:**
    ```python
    class OptionSchema(Schema):
        class Meta:
            fields = ["id", "name", "data"]
    ```
*   **Proposed Change:** Replace with `Option` dataclass.

**2. `ValidationSchema`**

*   **Current Implementation:**
    ```python
    class ValidationSchema(Schema):
        class Meta:
            fields = ["name", "config"]
    ```
*   **Proposed Change:** Replace with `Validation` dataclass.

**3. `FormFieldPropertySchema`**

*   **Current Implementation:**
    ```python
    class FormFieldPropertySchema(Schema):
        class Meta:
            fields = ["id", "value"]
    ```
*   **Proposed Change:** Replace with `FormFieldProperty` dataclass.

### Phase 2: `FormFieldSchema` Replacement

**1. `FormFieldSchema`**

*   **Current Implementation:**
    ```python
    class FormFieldSchema(Schema):
        class Meta:
            fields = [
                "id",
                "type",
                "label",
                "default_value",
                "options",
                "validation",
                "properties",
                "value",
            ]

        default_value = marshmallow.fields.String(required=False, allow_none=True)
        options = marshmallow.fields.List(marshmallow.fields.Nested(OptionSchema))
        validation = marshmallow.fields.List(marshmallow.fields.Nested(ValidationSchema))
        properties = marshmallow.fields.List(marshmallow.fields.Nested(FormFieldPropertySchema))
    ```
*   **Analysis:** This schema nests `OptionSchema`, `ValidationSchema`, and `FormFieldPropertySchema`.
*   **Proposed Change:** Replace with a `FormField` dataclass that uses the new dataclasses from Phase 1.

### Phase 3: `TaskSchema` Replacement

**1. `TaskSchema`**

*   **Current Implementation:** A `TaskSchema` with a `post_load` method that creates a `Task` object.
*   **Analysis:** This is the root schema for task-related serialization.
*   **Proposed Change:**
    *   The `Task` class already exists and will be converted to a dataclass.
    *   `to_dict` and `from_dict` methods will be added to handle serialization.
    *   Remove the `TaskSchema` entirely.

### Execution Plan:

1.  **Create Dataclasses:**
    *   Define `Option`, `Validation`, and `FormFieldProperty` dataclasses.
    *   Add `to_dict` and `from_dict` methods to each.
    *   Remove the corresponding Marshmallow schemas.

2.  **Update `FormFieldSchema`:**
    *   Define the `FormField` dataclass.
    *   Update its `to_dict` and `from_dict` methods to handle the nested `Option`, `Validation`, and `FormFieldProperty` dataclasses.
    *   Remove the `FormFieldSchema`.

3.  **Update `Task` Class:**
    *   Convert the `Task` class to a dataclass.
    *   Add `to_dict` and `from_dict` methods.
    *   Remove `TaskSchema`.

4.  **Refactor Code:**
    *   Search the entire codebase for usages of `TaskSchema`, `FormFieldSchema`, etc.
    *   Replace all usages with the new dataclasses and their methods. This will primarily affect `spiffworkflow_backend/routes/tasks_controller.py` and any other locations where task serialization is performed.

By breaking down the task into these phases, we can incrementally replace the Marshmallow schemas with dataclasses without breaking the application.
