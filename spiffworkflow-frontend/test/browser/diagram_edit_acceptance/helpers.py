import os
import re

from playwright.sync_api import Page, expect

BASE_URL = os.getenv("E2E_URL", "http://localhost:7001")
MODEL_FILE_URL = (
    f"{BASE_URL}/process-models/"
    "system:diagram-edit-acceptance-test:test-a/files/test-a.bpmn"
)


def open_diagram(page: Page, element_id: str) -> None:
    page.set_viewport_size({"width": 1600, "height": 2000})
    page.goto(MODEL_FILE_URL)
    expect(
        page.get_by_text("Process Model File: test-a.bpmn"),
        "Diagram loaded",
    ).to_be_visible(timeout=20000)
    page.get_by_role("button", name="Fit to View").click()
    expect(
        page.locator(f'g[data-element-id="{element_id}"]'),
        "Element rendered",
    ).to_be_visible(timeout=20000)


def select_element(page: Page, element_id: str) -> None:
    target = page.locator(f'g[data-element-id="{element_id}"]')
    hit = page.locator(f'g[data-element-id="{element_id}"] .djs-hit')
    for _ in range(3):
        page.evaluate(
            """(id) => {
            const el = document.querySelector(`g[data-element-id="${id}"]`);
            if (el) el.scrollIntoView({ block: 'center', inline: 'center' });
          }""",
            element_id,
        )
        if hit.count() > 0:
            hit.first.click(force=True)
        else:
            target.click(force=True)
        if page.locator('input[name="id"]').input_value() == element_id:
            return
        page.wait_for_timeout(250)
        page.evaluate(
            """(id) => {
            const el = document.querySelector(`g[data-element-id="${id}"]`);
            if (!el) return false;
            ['mousedown','mouseup','click'].forEach((type) =>
              el.dispatchEvent(new MouseEvent(type, { bubbles: true }))
            );
            return true;
          }""",
            element_id,
        )
        if page.locator('input[name="id"]').input_value() == element_id:
            return
        page.wait_for_timeout(250)
    expect(
        page.locator('input[name="id"]'),
        "Properties panel updated for selected element",
    ).to_have_value(element_id, timeout=10000)


def expand_group_if_needed(group_locator) -> None:
    launch_button = group_locator.locator('button:has-text("Launch Editor")')
    if not launch_button.is_visible():
        header = group_locator.locator('.bio-properties-panel-group-header-title')
        if header.count() > 0:
            header.first.click(force=True)


def open_and_close_dialog(page: Page, heading_text: str) -> None:
    dialog = page.get_by_role("dialog")
    expect(
        dialog.get_by_role("heading", name=re.compile(heading_text, re.I)),
        "Dialog opened",
    ).to_be_visible(timeout=10000)
    dialog.get_by_role("button", name=re.compile(r"close", re.I)).click()
    expect(dialog, "Dialog closed").to_be_hidden(timeout=10000)
