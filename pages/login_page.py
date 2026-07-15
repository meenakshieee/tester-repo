from playwright.sync_api import Page, expect

from config import settings

class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.base_url = settings.base_url
        self.url = f"{self.base_url}/signin"

        # Locators
        self.email_input = page.locator("#emailAddress")
        self.password_input = page.locator("#password")
        self.submit_button = page.locator("button[type='submit']")
        self.validation_errors = page.locator(".validation--errors")
        self.sign_out_link = page.get_by_role("link", name="Sign Out")

    def navigate(self):
        """Navigates to the sign-in page."""
        self.page.goto(self.url)
        expect(self.email_input).to_be_visible()

    def login(self, email: str, password: str):
        """Performs a login attempt with the given credentials."""
        self.email_input.fill(email)
        self.password_input.fill(password)
        self.submit_button.click()

    def expect_signed_in(self):
        """Assert that the user is signed in (by checking for the Sign Out link)."""
        expect(self.page).to_have_url(f"{self.base_url}/")
        expect(self.sign_out_link).to_be_visible()
