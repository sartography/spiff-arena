import os
import re
from pathlib import Path
from typing import Any, Mapping

import pytest
from playwright.sync_api import Browser, Page, expect

from diagram_edit_acceptance.config import CONFIG


def _locator(page: Page, spec: Any):
    if isinstance(spec, Mapping):
        if "role" in spec:
            return page.get_by_role(
                spec["role"],
                name=spec.get("name"),
                exact=spec.get("exact", False),
            )
        if "text" in spec:
            return page.get_by_text(spec["text"])
        if "css" in spec:
            return page.locator(spec["css"])
    return page.locator(spec)


def _get_username() -> str:
    login = CONFIG.get("login", {})
    return os.getenv(login.get("username_env", ""), login.get("username_default", ""))


def _get_password() -> str:
    login = CONFIG.get("login", {})
    return os.getenv(login.get("password_env", ""), login.get("password_default", ""))


def login(page: Page, username: str | None = None, password: str | None = None) -> None:
    login_config = CONFIG["login"]
    username = username or _get_username()
    password = password or _get_password()

    page.goto(login_config["url"])
    _locator(page, login_config["username"]).fill(username)
    _locator(page, login_config["password"]).fill(password)
    _locator(page, login_config["submit"]).click()
    post_login_url = login_config.get("post_login_url")
    if post_login_url:
        page.wait_for_url(post_login_url, timeout=20000)

    dialog = page.get_by_role("dialog")
    if dialog.count() > 0:
        close_button = dialog.get_by_role(
            "button",
            name=re.compile(r"(continue|close|dismiss|ok|got it|start)", re.I),
        )
        if close_button.count() > 0:
            close_button.first.click()
        else:
            dialog.get_by_role("button").first.click()

    page.goto(CONFIG["diagram"]["url"])


@pytest.fixture(scope="session")
def storage_state_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("auth") / "storage_state.json"


@pytest.fixture(scope="session", autouse=True)
def authenticate(browser: Browser, storage_state_path: Path) -> Path:
    context = browser.new_context()
    page = context.new_page()
    login(page, username=_get_username(), password=_get_password())
    context.storage_state(path=storage_state_path)
    context.close()
    return storage_state_path


@pytest.fixture
def browser_context_args(storage_state_path: Path) -> dict:
    return {"storage_state": storage_state_path}
