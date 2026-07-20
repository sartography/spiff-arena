from playwright.sync_api import Page, expect

from helpers.login import BASE_URL, login


def test_dark_mode_uses_dark_background_and_light_text(page: Page) -> None:
    login(page)

    theme_container = page.locator("#container-for-extensions-container")
    expect(theme_container).to_have_attribute("data-theme", "light")

    page.get_by_role("button", name="Toggle dark mode").click()

    expect(theme_container).to_have_attribute("data-theme", "dark")
    expect(theme_container).to_have_css("background-color", "rgb(18, 18, 18)")
    expect(page.locator("h1").first).to_have_css("color", "rgb(245, 245, 245)")

    page.goto(
        f"{BASE_URL}/process-models/"
        "misc:acceptance-tests-group-one:acceptance-tests-model-1/"
        "files/process_model_one.bpmn"
    )
    properties_panel = page.locator(".bio-properties-panel")
    expect(properties_panel).to_be_visible(timeout=10000)
    expect(properties_panel).to_have_css("color", "rgb(245, 245, 245)")
    expect(page.locator(".bio-properties-panel-group").first).to_have_css(
        "background-color", "rgb(18, 18, 18)"
    )

    page.locator("g[data-element-id=StartEvent_1]").click()
    page.locator(
        '.bio-properties-panel-group-header-title:has-text("General")'
    ).click()
    name_input = page.locator("#bio-properties-panel-name")
    expect(name_input).to_be_visible()
    expect(name_input).to_have_css("background-color", "rgb(43, 43, 43)")
