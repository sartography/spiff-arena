"""Exercise the real worker shell entrypoint without starting a broker or database."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3]


class TestWorkerStartup(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="worker-startup-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.backend = self.root / "backend"
        self.bin = self.backend / "bin"
        self.bin.mkdir(parents=True)
        for name in (
            "start_celery_worker",
            "prepare_worker_process_models",
            "clone_process_models",
            "wait_for_db_schema_migrations",
        ):
            shutil.copy2(BACKEND / "bin" / name, self.bin / name)
        self.models = self.root / "models"
        self.source = self.root / "source"
        self.source.mkdir()
        self._git("init", "-b", "fixture", cwd=self.source)
        (self.source / "model.txt").write_text("original", encoding="utf-8")
        self._git("add", "model.txt", cwd=self.source)
        self._git("commit", "-m", "Fixture model", cwd=self.source)
        self.log = self.root / "commands.log"
        self.mock_bin = self.root / "mock-bin"
        self.mock_bin.mkdir()
        self._executable(
            self.mock_bin / "uv",
            """#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "$TEST_COMMAND_LOG"
test -f "$SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR/model.txt"
case "$*" in
  'run flask db current'|'run flask db heads') echo fixture_revision ;;
  'run celery '*) exec "$TEST_WORKER_STUB" "$@" ;;
  *) exit 99 ;;
esac
""",
        )
        self.worker = self.backend / ".venv" / "bin" / "celery"
        self.worker.parent.mkdir(parents=True)
        self._executable(
            self.worker,
            """#!/usr/bin/env bash
set -euo pipefail
test "$SPIFFWORKFLOW_BACKEND_CELERY_ENABLED" = true
test "$SPIFFWORKFLOW_BACKEND_RUN_BACKGROUND_SCHEDULER_IN_CREATE_APP" = false
test "$SPIFFWORKFLOW_BACKEND_RUNNING_IN_CELERY_WORKER" = true
test "$(cat "$SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR/model.txt")" = "$TEST_EXPECTED_MODEL"
echo worker-started >> "$TEST_COMMAND_LOG"
""",
        )
        self.env = {key: value for key, value in os.environ.items() if not key.startswith(("SPIFFWORKFLOW_", "GIT_"))}
        self.env.update(
            PATH=str(self.mock_bin) + os.pathsep + os.environ["PATH"],
            SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR=str(self.models),
            SPIFFWORKFLOW_BACKEND_GIT_CLONE_PROCESS_MODELS="true",
            SPIFFWORKFLOW_BACKEND_GIT_PUBLISH_CLONE_URL=str(self.source),
            SPIFFWORKFLOW_BACKEND_GIT_SOURCE_BRANCH="fixture",
            TEST_COMMAND_LOG=str(self.log),
            TEST_WORKER_STUB=str(self.worker),
            TEST_EXPECTED_MODEL="original",
        )

    @staticmethod
    def _executable(path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)

    @staticmethod
    def _git(*arguments: str, cwd: Path) -> str:
        result = subprocess.run(  # noqa: S603
            ["git", "-c", "user.name=Startup Test", "-c", "user.email=startup@example.test", *arguments],  # noqa: S607
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip()

    def _start(self) -> subprocess.CompletedProcess[str]:
        self.log.unlink(missing_ok=True)
        return subprocess.run(  # noqa: S603
            ["bash", str(self.bin / "start_celery_worker")],  # noqa: S607
            cwd=self.backend,
            env=self.env,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def _assert_started(self) -> None:
        result = self._start()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("worker-started", self.log.read_text(encoding="utf-8"))

    def _assert_refused(self, message: str) -> None:
        result = self._start()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(message, result.stderr)
        self.assertFalse(self.log.exists(), "Application imports/worker execution occurred before model readiness")

    def test_clone_precedes_migration_queries_and_worker_in_both_exec_modes(self) -> None:
        for direct in ("false", "true"):
            with self.subTest(direct=direct):
                self.models = self.root / ("models-" + direct)
                self.env["SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR"] = str(self.models)
                self.env["SPIFFWORKFLOW_BACKEND_CELERY_WORKER_DIRECT_EXEC"] = direct
                self._assert_started()
                self.assertEqual(
                    self._git("rev-parse", "HEAD", cwd=self.models),
                    self._git("rev-parse", "HEAD", cwd=self.source),
                )

    def test_existing_checkout_and_local_changes_survive_restart_and_remote_advancement(self) -> None:
        self._assert_started()
        (self.models / "model.txt").write_text("unpublished", encoding="utf-8")
        self._git("add", "model.txt", cwd=self.models)
        self._git("commit", "-m", "Unpublished local model", cwd=self.models)
        original_head = self._git("rev-parse", "HEAD", cwd=self.models)
        (self.models / "model.txt").write_text("edited", encoding="utf-8")
        (self.models / "untracked.txt").write_text("keep", encoding="utf-8")
        (self.source / "model.txt").write_text("new remote version", encoding="utf-8")
        self._git("add", "model.txt", cwd=self.source)
        self._git("commit", "-m", "Remote advancement", cwd=self.source)
        self.env["TEST_EXPECTED_MODEL"] = "edited"
        del self.env["SPIFFWORKFLOW_BACKEND_GIT_PUBLISH_CLONE_URL"]
        del self.env["SPIFFWORKFLOW_BACKEND_GIT_SOURCE_BRANCH"]
        self._assert_started()
        self.assertEqual(self._git("rev-parse", "HEAD", cwd=self.models), original_head)
        self.assertEqual((self.models / "untracked.txt").read_text(encoding="utf-8"), "keep")

    def test_linked_git_worktree_is_preserved(self) -> None:
        self._git("worktree", "add", "--detach", str(self.models), cwd=self.source)
        self.assertTrue((self.models / ".git").is_file())
        self._assert_started()

    def test_mounted_nongit_models_work_with_clone_disabled(self) -> None:
        self.models.mkdir()
        (self.models / "model.txt").write_text("original", encoding="utf-8")
        self.env["SPIFFWORKFLOW_BACKEND_GIT_CLONE_PROCESS_MODELS"] = "false"
        del self.env["SPIFFWORKFLOW_BACKEND_GIT_PUBLISH_CLONE_URL"]
        self._assert_started()
        self.assertFalse((self.models / ".git").exists())

    def test_missing_mount_does_not_start_or_create_placeholder(self) -> None:
        self.env["SPIFFWORKFLOW_BACKEND_GIT_CLONE_PROCESS_MODELS"] = "false"
        self._assert_refused("process-model root is unavailable")
        self.assertFalse(self.models.exists())

    def test_missing_root_setting_is_actionable(self) -> None:
        del self.env["SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR"]
        self._assert_refused("SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR must be set")

    def test_root_file_is_preserved_and_refused(self) -> None:
        self.models.write_text("keep", encoding="utf-8")
        self._assert_refused("root is not a directory")
        self.assertEqual(self.models.read_text(encoding="utf-8"), "keep")

    def test_failed_clone_never_starts_worker(self) -> None:
        self.env["SPIFFWORKFLOW_BACKEND_GIT_PUBLISH_CLONE_URL"] = str(self.root / "nonexistent-source")
        self._assert_refused("does not exist")

    def test_nonempty_mount_including_lost_found_is_never_cleared(self) -> None:
        retained = self.models / "lost+found" / "retained.txt"
        retained.parent.mkdir(parents=True)
        retained.write_text("keep", encoding="utf-8")
        self._assert_refused("Refusing to clone over")
        self.assertEqual(retained.read_text(encoding="utf-8"), "keep")

    def test_incomplete_git_checkout_is_refused(self) -> None:
        self.models.mkdir()
        self._git("init", cwd=self.models)
        self._assert_refused("checkout has no readable HEAD")

    def test_unreadable_or_untraversable_mount_is_refused(self) -> None:
        if os.geteuid() == 0:
            self.skipTest("Root bypasses directory permission checks")
        self.models.mkdir()
        self.models.chmod(0o000)
        self.addCleanup(self.models.chmod, 0o700)
        self._assert_refused("cannot read or traverse")


if __name__ == "__main__":
    unittest.main()
