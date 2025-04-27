from playwright.sync_api import Page

def print_page_details(page: Page):
    """Prints details of elements with data-testid and interactable elements on the page."""
    
    page.wait_for_load_state() # Ensure page is loaded before querying elements

    print("\n--- Elements with data-testid ---")
    elements_with_testid = page.query_selector_all('[data-testid]')
    if not elements_with_testid:
        print("No elements with data-testid found.")
    else:
        for element in elements_with_testid:
            data_testid = element.get_attribute('data-testid')
            tag_name = element.evaluate('element => element.tagName.toLowerCase()')
            if data_testid:
                print(f"Element: <{tag_name}>, data-testid={data_testid}")

    print("\n--- Input and Button Elements ---")
    interactable_elements = page.query_selector_all('input, button, a[role="button"], select, textarea')
    if not interactable_elements:
        print("No interactable elements (inputs, buttons, etc.) found.")
    else:
        for element in interactable_elements:
            tag_name = element.evaluate('element => element.tagName.toLowerCase()')
            element_id = element.get_attribute('id')
            element_name = element.get_attribute('name')
            element_text = element.text_content().strip()
            
            # Attempt to find associated label text
            label_text = None
            if element_id:
                # Check for label with for="element_id"
                label = page.query_selector(f'label[for="{element_id}"]')
                if label:
                    label_text = label.text_content().strip()
            
            # If no label found via 'for', check if element is inside a label
            if not label_text:
                 label_text = element.evaluate('''
                    element => {
                        const parentLabel = element.closest('label');
                        return parentLabel ? parentLabel.textContent.trim() : null;
                    }
                ''')

            # Fallback to aria-label or button text
            if not label_text:
                 label_text = element.get_attribute('aria-label')
            if not label_text and tag_name == 'button' and element_text:
                 label_text = element_text
                 
            print(f"Element: <{tag_name}>", end="")
            if element_id: print(f", id='{element_id}'", end="")
            if element_name: print(f", name='{element_name}'", end="")
            if label_text: print(f", Label/Text='{label_text}'", end="")
            print() # Newline
