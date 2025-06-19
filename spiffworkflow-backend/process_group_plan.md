### Plan to Remove Marshmallow from `process_group.py`

The `process_group.py` file defines four Marshmallow schemas that need to be removed: `MessageSchema`, `RetrievalExpressionSchema`, `CorrelationPropertySchema`, and `ProcessGroupSchema`. The goal is to replace this functionality with dataclasses and custom serialization/deserialization methods.

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
    from dataclasses import dataclass

    @dataclass
    class Message:
        id: str
        schema: dict
    ```
*   **Impact:** The `ProcessGroupSchema` will need to be updated to handle this new dataclass.

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
    from dataclasses import dataclass

    @dataclass
    class RetrievalExpression:
        message_ref: str
        formal_expression: str
    ```

**3. `CorrelationPropertySchema`**

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
    from dataclasses import dataclass, field

    @dataclass
    class CorrelationProperty:
        id: str
        retrieval_expression: RetrievalExpression | None = None
    ```

**4. `ProcessGroupSchema`**

*   **Current Implementation:** This is the most complex schema, with nested schemas and a `post_load` method.
*   **Analysis:** This schema is responsible for serializing and deserializing the `ProcessGroup` object.
*   **Proposed Change:**
    *   Remove `ProcessGroupSchema` entirely.
    *   Add `to_dict` and `from_dict` methods to the `ProcessGroup` dataclass.
    *   The `from_dict` classmethod will handle the logic currently in the `post_load` method.
    *   The `to_dict` method will replace the serialization logic.

    ```python
    @dataclass(order=True)
    class ProcessGroup:
        # ... existing fields ...

        @classmethod
        def from_dict(cls, data: dict) -> "ProcessGroup":
            # Logic to instantiate ProcessGroup from a dictionary,
            # including handling nested objects.
            # This will replace the post_load method.
            pass

        def to_dict(self) -> dict:
            # Logic to serialize ProcessGroup to a dictionary.
            # This will replace the schema's serialization.
            pass
    ```

**Execution Plan:**

1.  **Create Dataclasses:** Define the new `Message`, `RetrievalExpression`, and `CorrelationProperty` dataclasses in `process_group.py`.
2.  **Update `ProcessGroup`:**
    *   Modify the `ProcessGroup` dataclass to use the new dataclasses for `messages` and `correlation_properties`.
    *   Implement the `to_dict` and `from_dict` methods.
3.  **Refactor Code:** Search for all usages of `ProcessGroupSchema` and update them to use the new methods on `ProcessGroup`. This will likely involve changes in API endpoints and service layers where serialization/deserialization occurs.
4.  **Remove Old Schemas:** Once all references are updated, delete the four Marshmallow schemas from `process_group.py`.
5.  **Testing:** Run all tests to ensure that the application functions as expected.
