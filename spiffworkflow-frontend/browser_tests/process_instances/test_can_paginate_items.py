import pytest
import re
from playwright.sync_api import expect
from helpers.login import login, logout
from helpers.debug import print_page_details
from helpers.playwright_setup import browser_context

# Final fallback attacker: Try each process group, click all links and all model-guess buttons, and if no model page loads, fail loudly with debug info.
def goto_any_model_start_process(page):
    page.goto("http://localhost:7001/process-groups")
    page.wait_for_timeout(900)
    print_page_details(page)
    all_buttons = page.query_selector_all('button')
    group_buttons = [btn for btn in all_buttons if 'Models:' in (btn.text_content() or '') and 'Groups:' in (btn.text_content() or '') and btn.is_visible() and btn.is_enabled()]
    if not group_buttons:
        print_page_details(page)
        pytest.fail("No process group with models!")
    found = False
    for group_btn in group_buttons:
        try:
            group_btn.click()
        except Exception:
            continue
        page.wait_for_timeout(700)
        print_page_details(page)
        # Try all links (true models)
        anchors = page.query_selector_all("a[href*='/process-models/']")
        for link in anchors:
            txt = link.text_content() or ''
            if link.is_visible() and '/new' not in (link.get_attribute('href') or ''):
                try:
                    link.click()
                except Exception:
                    continue
                page.wait_for_timeout(800)
                # If a start button, use it
                start_btn = page.query_selector('[data-testid=start-process-instance]')
                marker = page.query_selector('[data-testid=process-model-show-permissions-loaded]')
                if start_btn and start_btn.is_enabled() and marker and page.locator('[data-testid=process-model-show-permissions-loaded]').is_visible():
                    found = True
                    break
                else:
                    # Try alternative: any button with text that seems like a model (not the above group button)
                    local_btns = page.query_selector_all('button')
                    for modbtn in local_btns:
                        t = modbtn.text_content() or ''
                        if modbtn != group_btn and 'Models:' not in t and 'Groups:' not in t and len(t) > 4 and modbtn.is_enabled() and modbtn.is_visible():
                            try:
                                modbtn.click()
                            except Exception:
                                continue
                            page.wait_for_timeout(600)
                            s_btn = page.query_selector('[data-testid=start-process-instance]')
                            mker = page.query_selector('[data-testid=process-model-show-permissions-loaded]')
                            if s_btn and s_btn.is_enabled() and mker and page.locator('[data-testid=process-model-show-permissions-loaded]').is_visible():
                                found = True
                                break
                        if found:
                            break
            if found:
                break
        if found:
            break
    if not found:
        print_page_details(page)
        pytest.fail("Tried all fallback routes. No process model with start-process-instance!")

def run_primary_bpmn_file(page):
    btn = page.query_selector('[data-testid=start-process-instance]')
    if not btn or not btn.is_enabled():
        print_page_details(page)
        pytest.fail("Start process instance button not found or not enabled!")
    btn.click()
    expect(page).to_have_url(lambda url: "/process-instances" in url)
    expect(page.locator('text=Process Instance Id')).to_be_visible(timeout=13000)
    expect(page.locator('text=complete')).to_be_visible(timeout=13000)
    # Back to model
    bcrumb = page.query_selector('[data-testid=process-model-breadcrumb-link]')
    if not bcrumb or not bcrumb.is_enabled():
        print_page_details(page)
        pytest.fail("Model breadcrumb link not found!")
    bcrumb.click()
    expect(page.locator('[data-testid=process-model-show-permissions-loaded]')).to_be_visible(timeout=13000)

def test_can_paginate_items(browser_context):
    page = browser_context.new_page()
    login(page, "admin", "admin")
    goto_any_model_start_process(page)
    for _ in range(5):
        run_primary_bpmn_file(page)
    instance_link = page.query_selector('[data-testid=process-instance-list-link]')
    if not instance_link:
        print_page_details(page)
        pytest.fail("Process instance list link not found!")
    instance_link.click()
    expect(page).to_have_url(re.compile(r'/process-instances(/all)?'))
    paginator = page.query_selector('[data-testid=pagination-options]')
    if not paginator or not paginator.is_visible():
        print_page_details(page)
        pytest.fail("Paginator not found or not visible!")
    paginator.scroll_into_view_if_needed()
    select = paginator.query_selector('.cds--select__item-count .cds--select-input')
    if select:
        select.select_option('2')
    expect(page.get_by_text(re.compile(r'1[–-]2 of \\d+'))).to_be_visible(timeout=10000)
    first_row = page.query_selector('[data-testid=paginated-entity-id]')
    if not first_row or not first_row.is_visible():
        print_page_details(page)
        pytest.fail("First row entity not found")
    old_id = first_row.text_content().strip()
    fwd = paginator.query_selector('.cds--pagination__button--forward')
    if fwd and fwd.is_enabled():
        fwd.click()
        assert not page.locator('[data-testid=paginated-entity-id]', has_text=old_id).is_visible(), "Old id still visible after fwd"
        expect(page.get_by_text(re.compile(r'3[–-]4 of \\d+'))).to_be_visible(timeout=10000)
        back = paginator.query_selector('.cds--pagination__button--backward')
        if back and back.is_enabled():
            back.click()
            expect(page.get_by_text(re.compile(r'1[–-]2 of \\d+'))).to_be_visible(timeout=10000)
            assert page.locator('[data-testid=paginated-entity-id]', has_text=old_id).is_visible(), "Old id not restored after back"
    logout(page)
    page.close()
