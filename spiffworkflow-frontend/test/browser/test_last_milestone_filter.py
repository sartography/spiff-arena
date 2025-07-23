from playwright.sync_api import expect, BrowserContext, Page

from helpers.login import login
from helpers.playwright_setup import browser_context  # Import the fixture


def test_last_milestone_filter(browser_context: BrowserContext):
    """Test the last milestone filter functionality in process instances."""
    page = browser_context.new_page()
    login(page, "admin", "admin")
    
    # Navigate to the process instances page
    page.goto("http://localhost:7001/process-instances/all")
    
    # Take screenshot of initial state before opening filters
    page.screenshot(path="debug_screenshots/milestone-filter-before.png")
    
    # Open the advanced options modal
    page.get_by_test_id("advanced-options-filters").click()
    
    # Verify the last milestone dropdown is present
    expect(page.get_by_label("Last milestone")).to_be_visible()
    
    # Take screenshot of advanced options modal
    page.screenshot(path="debug_screenshots/milestone-filter-modal-open.png")
    
    # Select a milestone value from the dropdown
    page.get_by_label("Last milestone").click()
    # Select the first available milestone option
    page.locator("li[role='option']").first.click()
    
    # Take screenshot after selection
    page.screenshot(path="debug_screenshots/milestone-filter-selected.png")
    
    # Close the advanced options modal
    page.get_by_role("button", name="Close").click()
    
    # Verify the filter is applied - we should see the milestone tag in the UI
    # This assumes the milestone filter displays a tag with the selected milestone value
    milestone_filter_tag = page.get_by_test_id("filter-tag-last_milestone_bpmn_name")
    expect(milestone_filter_tag).to_be_visible()
    
    # Take screenshot of filtered results
    page.screenshot(path="debug_screenshots/milestone-filter-applied.png")
    
    # Verify the process instances are filtered - check that all visible process instances
    # have the selected milestone value
    # This assumes that the milestone value is displayed in each process instance row
    milestone_cells = page.get_by_test_id("process-instance-show-link-last_milestone_bpmn_name").all()
    selected_milestone = milestone_filter_tag.text_content().split('=')[1]
    
    for cell in milestone_cells:
        # Check that each cell's content contains the selected milestone
        expect(cell).to_contain_text(selected_milestone)