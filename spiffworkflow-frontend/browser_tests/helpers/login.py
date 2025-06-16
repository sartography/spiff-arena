from playwright.sync_api import Page, expect
import re
from helpers.debug import print_page_details # For diagnostics

BASE_URL = "http://localhost:7001"
LOGIN_PAGE_IDENTIFIER_TEXT = "This login form is for demonstration purposes only" # Used in logout verification

def login(page: Page, username: str, password: str, base_url: str = BASE_URL):
    print(f"Login: Navigating to base URL: {base_url}")
    page.goto(base_url, wait_until="networkidle") # Wait for network idle

    print("Login: Waiting for redirection to /auth/sign-in URL...")
    try:
        # Expect redirection to the sign-in page with a generous timeout
        expect(page).to_have_url(re.compile(r".*/auth/sign-in.*"), timeout=25000) # Increased timeout
        print(f"Login: Successfully on sign-in page URL: {page.url}")
    except Exception as e:
        print(f"Login: Failed to reach /auth/sign-in URL. Current URL: {page.url}")
        print("Login: Page details before raising error:")
        print_page_details(page) # Crucial diagnostic for this failure case
        raise  # Re-raise the exception to fail the test clearly

    # If on sign-in page, proceed with locating elements
    print("Login: Attempting to fill username...")
    username_field = page.locator("#username")
    expect(username_field).to_be_visible(timeout=15000) # Wait for element
    username_field.fill(username)
    print("Login: Username filled.")

    print("Login: Attempting to fill password...")
    password_field = page.locator("#password")
    expect(password_field).to_be_visible(timeout=10000)
    password_field.fill(password)
    print("Login: Password filled.")

    print("Login: Attempting to click login button...")
    login_button = page.locator("#spiff-login-button")
    expect(login_button).to_be_enabled(timeout=10000)
    login_button.click()
    print("Login: Login button clicked.")

    print("Login: Waiting for 'User Actions' button to confirm login...")
    expect(page.get_by_role("button", name="User Actions")).to_be_visible(timeout=15000)
    print("Login: Login successful, 'User Actions' button visible.")

def logout(page: Page, base_url: str = BASE_URL):
    print("Logout: Attempting to logout...")
    user_menu_button = page.get_by_role("button", name="User Actions")
    
    try:
        expect(user_menu_button).to_be_enabled(timeout=10000)
        print("Logout: 'User Actions' button found and enabled.")
        user_menu_button.click()
        
        sign_out_button = page.locator('[data-testid="sign-out-button"]')
        expect(sign_out_button).to_be_visible(timeout=5000)
        print("Logout: Sign-out button in dropdown visible.")
        sign_out_button.click()
        print("Logout: Clicked sign-out button from dropdown.")
    except Exception as e:
        print(f"Logout: Error during UI logout via User Actions button ({e}). Attempting direct navigation to signout URL.")
        page.goto(f"{base_url}/auth/signout", wait_until="networkidle")

    print("Logout: Verifying return to the login page.")
    # Expect to land on the sign-in page.
    expect(page).to_have_url(re.compile(r".*/auth/sign-in.*"), timeout=15000) # Increased timeout
    # Check for a reliable element on the sign-in page, like the login button.
    expect(page.locator("#spiff-login-button")).to_be_visible(timeout=10000)
    # Optionally, also check for the specific text if it's consistently present on logout
    # expect(page.get_by_text(LOGIN_PAGE_IDENTIFIER_TEXT, exact=True)).to_be_visible(timeout=10000)
    print("Logout: Successfully logged out and verified on sign-in page.")
