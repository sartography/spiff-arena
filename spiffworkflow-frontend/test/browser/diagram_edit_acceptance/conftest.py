import os
from pathlib import Path

import pytest
from playwright.sync_api import Browser

from helpers.login import login, BASE_URL


def _get_username() -> str:
    return os.getenv("BROWSER_TEST_USERNAME", "nelson")


def _get_password() -> str:
    return os.getenv("BROWSER_TEST_PASSWORD", "nelson")


@pytest.fixture(scope="session")
def storage_state_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("auth") / "storage_state.json"


@pytest.fixture(scope="session", autouse=True)
def authenticate(browser: Browser, storage_state_path: Path) -> Path:
    context = browser.new_context()
    page = context.new_page()
    login(page, username=_get_username(), password=_get_password(), base_url=BASE_URL)
    context.storage_state(path=storage_state_path)
    context.close()
    return storage_state_path


@pytest.fixture
def browser_context_args(storage_state_path: Path) -> dict:
    return {"storage_state": storage_state_path}
