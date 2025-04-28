from playwright.sync_api import Page, expect

# Default base URL, can be overridden if needed
BASE_URL = "http://localhost:7001"

def login(page: Page, username: str, password: str, base_url: str = BASE_URL):
    """Logs in a user via the standard login form."""
    page.goto(base_url)

    # Check if already on the sign-in page or need to navigate
    # Use a flexible check for the sign-in URL pattern
    if "/auth/sign-in" not in page.url:
        # If not on sign-in, assume redirection or direct access works.
        # If specific navigation is needed, add it here.
        # Example: page.click('text=Sign In') if needed.
        # If not on sign-in, assume redirection or direct access works.
        # Example: page.click('text=Sign In') if needed.
        pass # Assuming goto handles redirection if not logged in.

    # Use ID selectors based on the working test_login.py
    page.locator('#username').fill(username)
    page.locator('#password').fill(password)
    page.locator('#spiff-login-button').click()

    # Wait for navigation and check for an element indicating successful login.
    # The 'User Actions' button seems reliable based on previous context.
    expect(page.get_by_role('button', name='User Actions')).to_be_visible(timeout=10000)

def logout(page: Page, base_url: str = BASE_URL):
    """Logs out the current user."""
    # Attempt logout via UI first
    user_menu_button = page.get_by_role('button', name='User Actions')
    if user_menu_button.is_visible():
        user_menu_button.click()
        # Use a more specific selector for the logout button if needed
        logout_button = page.get_by_role('button', name='Logout')
        expect(logout_button).to_be_visible()
        logout_button.click()
    else:
        # Fallback: Navigate directly to the signout URL
        # Ensure the signout URL is correct for the application
        page.goto(f"{base_url}/auth/signout")

    # Verify logout by checking for the login button.
    expect(page.locator('#spiff-login-button')).to_be_visible(timeout=10000)
