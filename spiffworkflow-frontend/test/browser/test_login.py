import time
from playwright.sync_api import Page, expect

from helpers.login import login, logout


def test_login(page: Page) -> None:
    login(page, "admin", "admin")


def test_logout(page: Page) -> None:
    login(page, "admin", "admin")
    logout(page)
    expect(
        page.get_by_text("This login form is for demonstration purposes only")
    ).to_be_visible()
