### Plan to Remove Marshmallow from `task.py`

The file `src/spiffworkflow_backend/models/task.py` is the most complex file in terms of Marshmallow usage. It contains five schemas: `OptionSchema`, `ValidationSchema`, `FormFieldPropertySchema`, `FormFieldSchema`, and `TaskSchema`. The strategy will be to replace each of these with a dataclass and then update the parent containers.

**1. Bottom-Up Replacement: Form Field Schemas**

We'll start with the schemas that are nested within others.

*   **`OptionSchema`**:
    *   **Current:** `class OptionSchema(Schema): class Meta: fields = ["id", "name", "data"]`
    *   **Proposed:** Create an `Option` dataclass.
      ```python
      from dataclasses import dataclass
      from typing import Any

      @dataclass
      class Option:
          id: str
          name: str
          data: Any
      ```

*   **`ValidationSchema`**:
    *   **Current:** `class ValidationSchema(Schema): class Meta: fields = ["name", "config"]`
    *   **Proposed:** Create a `Validation` dataclass.
      ```python
      @dataclass
      class Validation:
          name: str
          config: Any
      ```

*   **`FormFieldPropertySchema`**:
    *   **Current:** `class FormFieldPropertySchema(Schema): class Meta: fields = ["id", "value"]`
    *   **Proposed:** Create a `FormFieldProperty` dataclass.
      ```python
      @dataclass
      class FormFieldProperty:
          id: str
          value: Any
      ```

**2. `FormFieldSchema` Replacement**

This schema composes the smaller schemas from step 1.

*   **Current Implementation:**
    ```python
    class FormFieldSchema(Schema):
        class Meta: fields = [...]
        options = marshmallow.fields.List(marshmallow.fields.Nested(OptionSchema))
        validation = marshmallow.fields.List(marshmallow.fields.Nested(ValidationSchema))
        properties = marshmallow.fields.List(marshmallow.fields.Nested(FormFieldPropertySchema))
    ```
*   **Analysis:** This defines the structure of a single field within a form.
*   **Proposed Change:** Replace it with a `FormField` dataclass that uses the new dataclasses defined above. We will also add `from_dict` and `to_dict` methods to handle the nested structures.

    ```python
    from dataclasses import field, asdict

    @dataclass
    class FormField:
        id: str
        type: str
        label: str
        default_value: str | None = None
        options: list[Option] = field(default_factory=list)
        validation: list[Validation] = field(default_factory=list)
        properties: list[FormFieldProperty] = field(default_factory=list)
        value: Any | None = None

        @classmethod
        def from_dict(cls, data: dict) -> "FormField":
            data['options'] = [Option(**o) for o in data.get('options', [])]
            data['validation'] = [Validation(**v) for v in data.get('validation', [])]
            data['properties'] = [FormFieldProperty(**p) for p in data.get('properties', [])]
            return cls(**data)

        def to_dict(self) -> dict:
            return asdict(self)
    ```

**3. `TaskSchema` Replacement**

This is the top-level schema for the `Task` object.

*   **Current Implementation:** A `TaskSchema` with a `post_load` method that creates a `Task` object.
*   **Analysis:** It serializes and deserializes the main `Task` object. The existing `Task` class is a plain class with a large `__init__`.
*   **Proposed Change:**
    *   Convert the `Task` class into a dataclass. This will simplify its definition.
    *   Remove the `TaskSchema` entirely.
    *   Add `from_dict` and `to_dict` methods to the `Task` dataclass. The `from_dict` method will handle the logic of instantiating the object from a dictionary, and `to_dict` will replace the schema's dump functionality. The existing `serialized()` method can be adapted or replaced by `to_dict`.

*   **`Task` Dataclass Implementation:**

    ```python
    from dataclasses import dataclass, field, asdict

    @dataclass
    class Task:
        id: str
        # ... all other fields from the original __init__ ...

        # We can probably remove the complex __init__ method and just use the dataclass's default.
        # We might need a __post_init__ if there's complex logic.

        @classmethod
        def from_dict(cls, data: dict) -> "Task":
            # This method will handle nested objects like 'form' if needed.
            # It will also need to handle the Enum conversion for multi_instance_type.
            field_names = {f.name for f in cls.__dataclass_fields__.values()}
            filtered_data = {k: v for k, v in data.items() if k in field_names}
            # Add logic for nested `form` and `EnumField`
            return cls(**filtered_data)

        def to_dict(self) -> dict:
            # Replaces the old `serialized()` method.
            data = asdict(self)
            # Handle enum serialization if needed
            if self.multi_instance_type:
                data['multi_instance_type'] = self.multi_instance_type.value
            return data
    ```

**Execution Plan:**

1.  **Implement Dataclasses:**
    *   Create the `Option`, `Validation`, and `FormFieldProperty` dataclasses.
    *   Create the `FormField` dataclass with its `from_dict` and `to_dict` methods.
2.  **Refactor the `Task` Class:**
    *   Convert the existing `Task` class to a `@dataclass`.
    *   Add the `from_dict` and `to_dict` methods. This will likely involve adapting the logic from the old `__init__` and `serialized` methods.
3.  **Update References:**
    *   Search the entire codebase for usages of `TaskSchema`, `FormFieldSchema`, etc.
    *   Replace all `Schema().load(data)` calls with the corresponding `ClassName.from_dict(data)`.
    *   Replace all `Schema().dump(obj)` calls with `obj.to_dict()`.
4.  **Remove Schemas:** Delete all five Marshmallow schemas from `task.py`.
5.  **Test:** Thoroughly run the test suite to ensure that task serialization and deserialization work correctly across the application, especially in API endpoints that rely on this model.
