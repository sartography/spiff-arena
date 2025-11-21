import os
import shutil
import tempfile
from typing import Any

from flask import Flask, current_app
from starlette.testclient import TestClient

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestGlobalScripts(BaseTest):
    def test_global_script_loading_and_execution(self, app: Flask, client: TestClient) -> None:
        # 1. Create a temporary directory for the process model repo
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 2. Create a global-scripts directory inside it
            global_scripts_dir = os.path.join(tmp_dir, "global-scripts")
            os.makedirs(global_scripts_dir)

            # 3. Create a hello_world.py script inside global-scripts
            script_content = """
from typing import Any
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script

class HelloWorld(Script):
    def get_description(self) -> str:
        return "Returns Hello World"

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> Any:
        return "Hello World from Global Script"
"""
            with open(os.path.join(global_scripts_dir, "hello_world.py"), "w") as f:
                f.write(script_content)

            # 4. Configure SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR to point to the temp dir
            # We use app_config_mock to safely modify the config for this test
            with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR", tmp_dir):
                
                # 5. Reset Script.SCRIPT_SUB_CLASSES to None to force reloading
                # We need to access the global variable in the script module
                # Since SCRIPT_SUB_CLASSES is a global in script.py, we can modify it via the class method or direct access if imported
                # Script.SCRIPT_SUB_CLASSES is not directly exposed as a public attribute to set, but we can set the module level variable
                # or just set the private variable on the class if it was stored there, but it is a module global.
                # Looking at script.py:
                # global SCRIPT_SUB_CLASSES
                # if not SCRIPT_SUB_CLASSES: ...
                
                # We can reset it by accessing the module
                import spiffworkflow_backend.scripts.script as script_module
                script_module.SCRIPT_SUB_CLASSES = None

                # 6. Call Script.get_all_subclasses() and verify HelloWorld is present
                subclasses = Script.get_all_subclasses()
                hello_world_class = next((s for s in subclasses if s.__name__ == "HelloWorld"), None)
                
                assert hello_world_class is not None, "HelloWorld class should be loaded from global scripts"

                # 7. Instantiate HelloWorld and call run
                script_instance = hello_world_class()
                context = ScriptAttributesContext(
                    task=None,
                    environment_identifier="testing",
                    process_instance_id=1,
                    process_model_identifier="test"
                )
                result = script_instance.run(context)
                
                assert result == "Hello World from Global Script"

                # Clean up: Reset SCRIPT_SUB_CLASSES again so it doesn't affect other tests
                script_module.SCRIPT_SUB_CLASSES = None
