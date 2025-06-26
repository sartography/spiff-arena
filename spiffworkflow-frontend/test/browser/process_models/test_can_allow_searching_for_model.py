import re
import pytest
from playwright.sync_api import expect, BrowserContext

from helpers.login import login, logout, BASE_URL
from helpers.playwright_setup import browser_context  # fixture


def test_can_allow_searching_for_model(browser_context: BrowserContext):
    """
    Test that a user can search for a process model by typing part of the model id
    and select and view the searched model.
    """
    page = browser_context.new_page()

    # 1. Log in
    login(page, "admin", "admin")

    # 2. Navigate to the Acceptance Tests Group One page
    group_id = "misc/acceptance-tests-group-one"
    group_path = group_id.replace("/", ":")  # misc:acceptance-tests-group-one
    # Go to the group page
    page.goto(f"{BASE_URL}/process-groups/{group_path}")

    # Confirm group page loaded
    expect(
        page.get_by_test_id("process-group-breadcrumb-Acceptance Tests Group One")
    ).to_be_visible(timeout=10000)

    # 3. Expand the Process Models section
    process_models_btn = page.get_by_role("button", name=re.compile(r"^Process Models"))
    expect(process_models_btn).to_be_visible(timeout=10000)
    process_models_btn.click()

    # 4. Search for 'model-3'
    search_input = page.get_by_placeholder("Search")
    expect(search_input).to_be_visible(timeout=10000)
    search_input.fill("model-3")

    # 5. Select the found model by clicking its card
    model_display_name = "Acceptance Tests Model 3"
    card_test_id = f"process-model-card-{model_display_name}"
    model_card = page.get_by_test_id(card_test_id)
    expect(model_card).to_be_visible(timeout=10000)
    model_card.click()

    # 6. Verify the model detail page shows the selected model
    # URL should end with /process-models/{group_path}:acceptance-tests-model-3
    expected_url_pattern = fr".*?/process-models/{re.escape(group_path)}:acceptance-tests-model-3$"
    expect(page).to_have_url(re.compile(expected_url_pattern), timeout=10000)

    # Verify the heading shows the correct model display name
    heading = page.get_by_role("heading", name=f"Process Model: {model_display_name}")
    expect(heading).to_be_visible(timeout=10000)

    # 7. Logout
    logout(page)
