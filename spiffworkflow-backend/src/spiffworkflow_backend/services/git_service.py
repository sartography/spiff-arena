"""Git_service."""
import os
import shutil
import subprocess  # noqa we need the subprocess module to safely run the git commands
import uuid
from typing import Optional
from typing import Union

from flask import current_app
from flask import g

from spiffworkflow_backend.config import ConfigurationError
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.file_system_service import FileSystemService


class MissingGitConfigsError(Exception):
    """MissingGitConfigsError."""


class InvalidGitWebhookBodyError(Exception):
    """InvalidGitWebhookBodyError."""


class GitCloneUrlMismatchError(Exception):
    """GitCloneUrlMismatchError."""


class GitCommandError(Exception):
    """GitCommandError."""


# TOOD: check for the existence of git and configs on bootup if publishing is enabled
class GitService:
    """GitService."""

    @classmethod
    def get_current_revision(cls) -> str:
        """Get_current_revision."""
        bpmn_spec_absolute_dir = current_app.config["BPMN_SPEC_ABSOLUTE_DIR"]
        # The value includes a carriage return character at the end, so we don't grab the last character
        with FileSystemService.cd(bpmn_spec_absolute_dir):
            return cls.run_shell_command_to_get_stdout(
                ["git", "rev-parse", "--short", "HEAD"]
            )

    @classmethod
    def get_instance_file_contents_for_revision(
        cls,
        process_model: ProcessModelInfo,
        revision: str,
        file_name: Optional[str] = None,
    ) -> str:
        """Get_instance_file_contents_for_revision."""
        bpmn_spec_absolute_dir = current_app.config["BPMN_SPEC_ABSOLUTE_DIR"]
        process_model_relative_path = FileSystemService.process_model_relative_path(
            process_model
        )
        file_name_to_use = file_name
        if file_name_to_use is None:
            file_name_to_use = process_model.primary_file_name
        with FileSystemService.cd(bpmn_spec_absolute_dir):
            shell_command = [
                "git",
                "show",
                f"{revision}:{process_model_relative_path}/{file_name_to_use}",
            ]
            return cls.run_shell_command_to_get_stdout(shell_command)

    @classmethod
    def commit(
        cls,
        message: str,
        repo_path: Optional[str] = None,
        branch_name: Optional[str] = None,
    ) -> str:
        """Commit."""
        cls.check_for_basic_configs()
        branch_name_to_use = branch_name
        if branch_name_to_use is None:
            branch_name_to_use = current_app.config["GIT_BRANCH"]
        repo_path_to_use = repo_path
        if repo_path is None:
            repo_path_to_use = current_app.config["BPMN_SPEC_ABSOLUTE_DIR"]
        if repo_path_to_use is None:
            raise ConfigurationError("BPMN_SPEC_ABSOLUTE_DIR config must be set")
        if current_app.config['GIT_SSH_PRIVATE_KEY']:
            os.environ['GIT_SSH_PRIVATE_KEY'] = current_app.config['GIT_SSH_PRIVATE_KEY']

        git_username = ""
        git_email = ""
        if current_app.config["GIT_USERNAME"] and current_app.config["GIT_USER_EMAIL"]:
            git_username = current_app.config["GIT_USERNAME"]
            git_email = current_app.config["GIT_USER_EMAIL"]
        shell_command_path = os.path.join(
            current_app.root_path, "..", "..", "bin", "git_commit_bpmn_models_repo"
        )
        shell_command = [
            shell_command_path,
            repo_path_to_use,
            message,
            branch_name_to_use,
            git_username,
            git_email,
            current_app.config["GIT_USER_PASSWORD"],
        ]
        return cls.run_shell_command_to_get_stdout(shell_command)

    @classmethod
    def check_for_basic_configs(cls) -> None:
        """Check_for_basic_configs."""
        if current_app.config["GIT_BRANCH"] is None:
            raise MissingGitConfigsError(
                "Missing config for GIT_BRANCH. "
                "This is required for publishing process models"
            )

    @classmethod
    def check_for_publish_configs(cls) -> None:
        """Check_for_configs."""
        cls.check_for_basic_configs()
        if current_app.config["GIT_BRANCH_TO_PUBLISH_TO"] is None:
            raise MissingGitConfigsError(
                "Missing config for GIT_BRANCH_TO_PUBLISH_TO. "
                "This is required for publishing process models"
            )
        if current_app.config["GIT_CLONE_URL_FOR_PUBLISHING"] is None:
            raise MissingGitConfigsError(
                "Missing config for GIT_CLONE_URL_FOR_PUBLISHING. "
                "This is required for publishing process models"
            )

    @classmethod
    def run_shell_command_as_boolean(cls, command: list[str]) -> bool:
        """Run_shell_command_as_boolean."""
        # we know result will be a bool here
        result: bool = cls.run_shell_command(command, return_success_state=True)  # type: ignore
        return result

    @classmethod
    def run_shell_command_to_get_stdout(cls, command: list[str]) -> str:
        """Run_shell_command_to_get_stdout."""
        # we know result will be a CompletedProcess here
        result: subprocess.CompletedProcess[bytes] = cls.run_shell_command(
            command, return_success_state=False
        )  # type: ignore
        return result.stdout.decode("utf-8").strip()

    @classmethod
    def run_shell_command(
        cls, command: list[str], return_success_state: bool = False
    ) -> Union[subprocess.CompletedProcess[bytes], bool]:
        """Run_shell_command."""
        # this is fine since we pass the commands directly
        result = subprocess.run(command, check=False, capture_output=True)  # noqa
        if return_success_state:
            return result.returncode == 0

        if result.returncode != 0:
            stdout = result.stdout.decode("utf-8")
            stderr = result.stderr.decode("utf-8")
            raise GitCommandError(
                f"Failed to execute git command: {command} "
                f"Stdout: {stdout} "
                f"Stderr: {stderr} "
            )

        return result

    # only supports github right now
    @classmethod
    def handle_web_hook(cls, webhook: dict) -> bool:
        """Handle_web_hook."""
        cls.check_for_publish_configs()

        if "repository" not in webhook or "clone_url" not in webhook["repository"]:
            raise InvalidGitWebhookBodyError(
                "Cannot find required keys of 'repository:clone_url' from webhook"
                f" body: {webhook}"
            )

        clone_url = webhook["repository"]["clone_url"]
        if clone_url != current_app.config["GIT_CLONE_URL_FOR_PUBLISHING"]:
            raise GitCloneUrlMismatchError(
                "Configured clone url does not match clone url from webhook:"
                f" {clone_url}"
            )

        if "ref" not in webhook:
            raise InvalidGitWebhookBodyError(
                f"Could not find the 'ref' arg in the webhook boy: {webhook}"
            )

        if current_app.config["GIT_BRANCH"] is None:
            raise MissingGitConfigsError(
                "Missing config for GIT_BRANCH. This is required for updating the"
                " repository as a result of the webhook"
            )

        ref = webhook["ref"]
        git_branch = current_app.config["GIT_BRANCH"]
        if ref != f"refs/heads/{git_branch}":
            return False

        with FileSystemService.cd(current_app.config["BPMN_SPEC_ABSOLUTE_DIR"]):
            cls.run_shell_command(["git", "pull"])
        return True

    @classmethod
    def publish(cls, process_model_id: str, branch_to_update: str) -> str:
        """Publish."""
        cls.check_for_publish_configs()
        source_process_model_root = FileSystemService.root_path()
        source_process_model_path = os.path.join(
            source_process_model_root, process_model_id
        )
        unique_hex = uuid.uuid4().hex
        clone_dir = f"sample-process-models.{unique_hex}"

        # clone new instance of sample-process-models, checkout branch_to_update
        # we are adding a guid to this so the flake8 issue has been mitigated
        destination_process_root = f"/tmp/{clone_dir}"  # noqa

        git_clone_url = current_app.config["GIT_CLONE_URL_FOR_PUBLISHING"]
        if git_clone_url.startswith('https://'):
            git_clone_url = git_clone_url.replace(
                "https://",
                f"https://{current_app.config['GIT_USERNAME']}:{current_app.config['GIT_USER_PASSWORD']}@",
            )
        cmd = ["git", "clone", git_clone_url, destination_process_root]

        cls.run_shell_command(cmd)
        with FileSystemService.cd(destination_process_root):
            # create publish branch from branch_to_update
            cls.run_shell_command(["git", "checkout", branch_to_update])
            branch_to_pull_request = f"publish-{process_model_id}"

            # check if branch exists and checkout appropriately
            command = [
                "git",
                "show-ref",
                "--verify",
                f"refs/remotes/origin/{branch_to_pull_request}",
            ]
            if cls.run_shell_command_as_boolean(command):
                cls.run_shell_command(["git", "checkout", branch_to_pull_request])
            else:
                cls.run_shell_command(["git", "checkout", "-b", branch_to_pull_request])

            # copy files from process model into the new publish branch
            destination_process_model_path = os.path.join(
                destination_process_root, process_model_id
            )
            if os.path.exists(destination_process_model_path):
                shutil.rmtree(destination_process_model_path)
            shutil.copytree(source_process_model_path, destination_process_model_path)

            # add and commit files to branch_to_pull_request, then push
            commit_message = (
                f"Request to publish changes to {process_model_id}, "
                f"from {g.user.username} on {current_app.config['ENV_IDENTIFIER']}"
            )
            cls.commit(commit_message, destination_process_root, branch_to_pull_request)

            # build url for github page to open PR
            git_remote = cls.run_shell_command_to_get_stdout(
                ["git", "config", "--get", "remote.origin.url"]
            )
            remote_url = git_remote.strip().replace(".git", "")
            pr_url = f"{remote_url}/compare/{branch_to_update}...{branch_to_pull_request}?expand=1"

        # try to clean up
        if os.path.exists(destination_process_root):
            shutil.rmtree(destination_process_root)

        return pr_url
