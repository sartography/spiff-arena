# Global Scripts

Global Scripts in SpiffArena provide a powerful mechanism to extend the system's scripting capabilities by allowing you to define custom script functions that can be used across all your process models. These scripts are automatically loaded and made available throughout your SpiffWorkflow environment, providing a centralized way to add custom business logic.

## Overview

Global Scripts are custom Python classes that extend the base `Script` class and are automatically discovered and loaded from a designated directory in your process model repository. Once loaded, these scripts become available for use in any process model within your SpiffWorkflow instance.

Key benefits:
- **Centralized Logic**: Define reusable business logic in one place
- **Automatic Discovery**: Scripts are automatically loaded without manual registration
- **Consistent API**: Uses the same interface as built-in SpiffWorkflow scripts
- **Process Model Agnostic**: Available across all process models in your instance

## Configuration

### Environment Variables

Global Scripts are **disabled by default** and must be explicitly enabled. They are controlled by two configuration variables:

```bash
# Enable global scripts by setting the directory name (disabled by default)
SPIFFWORKFLOW_BACKEND_GLOBAL_SCRIPTS_DIR_NAME=global-scripts

# Base directory for BPMN specifications (usually already configured)
SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR=/path/to/your/process/models
```

**Important**: If `SPIFFWORKFLOW_BACKEND_GLOBAL_SCRIPTS_DIR_NAME` is not set or is set to an empty value, global scripts will be completely disabled for security reasons.

### Directory Structure

When enabled, Global Scripts are stored in a directory within your process model repository:

```
process-models/
├── global-scripts/          # Directory name set by SPIFFWORKFLOW_BACKEND_GLOBAL_SCRIPTS_DIR_NAME
│   ├── hello_world.py       # Your custom script
│   ├── data_processor.py    # Another custom script
│   └── utility_functions.py # More custom scripts
├── my-process-group/
│   └── my-process-model/
└── another-process-group/
```

## Creating Global Scripts

### Basic Script Structure

All global scripts must extend the `Script` base class and implement the required methods:

```python
from typing import Any
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script

class HelloWorld(Script):
    def get_description(self) -> str:
        return "Returns a friendly greeting message"

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> Any:
        return "Hello World from Global Script"
```

### Script Function Naming

The script function name available in your process models is automatically derived from your class name by converting PascalCase to snake_case:

- `HelloWorld` → `hello_world()`
- `DataProcessor` → `data_processor()`
- `XMLUtility` → `x_m_l_utility()`

### Advanced Example

Here's a more comprehensive example that demonstrates accessing process context and parameters:

```python
from typing import Any
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script

class DataProcessor(Script):
    def get_description(self) -> str:
        return "Processes and validates business data according to company rules"

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> Any:
        # Access process instance information
        process_instance_id = script_attributes_context.process_instance_id
        process_model_id = script_attributes_context.process_model_identifier

        # Get input parameters from the process
        data = kwargs.get('data', {})
        validation_type = kwargs.get('validation_type', 'standard')

        # Perform custom business logic
        if validation_type == 'strict':
            return self._strict_validation(data)
        else:
            return self._standard_validation(data)

    def _strict_validation(self, data: dict) -> dict:
        # Custom validation logic
        processed_data = data.copy()
        processed_data['validated'] = True
        processed_data['validation_level'] = 'strict'
        return processed_data

    def _standard_validation(self, data: dict) -> dict:
        # Standard validation logic
        processed_data = data.copy()
        processed_data['validated'] = True
        processed_data['validation_level'] = 'standard'
        return processed_data
```

## Using Global Scripts in Process Models

Once created, global scripts are automatically available in your process models and can be used in script tasks:

### In a Script Task

```python
# Call your global script function
result = data_processor(
    data={'name': 'John', 'age': 30},
    validation_type='strict'
)

# The result can then be used in your process
validated_user = result
```

### In Expression Fields

Global scripts can also be used in expression fields throughout your BPMN diagrams:

```python
# In a gateway condition
hello_world() == "Hello World from Global Script"

# In variable assignments
user_data = data_processor(data=form_data, validation_type='standard')
```

## Best Practices

### File Organization

- Use descriptive file names that match your class names (e.g., `data_processor.py` for `DataProcessor`)
- Group related functionality into single files when appropriate
- Avoid creating too many small single-purpose scripts

### Script Design

- **Keep scripts focused**: Each script should have a single, well-defined purpose
- **Use descriptive names**: Both class names and function parameters should be self-documenting
- **Handle errors gracefully**: Include appropriate error handling for expected failure cases
- **Document complex logic**: Add docstrings and comments for non-trivial business logic

### Dependencies

- **Import dependencies carefully**: Only import what you need and ensure dependencies are available in your SpiffWorkflow environment
- **Consider portability**: Scripts should work across different environments (dev, staging, production)
- **Avoid external dependencies when possible**: Prefer using Python standard library or dependencies already available in SpiffWorkflow

### Security Considerations

- **Validate inputs**: Always validate and sanitize any external data
- **Avoid system calls**: Don't execute shell commands or file system operations unless absolutely necessary
- **Limit privileges**: Scripts run with the same privileges as the SpiffWorkflow backend

## Testing Global Scripts

### Unit Testing

You can test your global scripts independently:

```python
import unittest
from your_global_scripts.data_processor import DataProcessor
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext

class TestDataProcessor(unittest.TestCase):
    def setUp(self):
        self.script = DataProcessor()
        self.context = ScriptAttributesContext(
            task=None,
            environment_identifier="testing",
            process_instance_id=1,
            process_model_identifier="test"
        )

    def test_standard_validation(self):
        result = self.script.run(
            self.context,
            data={'name': 'John', 'age': 30},
            validation_type='standard'
        )
        self.assertTrue(result['validated'])
        self.assertEqual(result['validation_level'], 'standard')
```

### Integration Testing

Test your scripts within actual process models to ensure they work correctly in the full SpiffWorkflow context.

## Troubleshooting

### Common Issues

**Script not found**:
- **First, verify global scripts are enabled**: Check that `SPIFFWORKFLOW_BACKEND_GLOBAL_SCRIPTS_DIR_NAME` is set (global scripts are disabled by default)
- Verify the file is in the correct directory (as specified by `SPIFFWORKFLOW_BACKEND_GLOBAL_SCRIPTS_DIR_NAME`)
- Check that the class extends `Script` properly
- Ensure there are no Python syntax errors in your script file

**Import errors**:
- Verify all required modules are available in your SpiffWorkflow environment
- Check for circular import dependencies
- Ensure file names don't conflict with Python built-in modules

**Runtime errors**:
- Check the SpiffWorkflow backend logs for detailed error messages
- Verify input parameters match what your script expects
- Test scripts independently before using in process models

### Debugging

Enable debug logging in SpiffWorkflow to see detailed information about script loading and execution:

```bash
export SPIFFWORKFLOW_BACKEND_LOG_LEVEL=DEBUG
```

## Relationship to Extensions

Global Scripts and [Extensions](extensions) serve different but complementary purposes:

- **Global Scripts**: Provide reusable backend logic and data processing functions
- **Extensions**: Add new frontend UI components and user-facing features

You can use both together: Extensions can call Global Scripts through process models to perform backend data processing while providing custom frontend interfaces.

## Migration from Built-in Scripts

If you have custom logic that was previously implemented as patches to SpiffWorkflow's built-in scripts, Global Scripts provide a cleaner way to maintain this functionality:

1. Create a new global script with your custom logic
2. Update your process models to use the new script function name
3. Remove any patches to the core SpiffWorkflow code

This approach makes upgrades easier and keeps your customizations separate from the core system.