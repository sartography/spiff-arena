from playwright.sync_api import Page, expect


def switch_to_card_view(page: Page) -> None:
    card_view_button = page.get_by_role("button", name="Card view")
    expect(card_view_button).to_be_visible(timeout=10000)
    card_view_button.click()
