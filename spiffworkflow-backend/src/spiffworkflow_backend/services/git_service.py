"""Git_service."""
import os
import shutil
import uuid
from typing import Optional

from flask import current_app
from flask import g

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
    def commit(message: str, repo_path: Optional[str] = None) -> str:
        """Commit."""
        repo_path_to_use = repo_path
        if repo_path is None:
            repo_path_to_use = current_app.config["BPMN_SPEC_ABSOLUTE_DIR"]

        git_username = ""
        git_email = ""
        if current_app.config["GIT_USERNAME"] and current_app.config["GIT_USER_EMAIL"]:
            git_username = current_app.config["GIT_USERNAME"]
            git_email = current_app.config["GIT_USER_EMAIL"]
        shell_command_path = os.path.join(
            current_app.root_path, "..", "..", "bin", "git_commit_bpmn_models_repo"
        )
        shell_command = f"{shell_command_path} '{repo_path_to_use}' '{message}' '{git_username}' '{git_email}'"
        output = os.popen(shell_command).read()  # noqa: S605
        return output

    @classmethod
    def publish(cls, process_model_id: str, branch_to_update: str) -> str:
        """Publish."""
        source_process_model_root = FileSystemService.root_path()
        source_process_model_path = os.path.join(
            source_process_model_root, process_model_id
        )
        unique_hex = uuid.uuid4().hex
        clone_dir = f"sample-process-models.{unique_hex}"

        # clone new instance of sample-process-models, checkout branch_to_update
        # we are adding a guid to this so the flake8 issue has been mitigated
        destination_process_root = f"/tmp/{clone_dir}"  # noqa

        cmd = (
            f"git clone https://{current_app.config['GIT_USERNAME']}:{current_app.config['GIT_USER_PASSWORD']}"
            f"@github.com/sartography/sample-process-models.git {destination_process_root}"
        )
        os.system(cmd)  # noqa: S605
        with FileSystemService.cd(destination_process_root):
            # create publish branch from branch_to_update
            os.system(f"git checkout {branch_to_update}")  # noqa: S605
            publish_branch = f"publish-{process_model_id}"
            command = f"git show-ref --verify refs/remotes/origin/{publish_branch}"
            output = os.popen(command).read()  # noqa: S605
            if output:
                os.system(f"git checkout {publish_branch}")  # noqa: S605
            else:
                os.system(f"git checkout -b {publish_branch}")  # noqa: S605

            # copy files from process model into the new publish branch
            destination_process_model_path = os.path.join(
                destination_process_root, process_model_id
            )
            if os.path.exists(destination_process_model_path):
                shutil.rmtree(destination_process_model_path)
            shutil.copytree(source_process_model_path, destination_process_model_path)

            # add and commit files to publish_branch, then push
            commit_message = f"Request to publish changes to {process_model_id}, from {g.user.username}"
            cls.commit(commit_message, destination_process_root)
            os.system("git push")  # noqa

            # build url for github page to open PR
            output = os.popen("git config --get remote.origin.url").read()  # noqa
            remote_url = output.strip().replace(".git", "")
            pr_url = f"{remote_url}/compare/{publish_branch}?expand=1"

        # try to clean up
        if os.path.exists(destination_process_root):
            shutil.rmtree(destination_process_root)

        return pr_url
