"""Git_service."""
import os

from flask import current_app

from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.file_system_service import FileSystemService


class GitService:
    """GitService."""

    @staticmethod
    def get_current_revision() -> str:
        """Get_current_revision."""
        bpmn_spec_absolute_dir = current_app.config["BPMN_SPEC_ABSOLUTE_DIR"]
        # The value includes a carriage return character at the end, so we don't grab the last character
        current_git_revision = os.popen(  # noqa: S605
            f"cd {bpmn_spec_absolute_dir} && git rev-parse --short HEAD"
        ).read()[
            :-1
        ]  # noqa: S605
        return current_git_revision

    @staticmethod
    def get_instance_file_contents_for_revision(
        process_model: ProcessModelInfo, revision: str
    ) -> bytes:
        """Get_instance_file_contents_for_revision."""
        bpmn_spec_absolute_dir = current_app.config["BPMN_SPEC_ABSOLUTE_DIR"]
        process_model_relative_path = FileSystemService.process_model_relative_path(
            process_model
        )
        shell_cd_command = f"cd {bpmn_spec_absolute_dir}"
        shell_git_command = f"git show {revision}:{process_model_relative_path}/{process_model.primary_file_name}"
        shell_command = f"{shell_cd_command} && {shell_git_command}"
        # git show 78ae5eb:category_number_one/script-task/script-task.bpmn
        file_contents: str = os.popen(shell_command).read()[:-1]  # noqa: S605
        assert file_contents  # noqa: S101
        return file_contents.encode("utf-8")

    @staticmethod
    def commit(message: str) -> str:
        """Commit."""
        bpmn_spec_absolute_dir = current_app.config["BPMN_SPEC_ABSOLUTE_DIR"]
        git_username = ""
        git_email = ""
        if (
            current_app.config["GIT_COMMIT_USERNAME"]
            and current_app.config["GIT_COMMIT_EMAIL"]
        ):
            git_username = current_app.config["GIT_COMMIT_USERNAME"]
            git_email = current_app.config["GIT_COMMIT_EMAIL"]
        shell_command = f"./bin/git_commit_bpmn_models_repo '{bpmn_spec_absolute_dir}' '{message}' '{git_username}' '{git_email}'"
        output = os.popen(shell_command).read()  # noqa: S605
        return output
