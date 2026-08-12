"""axe-core scans of representative pages, scoped to WCAG 2.1 A/AA (the
standard the Revised Section 508 regulations incorporate by reference).

These are not a full WCAG 2.1 AA conformance test -- axe-core's automated
rules only catch a subset of success criteria (it cannot judge things like
whether alt text is *meaningful*, or verify a logical reading/focus order).
They do give continuous, CI-enforced regression coverage for what axe-core
can check, across representative real pages -- including the canvas-rendered
BPMN editor, which eslint-plugin-jsx-a11y cannot see at all.

Full results for every scan (violations, passes, incomplete, inapplicable)
are written to test-results/axe/<name>.json regardless of pass/fail, and
that directory is uploaded as a CI artifact.
"""

from playwright.sync_api import Page, expect

from helpers.accessibility import assert_no_violations
from helpers.login import BASE_URL, login, logout
from helpers.process_groups import switch_to_card_view


def test_login_page_has_no_wcag_violations(page: Page) -> None:
    page.goto(BASE_URL)
    expect(page.locator("#spiff-login-button")).to_be_visible(timeout=10000)
    assert_no_violations(page, "login_page")


def test_process_groups_list_has_no_wcag_violations(page: Page) -> None:
    login(page)
    page.goto(f"{BASE_URL}/process-groups")
    switch_to_card_view(page)
    assert_no_violations(page, "process_groups_list")
    logout(page)


def test_process_model_show_has_no_wcag_violations(page: Page) -> None:
    login(page)
    page.goto(f"{BASE_URL}/process-groups")
    switch_to_card_view(page)
    page.get_by_text("Shared Resources", exact=False).first.click()
    page.get_by_text("Acceptance Tests Group One", exact=False).first.click()
    page.get_by_test_id("process-model-card-Acceptance Tests Model 1").first.click()
    expect(
        page.get_by_text("Process Model: Acceptance Tests Model 1", exact=False)
    ).to_be_visible(timeout=10000)
    assert_no_violations(page, "process_model_show")
    logout(page)


def test_bpmn_diagram_editor_has_no_wcag_violations(page: Page) -> None:
    """Covers the bpmn-js canvas editor, which renders via imperative
    SVG/canvas APIs and produces little lintable JSX -- eslint-plugin-jsx-a11y
    has near-zero visibility here, so this is the only automated a11y
    coverage this surface has."""
    login(page)
    page.goto(
        f"{BASE_URL}/process-models/"
        "misc:acceptance-tests-group-one:acceptance-tests-model-1/"
        "files/process_model_one.bpmn"
    )
    expect(page.locator(".bio-properties-panel")).to_be_visible(timeout=10000)
    assert_no_violations(page, "bpmn_diagram_editor")
    logout(page)


def test_process_instance_list_has_no_wcag_violations(page: Page) -> None:
    login(page)
    page.goto(f"{BASE_URL}/process-instances")
    assert_no_violations(page, "process_instance_list")
    logout(page)


def test_guest_task_form_has_no_wcag_violations(page: Page) -> None:
    """The public guest task form is reachable without authentication --
    exactly the kind of citizen-facing surface a VPAT/ACR needs to cover."""
    login(page)
    page.goto(f"{BASE_URL}/process-groups")
    switch_to_card_view(page)
    page.get_by_text("Shared Resources", exact=False).first.click()
    page.get_by_test_id("process-model-card-task-with-guest-form").first.click()
    start_button = page.get_by_test_id("start-process-instance").first
    expect(start_button).to_be_visible(timeout=10000)
    start_button.click()
    page.wait_for_timeout(1000)
    page.get_by_text("My process instances", exact=True).click()
    process_instance_link = page.locator(
        '[data-testid="process-instance-show-link-id"]'
    ).first
    expect(process_instance_link).to_be_visible(timeout=10000)
    process_instance_link.click()
    page.wait_for_url("**/process-instances/**", timeout=15000)
    metadata_link = page.locator('[data-testid="metadata-value-first_task_url"] a')
    expect(metadata_link).to_be_visible(timeout=10000)
    public_task_url = metadata_link.get_attribute("href")
    logout(page)

    assert public_task_url
    page.goto(public_task_url)
    assert_no_violations(page, "guest_task_form")