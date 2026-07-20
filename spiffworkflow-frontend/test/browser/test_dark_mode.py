from playwright.sync_api import Page, expect

from helpers.login import login


def test_dark_mode_uses_dark_background_and_light_text(page: Page) -> None:
    login(page)

    theme_container = page.locator("#container-for-extensions-container")
    expect(theme_container).to_have_attribute("data-theme", "light")

    page.get_by_role("button", name="Toggle dark mode").click()

    expect(theme_container).to_have_attribute("data-theme", "dark")
    expect(theme_container).to_have_css("background-color", "rgb(18, 18, 18)")
    expect(page.locator("h1").first).to_have_css("color", "rgb(245, 245, 245)")
