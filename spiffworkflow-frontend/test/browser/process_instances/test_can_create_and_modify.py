import re
from playwright.sync_api import expect, Page

from helpers.login import login, logout, BASE_URL


def update_dmn_text(page, old_text, new_text, element_id="wonderful_process"):
    page.locator(f"g[data-element-id='{element_id}']").click()
    page.locator(".dmn-icon-decision-table").click()
    test_element = page.get_by_test_id("process-model-file-show")
    expect(test_element).to_be_visible(timeout=10000)
    item = page.get_by_text(old_text)
    item.click()
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")
    page.keyboard.type(f'"{new_text}"')
    page.wait_for_timeout(500)
    page.get_by_test_id("process-model-file-save-button").click()


def update_bpmn_python_script(page, python_script, element_id="process_script"):
    page.locator(f"g[data-element-id='{element_id}']").click()
    # Click on the Script tab in properties panel
    page.locator(".bio-properties-panel-group-header-title").filter(
        has_text="Script"
    ).click()
    textarea = page.locator('textarea[name="pythonScript_bpmn:script"]')
    textarea.fill(python_script)
    page.wait_for_timeout(500)
    page.get_by_test_id("process-model-file-save-button").click()


def test_can_create_and_modify(page: Page):
    """
    Test that a user can create a new process instance, modify DMN and BPMN files, and restore originals.
    """

    # 1. Log in
    login(page)

    # 2. Navigate to the process model show page
    page.goto(f"{BASE_URL}/process-groups")
    page.get_by_text("Shared Resources", exact=False).first.click()
    expect(
        page.get_by_test_id("process-group-breadcrumb-Shared Resources")
    ).to_be_visible()
    page.get_by_text("Acceptance Tests Group One", exact=False).first.click()
    expect(
        page.get_by_test_id("process-group-breadcrumb-Acceptance Tests Group One")
    ).to_be_visible()
    model_name = "Acceptance Tests Model 1"
    page.get_by_test_id(f"process-model-card-{model_name}").first.click()
    expect(
        page.get_by_text(f"Process Model: {model_name}", exact=False)
    ).to_be_visible()
    model_url = page.url

    # Test constants
    original_dmn_output = "Very wonderful"
    new_dmn_output = "The new wonderful"
    original_python_script = 'person = "Kevin"'
    new_python_script = 'person = "Dan"'
    dmn_file = "awesome_decision.dmn"
    bpmn_file = "process_model_one.bpmn"

    # 3. Initial state validation: original DMN output should not exist
    expect(page.get_by_text(original_dmn_output)).to_have_count(0)

    # 4. Run initial BPMN file
    start_btn = page.get_by_test_id("start-process-instance").first
    expect(start_btn).to_be_enabled(timeout=10000)
    start_btn.click()
    page.wait_for_url(re.compile(r"/process-instances"), timeout=10000)
    # Return to model page
    page.goto(model_url)
    page.wait_for_url(model_url, timeout=10000)

    # 5. Modify DMN file and run
    page.get_by_test_id("process-model-files").click()
    page.get_by_test_id(f"edit-file-{dmn_file.replace('.', '-')}").click()
    update_dmn_text(page, original_dmn_output, new_dmn_output)
    # Return and run
    page.get_by_text(model_name, exact=False).click()
    page.wait_for_url(model_url, timeout=10000)
    start_btn = page.get_by_test_id("start-process-instance").first
    expect(start_btn).to_be_enabled(timeout=10000)
    start_btn.click()
    page.wait_for_url(re.compile(r"/process-instances"), timeout=10000)
    page.goto(model_url)
    page.wait_for_url(model_url, timeout=10000)

    # 6. Restore DMN file and run
    page.get_by_test_id("process-model-files").click()
    page.get_by_test_id(f"edit-file-{dmn_file.replace('.', '-')}").click()
    update_dmn_text(page, new_dmn_output, original_dmn_output)
    page.get_by_text(model_name, exact=False).click()
    page.wait_for_url(model_url, timeout=10000)
    start_btn = page.get_by_test_id("start-process-instance").first
    expect(start_btn).to_be_enabled(timeout=10000)
    start_btn.click()
    page.wait_for_url(re.compile(r"/process-instances"), timeout=10000)
    page.goto(model_url)
    page.wait_for_url(model_url, timeout=10000)

    # 7. Modify BPMN Python script and run
    page.get_by_test_id("process-model-files").click()
    page.get_by_test_id(f"edit-file-{bpmn_file.replace('.', '-')}").click()
    test_element = page.get_by_test_id("process-model-file-show")
    expect(test_element).to_be_visible(timeout=10000)
    expect(test_element).to_have_attribute("data-filename", bpmn_file)
    update_bpmn_python_script(page, new_python_script)
    page.get_by_text(model_name, exact=False).click()
    page.wait_for_url(model_url, timeout=10000)
    start_btn = page.get_by_test_id("start-process-instance").first
    expect(start_btn).to_be_enabled(timeout=10000)
    start_btn.click()
    page.wait_for_url(re.compile(r"/process-instances"), timeout=10000)
    page.goto(model_url)
    page.wait_for_url(model_url, timeout=10000)

    # 8. Restore BPMN Python script and run
    page.get_by_test_id("process-model-files").click()
    page.get_by_test_id(f"edit-file-{bpmn_file.replace('.', '-')}").click()
    update_bpmn_python_script(page, original_python_script)
    page.get_by_text(model_name, exact=False).click()
    page.wait_for_url(model_url, timeout=10000)
    start_btn = page.get_by_test_id("start-process-instance").first
    expect(start_btn).to_be_enabled(timeout=10000)
    start_btn.click()
    page.wait_for_url(re.compile(r"/process-instances"), timeout=10000)

    # Cleanup: logout
    logout(page)
