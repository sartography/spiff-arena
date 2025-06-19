# Plan to Remove Marshmallow from `process_group.py`

The `process_group.py` file defines four Marshmallow schemas that need to be removed: `MessageSchema`, `RetrievalExpressionSchema`, `CorrelationPropertySchema`, and `ProcessGroupSchema`. The goal is to replace this functionality with dataclasses and custom serialization/deserialization methods.

---

### Phase 1: `MessageSchema` and `RetrievalExpressionSchema`

These two schemas are simple and have no dependencies on other schemas in this file, making them good candidates for the first phase of refactoring.

**1. `MessageSchema`**

*   **Current Implementation:**
    ```python
    class MessageSchema(Schema):
        class Meta:
            fields = ["id", "schema"]
    ```

*   **Analysis:** This schema is used in `ProcessGroupSchema` to validate a list of messages.

*   **Proposed Change:** Replace `MessageSchema` with a `Message` dataclass.

    ```python
    @dataclass
    class Message:
        id: str
        schema: dict

        def to_dict(self):
            return dataclasses.asdict(self)

        @classmethod
        def from_dict(cls, data: dict):
            return cls(**data)
    ```

**2. `RetrievalExpressionSchema`**

*   **Current Implementation:**
    ```python
    class RetrievalExpressionSchema(Schema):
        class Meta:
            fields = ["message_ref", "formal_expression"]
    ```
*   **Analysis:** This schema is nested within `CorrelationPropertySchema`.

*   **Proposed Change:** Replace `RetrievalExpressionSchema` with a `RetrievalExpression` dataclass.
    ```python
    @dataclass
    class RetrievalExpression:
        message_ref: str
        formal_expression: str

        def to_dict(self):
            return dataclasses.asdict(self)

        @classmethod
        def from_dict(cls, data: dict):
            return cls(**data)
    ```

---

### Phase 2: `CorrelationPropertySchema`

This schema depends on `RetrievalExpressionSchema`, so it should be refactored after `RetrievalExpressionSchema` has been replaced.

**1. `CorrelationPropertySchema`**

*   **Current Implementation:**
    ```python
    class CorrelationPropertySchema(Schema):
        class Meta:
            fields = ["id", "retrieval_expression"]

        retrieval_expression = marshmallow.fields.Nested(RetrievalExpressionSchema, required=False)
    ```
*   **Analysis:** This schema nests `RetrievalExpressionSchema`.

*   **Proposed Change:** Replace `CorrelationPropertySchema` with a `CorrelationProperty` dataclass that uses the `RetrievalExpression` dataclass.
    ```python
    @dataclass
    class CorrelationProperty:
        id: str
        retrieval_expression: RetrievalExpression | None = None

        def to_dict(self):
            data = dataclasses.asdict(self)
            if self.retrieval_expression:
                data['retrieval_expression'] = self.retrieval_expression.to_dict()
            return data

        @classmethod
        def from_dict(cls, data: dict):
            if 'retrieval_expression' in data and data['retrieval_expression'] is not None:
                data['retrieval_expression'] = RetrievalExpression.from_dict(data['retrieval_expression'])
            return cls(**data)
    ```

---

### Phase 3: `ProcessGroupSchema`

This is the most complex schema, with multiple nested schemas. It should be refactored last.

**1. `ProcessGroupSchema`**

*   **Current Implementation:**
    ```python
    class ProcessGroupSchema(Schema):
        class Meta:
            model = ProcessGroup
            fields = [
                "id",
                "display_name",
                "process_models",
                "description",
                "process_groups",
                "messages",
                "correlation_properties",
            ]

        process_models = marshmallow.fields.List(marshmallow.fields.Nested("ProcessModelInfoSchema", dump_only=True, required=False))
        process_groups = marshmallow.fields.List(marshmallow.fields.Nested("ProcessGroupSchema", dump_only=True, required=False))
        messages = marshmallow.fields.List(marshmallow.fields.Nested(MessageSchema, dump_only=True, required=False))
        correlation_properties = marshmallow.fields.List(
            marshmallow.fields.Nested(CorrelationPropertySchema, dump_only=True, required=False)
        )

        @post_load
        def make_process_group(self, data: dict[str, str | bool | int], **kwargs: dict) -> ProcessGroup:
            return ProcessGroup(**data)
    ```
*   **Analysis:** This schema is used in `process_groups_controller.py` and `process_model_service.py`. It has nested schemas for `process_models`, `process_groups`, `messages`, and `correlation_properties`.

*   **Proposed Change:** The `ProcessGroup` dataclass already exists. We will augment it with `to_dict` and `from_dict` methods to handle serialization and deserialization, including the nested structures.

### Execution Plan:

1.  **Implement Dataclasses:**
    *   Add the `Message`, `RetrievalExpression`, and `CorrelationProperty` dataclasses to `process_group.py`.
    *   Remove the corresponding Marshmallow schemas: `MessageSchema`, `RetrievalExpressionSchema`, `CorrelationPropertySchema`.

2.  **Update `ProcessGroup` Dataclass:**
    *   Add `to_dict` and `from_dict` methods to the `ProcessGroup` dataclass. These methods will handle the serialization and deserialization of the nested dataclasses.
    *   Remove `ProcessGroupSchema` entirely.

3.  **Refactor Code:** Search for all usages of `ProcessGroupSchema` and update them to use the new methods on `ProcessGroup`. This will likely involve changes in API endpoints and service layers where serialization/deserialization occurs.

*   `tests/spiffworkflow_backend/integration/test_nested_groups.py`:
    -   Replace `ProcessGroupSchema().dump(process_group)` with `process_group.to_dict()`
*   `tests/spiffworkflow_backend/helpers/base_test.py`:
    -   Replace `ProcessGroupSchema().dump(process_group)` with `process_group.to_dict()`
*   `src/spiffworkflow_backend/routes/process_groups_controller.py`:
    -   Replace `ProcessGroupSchema(many=True).dump(batch)` with `[group.to_dict() for group in batch]`
*   `src/spiffworkflow_backend/services/process_model_service.py`:
    -   Remove the `GROUP_SCHEMA` class variable.
    -   Replace `self.GROUP_SCHEMA.load(data)` with `ProcessGroup.from_dict(data)`

By following this plan, we can systematically remove Marshmallow from `process_group.py` while maintaining the existing functionality.
