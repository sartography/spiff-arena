import os
import tempfile

from flask import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestGlobalScripts(BaseTest):
    def test_global_script_loading_and_execution(self, app: Flask, client: TestClient) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            global_scripts_dir = os.path.join(tmp_dir, "global-scripts")
            os.makedirs(global_scripts_dir)

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

            with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR", tmp_dir):
                with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_GLOBAL_SCRIPTS_DIR", "global-scripts"):
                    # Reset Script.SCRIPT_SUB_CLASSES to None to force reloading
                    # We can reset it by accessing the module
                    import spiffworkflow_backend.scripts.script as script_module

                    try:
                        script_module.SCRIPT_SUB_CLASSES = None

                        subclasses = Script.get_all_subclasses()
                        hello_world_class = next((s for s in subclasses if s.__name__ == "HelloWorld"), None)

                        assert hello_world_class is not None, "HelloWorld class should be loaded from global scripts"

                        script_instance = hello_world_class()
                        context = ScriptAttributesContext(
                            task=None, environment_identifier="testing", process_instance_id=1, process_model_identifier="test"
                        )
                        result = script_instance.run(context)

                        assert result == "Hello World from Global Script"
                    finally:
                        # Clean up: Reset SCRIPT_SUB_CLASSES again so it doesn't affect other tests
                        script_module.SCRIPT_SUB_CLASSES = None
