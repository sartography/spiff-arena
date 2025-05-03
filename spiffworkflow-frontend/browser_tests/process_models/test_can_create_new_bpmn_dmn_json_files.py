import uuid
import re
from playwright.sync_api import expect, BrowserContext

from helpers.login import login, logout, BASE_URL
from helpers.playwright_setup import browser_context  # fixture


def test_can_create_new_bpmn_dmn_json_files(browser_context: BrowserContext):
    """
    Test that a user can create new BPMN, DMN, and JSON files in a process model via direct URLs,
    verifies they appear in the Files tab listing, and deletes the model.
    """
    page = browser_context.new_page()
    # 1. Log in
    login(page, "admin", "admin")

    # 2. Create a new process model
    group_id = "misc/acceptance-tests-group-one"
    group_path = group_id.replace("/", ":")
    page.goto(f"{BASE_URL}/process-groups/{group_path}")
    page.get_by_test_id("add-process-model-button").click()
    unique = uuid.uuid4().hex[:8]
    model_id = f"bpmn-dmn-json-model-{unique}"
    display_name = f"BPMN/DMN/JSON Test Model {unique}"
    page.fill('input[name="display_name"]', display_name)
    page.fill('input[name="id"]', model_id)
    page.get_by_role("button", name="Submit").click()
    expect(page.get_by_text(f"Process Model: {display_name}"), "Model detail page load").to_be_visible(timeout=10000)

    # 3. Create BPMN, DMN, JSON files via direct URLs
    file_types = [
        # (URL segment, query, prefix, file_extension)
        ("files", "?file_type=bpmn", "process", "bpmn"),
        ("files", "?file_type=dmn",  "decision", "dmn"),
        ("form",  "?file_ext=json", "data",    "json"),
    ]

    for segment, query, prefix, ext in file_types:
        file_name = f"{prefix}_{unique}"
        # Navigate directly to the new file editor URL
        page.goto(f"{BASE_URL}/process-models/{group_path}:{model_id}/{segment}{query}")
        expect(page.get_by_text("Process Model File"), f"Editor loaded for {ext}").to_be_visible(timeout=10000)

        # Perform minimal edit to enable Save button
        if ext == "bpmn":
            page.locator('g[data-element-id=StartEvent_1]').click()
            page.locator('.bio-properties-panel-group-header-title[title=General]').click()
            page.locator('#bio-properties-panel-name').fill('Start Event Name')
        elif ext == "dmn":
            page.locator('g[data-element-id^=decision_]').click()
            page.locator('text=General').click()
            page.locator('#bio-properties-panel-id').fill(file_name)
        else:
            # JSON: type content into the code editor
            editor = page.locator('.view-line').first
            editor.click()
            editor.type('{"test_key": "test_value"}')

        # Allow state update
        page.wait_for_timeout(500)

        # Click Save button to open filename input
        save_btn_id = "process-model-file-save-button" if ext in ("bpmn", "dmn") else "file-save-button"
        save_btn = page.get_by_test_id(save_btn_id)
        expect(save_btn, f"Save button visible for {ext}").to_be_visible(timeout=10000)
        expect(save_btn, f"Save button enabled for {ext}").to_be_enabled(timeout=10000)
        save_btn.click()

        # Fill in file name input using role= textbox labeled 'File Name'
        name_input = page.get_by_role("textbox", name=re.compile(r"File Name"))
        expect(name_input, "Filename input visible").to_be_visible(timeout=10000)
        name_input.fill(file_name)

        # Confirm Save Changes
        page.get_by_role("button", name="Save Changes").click()
        expect(page.get_by_text(f"Process Model File: {file_name}"), f"File detail shown for {file_name}").to_be_visible(timeout=10000)

        # Return to model detail via breadcrumb link
        page.get_by_test_id("process-model-breadcrumb-link").click()
        expect(page.get_by_text(f"Process Model: {display_name}"), "Return to model detail").to_be_visible(timeout=10000)

    # 4. Verify files listed under Files tab
    page.get_by_test_id("process-model-files").click()
    for prefix, ext, in [(t[2], t[3]) for t in file_types]:
        testid = f"edit-file-{prefix}_{unique}-{ext}"
        expect(page.get_by_test_id(testid), f"File {testid} listed").to_be_visible(timeout=10000)

    # 5. Delete the process model
    page.get_by_test_id("delete-process-model-button").click()
    expect(page.get_by_text("Are you sure"), "Delete confirmation visible").to_be_visible(timeout=10000)
    page.get_by_role("button", name="Delete").click()
    expect(page, "Returned to group page after delete").to_have_url(re.compile(rf".*/process-groups/{re.escape(group_path)}$"), timeout=10000)
    expect(page.get_by_text(model_id), "Model id removed").to_have_count(0)
    expect(page.get_by_text(display_name), "Model name removed").to_have_count(0)

    # 6. Log out
    logout(page)
