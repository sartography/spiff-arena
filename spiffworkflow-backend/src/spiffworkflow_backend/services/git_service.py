import os
import re
import shutil
import subprocess  # noqa we need the subprocess module to safely run the git commands
import uuid

from flask import current_app
from flask import g
from spiffworkflow_backend.config import ConfigurationError
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.data_setup_service import DataSetupService
from spiffworkflow_backend.services.file_system_service import FileSystemService


class MissingGitConfigsError(Exception):
    pass


class InvalidGitWebhookBodyError(Exception):
    pass


class GitCloneUrlMismatchError(Exception):
    pass


class GitCommandError(Exception):
    pass


# TOOD: check for the existence of git and configs on bootup if publishing is enabled
class GitService:
    @classmethod
    def get_current_revision(cls) -> str:
        bpmn_spec_absolute_dir = current_app.config["SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR"]
        # The value includes a carriage return character at the end, so we don't grab the last character
        with FileSystemService.cd(bpmn_spec_absolute_dir):
            return cls.run_shell_command_to_get_stdout(["git", "rev-parse", "--short", "HEAD"])

    @classmethod
    def get_instance_file_contents_for_revision(
        cls,
        process_model: ProcessModelInfo,
        revision: str,
        file_name: str | None = None,
    ) -> str:
        bpmn_spec_absolute_dir = current_app.config["SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR"]
        process_model_relative_path = FileSystemService.process_model_relative_path(process_model)
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
        repo_path: str | None = None,
        branch_name: str | None = None,
    ) -> str:
        cls.check_for_basic_configs()
        branch_name_to_use = branch_name
        if branch_name_to_use is None:
            branch_name_to_use = current_app.config["SPIFFWORKFLOW_BACKEND_GIT_SOURCE_BRANCH"]
        repo_path_to_use = repo_path
        if repo_path is None:
            repo_path_to_use = current_app.config["SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR"]
        if repo_path_to_use is None:
            raise ConfigurationError("SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR config must be set")

        shell_command_path = os.path.join(current_app.root_path, "..", "..", "bin", "git_commit_bpmn_models_repo")
        shell_command = [
            shell_command_path,
            repo_path_to_use,
            message,
            branch_name_to_use,
        ]
        return cls.run_shell_command_to_get_stdout(shell_command)

    @classmethod
    def check_for_basic_configs(cls, raise_on_missing: bool = True) -> bool:
        if current_app.config["SPIFFWORKFLOW_BACKEND_GIT_SOURCE_BRANCH"] is None:
            if raise_on_missing:
                raise MissingGitConfigsError(
                    "Missing config for SPIFFWORKFLOW_BACKEND_GIT_SOURCE_BRANCH. "
                    "This is required for publishing process models"
                )
            return False
        return True

    @classmethod
    def check_for_publish_configs(cls, raise_on_missing: bool = True) -> bool:
        if not cls.check_for_basic_configs(raise_on_missing=raise_on_missing):
            return False
        if current_app.config["SPIFFWORKFLOW_BACKEND_GIT_PUBLISH_TARGET_BRANCH"] is None:
            if raise_on_missing:
                raise MissingGitConfigsError(
                    "Missing config for SPIFFWORKFLOW_BACKEND_GIT_PUBLISH_TARGET_BRANCH. "
                    "This is required for publishing process models"
                )
            return False
        if current_app.config["SPIFFWORKFLOW_BACKEND_GIT_PUBLISH_CLONE_URL"] is None:
            if raise_on_missing:
                raise MissingGitConfigsError(
                    "Missing config for SPIFFWORKFLOW_BACKEND_GIT_PUBLISH_CLONE_URL."
                    " This is required for publishing process models"
                )
            return False
        return True

    @classmethod
    def run_shell_command_as_boolean(cls, command: list[str]) -> bool:
        # we know result will be a bool here
        result: bool = cls.run_shell_command(command, return_success_state=True)  # type: ignore
        return result

    @classmethod
    def run_shell_command_to_get_stdout(cls, command: list[str]) -> str:
        # we know result will be a CompletedProcess here
        result: subprocess.CompletedProcess[bytes] = cls.run_shell_command(
            command, return_success_state=False
        )  # type: ignore
        return result.stdout.decode("utf-8").strip()

    @classmethod
    def run_shell_command(
        cls, command: list[str], return_success_state: bool = False
    ) -> subprocess.CompletedProcess[bytes] | bool:
        my_env = os.environ.copy()
        my_env["GIT_COMMITTER_NAME"] = current_app.config.get("SPIFFWORKFLOW_BACKEND_GIT_USERNAME") or "unknown"

        my_env["GIT_COMMITTER_EMAIL"] = (
            current_app.config.get("SPIFFWORKFLOW_BACKEND_GIT_USER_EMAIL") or "unknown@example.org"
        )

        # SSH authentication can be also provided via gitconfig.
        ssh_key_path = current_app.config.get("SPIFFWORKFLOW_BACKEND_GIT_SSH_PRIVATE_KEY_PATH")
        if ssh_key_path is not None:
            my_env["GIT_SSH_COMMAND"] = (
                "ssh -F /dev/null -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %s" % ssh_key_path
            )

        # this is fine since we pass the commands directly
        result = subprocess.run(command, check=False, capture_output=True, env=my_env)  # noqa

        if return_success_state:
            return result.returncode == 0

        if result.returncode != 0:
            stdout = result.stdout.decode("utf-8")
            stderr = result.stderr.decode("utf-8")
            raise GitCommandError(f"Failed to execute git command: {command}Stdout: {stdout}Stderr: {stderr}")

        return result

    # only supports github right now
    @classmethod
    def handle_web_hook(cls, webhook: dict) -> bool:
        cls.check_for_publish_configs()
        if "repository" not in webhook or "clone_url" not in webhook["repository"]:
            raise InvalidGitWebhookBodyError(
                f"Cannot find required keys of 'repository:clone_url' from webhook body: {webhook}"
            )
        repo = webhook["repository"]
        valid_clone_urls = [repo["clone_url"], repo["git_url"], repo["ssh_url"]]
        bpmn_spec_absolute_dir = current_app.config["SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR"]
        with FileSystemService.cd(bpmn_spec_absolute_dir):
            config_clone_url = cls.run_shell_command_to_get_stdout(["git", "config", "--get", "remote.origin.url"])
        if config_clone_url not in valid_clone_urls:
            raise GitCloneUrlMismatchError(
                f"Configured clone url does not match the repo URLs from webhook: {config_clone_url} =/="
                f" {valid_clone_urls}"
            )

        # Test webhook requests have a zen koan and hook info.
        if "zen" in webhook or "hook_id" in webhook:
            return False

        if "ref" not in webhook:
            raise InvalidGitWebhookBodyError(f"Could not find the 'ref' arg in the webhook boy: {webhook}")

        if current_app.config["SPIFFWORKFLOW_BACKEND_GIT_SOURCE_BRANCH"] is None:
            raise MissingGitConfigsError(
                "Missing config for SPIFFWORKFLOW_BACKEND_GIT_SOURCE_BRANCH. This is"
                " required for updating the repository as a result of the webhook"
            )

        ref = webhook["ref"]
        git_branch = current_app.config["SPIFFWORKFLOW_BACKEND_GIT_SOURCE_BRANCH"]
        if ref != f"refs/heads/{git_branch}":
            return False

        with FileSystemService.cd(current_app.config["SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR"]):
            cls.run_shell_command(["git", "pull", "--rebase"])
        DataSetupService.save_all_process_models()
        return True

    @classmethod
    def publish(cls, process_model_id: str, branch_to_update: str) -> str:
        cls.check_for_publish_configs()
        source_process_model_root = FileSystemService.root_path()
        source_process_model_path = os.path.join(source_process_model_root, process_model_id)
        unique_hex = uuid.uuid4().hex
        clone_dir = f"sample-process-models.{unique_hex}"

        # clone new instance of sample-process-models, checkout branch_to_update
        # we are adding a guid to this so the flake8 issue has been mitigated
        destination_process_root = f"/tmp/{clone_dir}"  # noqa

        git_clone_url = current_app.config["SPIFFWORKFLOW_BACKEND_GIT_PUBLISH_CLONE_URL"]
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
            destination_process_model_path = os.path.join(destination_process_root, process_model_id)
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
            git_remote = cls.run_shell_command_to_get_stdout(["git", "config", "--get", "remote.origin.url"])
            git_remote = re.sub(pattern=r"^git@([^:]+):", repl="https://\\1/", string=git_remote)

            remote_url = git_remote.strip().replace(".git", "")
            pr_url = f"{remote_url}/compare/{branch_to_update}...{branch_to_pull_request}?expand=1"

        # try to clean up
        if os.path.exists(destination_process_root):
            shutil.rmtree(destination_process_root)

        return pr_url
