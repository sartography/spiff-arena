"""Process Model."""

from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.services.git_service import GitService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestGitService(BaseTest):
    def test_strips_output_of_stdout_from_command(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        output = GitService.run_shell_command_to_get_stdout(
            ["echo", "   This output should not end in space  "], prepend_with_git=False
        )
        assert output == "This output should not end in space"
