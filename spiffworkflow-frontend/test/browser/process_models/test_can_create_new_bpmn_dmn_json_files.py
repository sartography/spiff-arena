import uuid
from playwright.sync_api import expect, Page

from helpers.login import login, logout, BASE_URL
from helpers.process_model import delete_process_model_and_verify_removal


def test_can_create_new_bpmn_dmn_json_files(page: Page):
    """
    Test that a user can create new BPMN, DMN, and JSON files in a process model via direct URLs,
    verifies they appear in the Files tab listing, and deletes the model.
    """
    # 1. Log in
    login(page)

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
    expect(
        page.get_by_text(f"Process Model: {display_name}"), "Model detail page load"
    ).to_be_visible(timeout=10000)

    # 3. Create BPMN, DMN, JSON files via direct URLs
    file_types = [
        # (URL segment, query, prefix, file_extension)
        ("files", "?file_type=bpmn", "process", "bpmn"),
        ("files", "?file_type=dmn", "decision", "dmn"),
        ("form", "?file_ext=json", "data", "json"),
    ]

    for segment, query, prefix, ext in file_types:
        file_name = f"{prefix}_{unique}"
        # Navigate directly to the new file editor URL
        page.goto(f"{BASE_URL}/process-models/{group_path}:{model_id}/{segment}{query}")
        test_element = page.get_by_test_id("process-model-file-show")
        expect(test_element).to_be_visible(timeout=10000)

        # Perform minimal edit to enable Save button
        if ext == "bpmn":
            page.locator("g[data-element-id=StartEvent_1]").click()
            page.locator(
                '.bio-properties-panel-group-header-title:has-text("General")'
            ).click()
            page.locator("#bio-properties-panel-name").fill("Start Event Name")
        elif ext == "dmn":
            page.locator("g[data-element-id^=decision_]").click()
            page.locator("text=General").click()
            page.locator("#bio-properties-panel-id").fill(file_name)
        else:
            # JSON: type content into the code editor
            editor = page.locator(".view-line").first
            editor.click()
            editor.type('{"test_key": "test_value"}')

        # Allow state update
        page.wait_for_timeout(500)

        # Click Save button to open filename input
        save_btn_id = (
            "process-model-file-save-button"
            if ext in ("bpmn", "dmn")
            else "file-save-button"
        )
        save_btn = page.get_by_test_id(save_btn_id)
        expect(save_btn, f"Save button visible for {ext}").to_be_visible(timeout=10000)
        expect(save_btn, f"Save button enabled for {ext}").to_be_enabled(timeout=10000)
        save_btn.click()

        # Fill in file name input using role= textbox labeled 'File Name'
        if ext == "json":
            name_input = page.get_by_test_id("process-model-file-name-field").locator(
                "input"
            )
        else:
            name_input = page.get_by_role("textbox", name="File Name")
        expect(name_input, "Filename input visible").to_be_visible(timeout=10000)
        name_input.fill(file_name)

        # Confirm Save Changes
        page.get_by_role("button", name="Save Changes").click()
        test_element = page.get_by_test_id("process-model-file-show")
        expect(test_element).to_be_visible(timeout=10000)
        expect(test_element).to_have_attribute("data-filename", f"{file_name}.{ext}")

        # Return to model detail via breadcrumb link
        page.get_by_test_id("process-model-breadcrumb-link").click()
        expect(
            page.get_by_text(f"Process Model: {display_name}"), "Return to model detail"
        ).to_be_visible(timeout=10000)

    # 4. Verify files listed under Files tab
    page.get_by_test_id("process-model-files").click()
    for (
        prefix,
        ext,
    ) in [(t[2], t[3]) for t in file_types]:
        testid = f"edit-file-{prefix}_{unique}-{ext}"
        expect(page.get_by_test_id(testid), f"File {testid} listed").to_be_visible(
            timeout=10000
        )

    # 5. Delete the process model
    delete_process_model_and_verify_removal(page, group_path, model_id, display_name)

    # 6. Log out
    logout(page)
