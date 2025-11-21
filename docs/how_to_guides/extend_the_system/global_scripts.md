# Global Scripts

Global Scripts allow you to define custom Python functions that can be used across all your process models.
They're automatically loaded from a directory in your process model repository.
If you need to make network calls, use connectors instead.

## Configuration

Global Scripts are **disabled by default**. To enable:

```bash
SPIFFWORKFLOW_BACKEND_GLOBAL_SCRIPTS_DIR_NAME=global-scripts
```

Scripts go in `process-models/global-scripts/` (or whatever directory you specify).

## Creating Scripts

Create a Python class that extends `Script`:

```python
from typing import Any
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script

class HelloWorld(Script):
    def get_description(self) -> str:
        return "Returns a greeting"

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> Any:
        return "Hello World"
```

Class names are converted to snake_case: `HelloWorld` → `hello_world()`

Save this in `hello_world.py` (file names should match the function name).

## Usage

Use your scripts in process models:

```python
# In script tasks
result = hello_world()

# In expressions
if hello_world() == "Hello World":
    # do something
```

