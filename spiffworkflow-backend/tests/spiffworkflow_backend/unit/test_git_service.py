"""Process Model."""

import sys
from types import SimpleNamespace
from unittest.mock import call

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired
    from typing_extensions import TypedDict
else:
    from typing import NotRequired
    from typing import TypedDict

from flask.app import Flask
from flask.testing import FlaskClient
from pytest_mock import MockerFixture

from spiffworkflow_backend.services.git_service import GitService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class WebhookRepository(TypedDict):
    clone_url: str
    git_url: str
    ssh_url: str


class GitWebhook(TypedDict):
    repository: WebhookRepository
    ref: str
    after: str
    zen: NotRequired[str]
    hook_id: NotRequired[int]


class TestGitService(BaseTest):
    @staticmethod
    def _build_webhook(
        branch_name: str = "sandbox",
        after_revision: str = "2222222222222222222222222222222222222222",
    ) -> GitWebhook:
        return {
            "repository": {
                "clone_url": "https://gitlab.example.com/org/repo.git",
                "git_url": "",
                "ssh_url": "git@gitlab.example.com:org/repo.git",
            },
            "ref": f"refs/heads/{branch_name}",
            "after": after_revision,
        }

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

    def test_current_revision_uses_short_ttl_cache(
        self,
        app: Flask,
        mocker: MockerFixture,
    ) -> None:
        GitService.clear_current_revision_cache()
        mock_run = mocker.patch.object(GitService, "run_shell_command_to_get_stdout", return_value="abc1234")

        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_GIT_CURRENT_REVISION_CACHE_TTL_SECONDS", 30):
            assert GitService.get_current_revision() == "abc1234"
            assert GitService.get_current_revision() == "abc1234"

        repo_path = app.config["SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR"]
        mock_run.assert_called_once_with(["rev-parse", "--short", "HEAD"], context_directory=repo_path)
        GitService.clear_current_revision_cache()

    def test_current_revision_cache_can_be_disabled(
        self,
        app: Flask,
        mocker: MockerFixture,
    ) -> None:
        GitService.clear_current_revision_cache()
        mock_run = mocker.patch.object(
            GitService,
            "run_shell_command_to_get_stdout",
            side_effect=["abc1234", "def5678"],
        )

        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_GIT_CURRENT_REVISION_CACHE_TTL_SECONDS", 0):
            assert GitService.get_current_revision() == "abc1234"
            assert GitService.get_current_revision() == "def5678"

        assert mock_run.call_count == 2
        GitService.clear_current_revision_cache()

    def test_commit_on_save_commits_when_enabled(
        self,
        app: Flask,
        mocker: MockerFixture,
    ) -> None:
        mock_commit = mocker.patch.object(GitService, "commit", return_value="commit output")

        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_GIT_COMMIT_ON_SAVE", True):
            GitService.commit_on_save("User: test commit")

        mock_commit.assert_called_once_with(message="User: test commit")

    def test_commit_on_save_skips_commit_when_disabled(
        self,
        app: Flask,
        mocker: MockerFixture,
    ) -> None:
        mock_commit = mocker.patch.object(GitService, "commit")

        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_GIT_COMMIT_ON_SAVE", False):
            GitService.commit_on_save("User: test commit")

        mock_commit.assert_not_called()

    def test_force_sync_to_webhook_revision_stashes_and_backs_up_local_state(
        self,
        app: Flask,
        client: FlaskClient,
        mocker: MockerFixture,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        webhook = self._build_webhook()
        current_revision = "1111111111111111111111111111111111111111"

        def stdout_side_effect(command: list[str], context_directory: str | None = None, prepend_with_git: bool = True) -> str:
            if command == ["config", "--get", "remote.origin.url"]:
                return webhook["repository"]["clone_url"]
            if command == ["status", "--porcelain"]:
                return " M pull-process-models-from-git.bpmn\n?? scratch.txt"
            raise AssertionError(f"Unexpected git stdout command: {command}")

        mocker.patch.object(GitService, "run_shell_command_to_get_stdout", side_effect=stdout_side_effect)
        mocker.patch.object(GitService, "get_current_revision", return_value=current_revision)
        mock_run_shell_command = mocker.patch.object(GitService, "run_shell_command")
        mocker.patch.object(GitService, "run_shell_command_as_boolean", return_value=False)
        mock_refresh = mocker.patch("spiffworkflow_backend.services.git_service.DataSetupService.refresh_process_model_caches")
        mocker.patch(
            "spiffworkflow_backend.services.git_service.uuid.uuid4", return_value=SimpleNamespace(hex="deadbeefcafebabe")
        )

        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_GIT_SOURCE_BRANCH", "sandbox"):
            result = GitService.force_sync_to_webhook_revision(webhook)

        repo_path = app.config["SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR"]
        assert result is True
        assert mock_run_shell_command.mock_calls == [
            call(["fetch", "origin", "sandbox"], context_directory=repo_path),
            call(
                ["stash", "push", "--include-untracked", "--message", "spiff-force-sync-stash-deadbeef"],
                context_directory=repo_path,
            ),
            call(
                ["branch", "spiff-force-sync-backup-111111111111-deadbeef", current_revision],
                context_directory=repo_path,
            ),
            call(["reset", "--hard", webhook["after"]], context_directory=repo_path),
            call(["clean", "-fd"], context_directory=repo_path),
        ]
        mock_refresh.assert_called_once_with()

    def test_force_sync_to_webhook_revision_resets_clean_checkout_without_backup(
        self,
        app: Flask,
        client: FlaskClient,
        mocker: MockerFixture,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        webhook = self._build_webhook()
        current_revision = "1111111111111111111111111111111111111111"

        def stdout_side_effect(command: list[str], context_directory: str | None = None, prepend_with_git: bool = True) -> str:
            if command == ["config", "--get", "remote.origin.url"]:
                return webhook["repository"]["clone_url"]
            if command == ["status", "--porcelain"]:
                return ""
            raise AssertionError(f"Unexpected git stdout command: {command}")

        mocker.patch.object(GitService, "run_shell_command_to_get_stdout", side_effect=stdout_side_effect)
        mocker.patch.object(GitService, "get_current_revision", return_value=current_revision)
        mock_run_shell_command = mocker.patch.object(GitService, "run_shell_command")
        mocker.patch.object(GitService, "run_shell_command_as_boolean", return_value=True)
        mock_refresh = mocker.patch("spiffworkflow_backend.services.git_service.DataSetupService.refresh_process_model_caches")

        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_GIT_SOURCE_BRANCH", "sandbox"):
            result = GitService.force_sync_to_webhook_revision(webhook)

        repo_path = app.config["SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR"]
        assert result is True
        assert mock_run_shell_command.mock_calls == [
            call(["fetch", "origin", "sandbox"], context_directory=repo_path),
            call(["reset", "--hard", webhook["after"]], context_directory=repo_path),
            call(["clean", "-fd"], context_directory=repo_path),
        ]
        mock_refresh.assert_called_once_with()

    def test_force_sync_to_webhook_revision_skips_when_repo_is_already_current_and_clean(
        self,
        app: Flask,
        client: FlaskClient,
        mocker: MockerFixture,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        webhook = self._build_webhook()

        def stdout_side_effect(command: list[str], context_directory: str | None = None, prepend_with_git: bool = True) -> str:
            if command == ["config", "--get", "remote.origin.url"]:
                return webhook["repository"]["clone_url"]
            if command == ["status", "--porcelain"]:
                return ""
            raise AssertionError(f"Unexpected git stdout command: {command}")

        mocker.patch.object(GitService, "run_shell_command_to_get_stdout", side_effect=stdout_side_effect)
        mocker.patch.object(GitService, "get_current_revision", return_value=webhook["after"])
        mock_run_shell_command = mocker.patch.object(GitService, "run_shell_command")
        mock_merge_base = mocker.patch.object(GitService, "run_shell_command_as_boolean")
        mock_refresh = mocker.patch("spiffworkflow_backend.services.git_service.DataSetupService.refresh_process_model_caches")

        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_GIT_SOURCE_BRANCH", "sandbox"):
            result = GitService.force_sync_to_webhook_revision(webhook)

        assert result is True
        mock_run_shell_command.assert_not_called()
        mock_merge_base.assert_not_called()
        mock_refresh.assert_not_called()

    def test_handle_web_hook_ignores_test_webhooks(
        self,
        app: Flask,
        mocker: MockerFixture,
    ) -> None:
        webhook = self._build_webhook()
        webhook["zen"] = "Keep it logically awesome."
        webhook["hook_id"] = 1

        mocker.patch.object(GitService, "run_shell_command_to_get_stdout", return_value=webhook["repository"]["clone_url"])
        mock_get_current_revision = mocker.patch.object(GitService, "get_current_revision")
        mock_run_shell_command = mocker.patch.object(GitService, "run_shell_command")
        mock_refresh = mocker.patch("spiffworkflow_backend.services.git_service.DataSetupService.refresh_process_model_caches")

        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_GIT_SOURCE_BRANCH", "sandbox"):
            result = GitService.handle_web_hook(webhook)

        assert result is False
        mock_get_current_revision.assert_not_called()
        mock_run_shell_command.assert_not_called()
        mock_refresh.assert_not_called()
