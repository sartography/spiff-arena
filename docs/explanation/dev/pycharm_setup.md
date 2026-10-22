# PyCharm Setup Instructions

This guide provides instructions for setting up PyCharm IDE for SpiffWorkflow backend development.

## Pre-Requisites
* Before starting, ensure you can run `bin/run_server_locally` script successfully.
  This will prove that your libraries are properly configured.
* Checkout a git repository with sample process models such as our [Sample Process Models](https://github.com/sartography/sample-process-models)

## Step 1 - Python Interpreter
Run `uv sync` in `spiffworkflow-backend/`, then configure PyCharm's Python interpreter to use `spiffworkflow-backend/.venv/bin/python`.

## Step 2 - Configuration Settings
Create a config.py file in the src/instance directory, with the following base settings
```python
FLASK_SESSION_SECRET_KEY="[PUT SOME RANDOM STUFF HERE]"
SPIFFWORKFLOW_BACKEND_APPLICATION_ROOT="/"
SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR="[FULL PATH TO SAMPLE PROCESS MODEL GIT CLONE]"

# This will configure your application to use a built in login rather than
# relying on keycloak etc...
SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS = [
    {
    "identifier":"default",
    "label":"internal openid",
    "uri":"http://localhost:7000/openid",
    "client_id":"spiffworkflow-backend",
    "client_secret":"JXeQExm0JhQPLumgHtIIqf52bDalHz0q"
    }
]

# You can modify the permissions by creating your own permissions file and setting it here.
# See example.yml in the src/spiffworkflow_backend/config/permissions directory
SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME="example.yml"
```

Check the default.py config file in src/spiffworkflow_backend/config directory for more options you can specify as needed.

## Step 3 - Run Configuration

Configure your Run configuration with the following settings:
* Select Flask Server as the run type
* Set the target to: spiffworkflow_backend
* Set the port to 7000 (-p 7000)
* See the screenshot below for reference:

![PyCharm Run Configuration](../../pycharm_config.png)

## Step 4 - Code Formatting

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting. Configure PyCharm's Ruff integration to use the repository's settings.

Start the application using the play / debug buttons.

## IMPORTANT
* Before committing changes to the repository, be sure to execute the `run_pyl` command in the top level spiff-arena directory and fix any issues it reports.
* Run `uv sync` at the repository root as well; the top-level checks use a separate environment from the backend.