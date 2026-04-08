#!/usr/bin/env python3
"""
Rewrite manual public API v1 URL construction to use build_public_api_v1_url().

Usage:
    uv run python bin/codemod/rewrite_public_api_v1_url_helper.py
"""

import logging
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


REPLACEMENTS: dict[Path, list[tuple[str, str]]] = {
    Path("src/spiffworkflow_backend/routes/service_tasks_controller.py"): [
        (
            "from spiffworkflow_backend.exceptions.api_error import ApiError\n",
            "from spiffworkflow_backend.exceptions.api_error import ApiError\n"
            "from spiffworkflow_backend.helpers.public_api_urls import build_public_api_v1_url\n",
        ),
        (
            '    api_path_prefix = current_app.config["SPIFFWORKFLOW_BACKEND_API_PATH_PREFIX"]\n'
            "    response_json = {\n"
            '        "results": available_authentications,\n'
            '        "resultsV2": available_v2_authentications,\n'
            '        "connector_proxy_base_url": current_app.config["SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL"],\n'
            '        "redirect_url": f"{current_app.config[\'SPIFFWORKFLOW_BACKEND_URL\']}'
            '{api_path_prefix}/authentication_callback",\n'
            "    }\n",
            "    response_json = {\n"
            '        "results": available_authentications,\n'
            '        "resultsV2": available_v2_authentications,\n'
            '        "connector_proxy_base_url": current_app.config["SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL"],\n'
            '        "redirect_url": build_public_api_v1_url(\n'
            '            current_app.config["SPIFFWORKFLOW_BACKEND_URL"], "authentication_callback"\n'
            "        ),\n"
            "    }\n",
        ),
        (
            '    api_path_prefix = current_app.config["SPIFFWORKFLOW_BACKEND_API_PATH_PREFIX"]\n'
            "    callback = f\"{current_app.config['SPIFFWORKFLOW_BACKEND_URL']}"
            '{api_path_prefix}/authentication_callback/{service}/oauth"\n',
            "    callback = build_public_api_v1_url(\n"
            '        current_app.config["SPIFFWORKFLOW_BACKEND_URL"], f"authentication_callback/{service}/oauth"\n'
            "    )\n",
        ),
    ],
    Path("src/spiffworkflow_backend/services/authentication_service.py"): [
        (
            "from spiffworkflow_backend.exceptions.api_error import ApiError\n",
            "from spiffworkflow_backend.exceptions.api_error import ApiError\n"
            "from spiffworkflow_backend.helpers.public_api_urls import build_public_api_v1_url\n",
        ),
        (
            '            redirect_url = f"{self.get_backend_url()}'
            "{current_app.config['SPIFFWORKFLOW_BACKEND_API_PATH_PREFIX']}/logout_return\"\n",
            '            redirect_url = build_public_api_v1_url(self.get_backend_url(), "logout_return")\n',
        ),
    ],
    Path("src/spiffworkflow_backend/services/service_task_delegate.py"): [
        (
            "from spiffworkflow_backend.config import CONNECTOR_PROXY_COMMAND_TIMEOUT\n",
            "from spiffworkflow_backend.config import CONNECTOR_PROXY_COMMAND_TIMEOUT\n"
            "from spiffworkflow_backend.helpers.public_api_urls import build_public_api_v1_url\n",
        ),
        (
            '                api_path_prefix = current_app.config["SPIFFWORKFLOW_BACKEND_API_PATH_PREFIX"]\n'
            '                params["spiff__callback_url"] = (\n'
            "                    f\"{current_app.config['SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND']}"
            '{api_path_prefix}/tasks/{process_instance_id}/{spiff_task.id}/callback"\n'
            "                )\n",
            '                params["spiff__callback_url"] = build_public_api_v1_url(\n'
            '                    current_app.config["SPIFFWORKFLOW_BACKEND_URL"],\n'
            '                    f"tasks/{process_instance_id}/{spiff_task.id}/callback",\n'
            "                )\n",
        ),
    ],
    Path("src/spiffworkflow_backend/scripts/markdown_file_download_link.py"): [
        (
            "from spiffworkflow_backend.helpers.api_version import build_api_url\n",
            "from spiffworkflow_backend.helpers.public_api_urls import build_public_api_v1_url\n",
        ),
        (
            '        api_path_prefix = current_app.config["SPIFFWORKFLOW_BACKEND_API_PATH_PREFIX"]\n'
            '        endpoint = f"process-data-file-download/{modified_process_model_identifier}/'
            '{process_instance_id}/{digest}"\n'
            "\n"
            "        url = build_api_url(backend_url, api_path_prefix, endpoint)\n",
            '        endpoint = f"process-data-file-download/{modified_process_model_identifier}/'
            '{process_instance_id}/{digest}"\n'
            "\n"
            "        url = build_public_api_v1_url(backend_url, endpoint)\n",
        ),
    ],
}


def get_git_tracked_files(repo_root: Path) -> set[Path]:
    git_executable = shutil.which("git")
    if git_executable is None:
        logger.warning("Git executable not found. Aborting for safety.")
        return set()

    try:
        result = subprocess.run(  # noqa: S603
            [git_executable, "ls-files"],
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_root,
        )
    except subprocess.CalledProcessError:
        logger.warning("Failed to get git tracked files. Is this a git repository?")
        return set()

    return {repo_root / path for path in result.stdout.strip().split("\n") if path}


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    repo_root = Path(__file__).resolve().parents[2]
    git_tracked_files = get_git_tracked_files(repo_root)
    if not git_tracked_files:
        logger.error("No git tracked files found. Aborting for safety.")
        return 2

    modified_files = 0

    for relative_path, replacements in REPLACEMENTS.items():
        file_path = repo_root / relative_path
        if file_path not in git_tracked_files:
            logger.error("Refusing to edit untracked file: %s", relative_path)
            return 2

        src = file_path.read_text(encoding="utf-8")
        updated = src

        for old, new in replacements:
            if old in updated:
                updated = updated.replace(old, new, 1)
            elif new in updated:
                continue
            else:
                logger.error("Expected snippet not found in %s", relative_path)
                return 1

        if updated != src:
            file_path.write_text(updated, encoding="utf-8")
            modified_files += 1
            logger.info("Modified: %s", relative_path)

    logger.info("Updated %d file(s).", modified_files)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
