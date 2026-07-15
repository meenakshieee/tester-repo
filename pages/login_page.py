from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class LoginPage(BasePage):
    """Page Object for the sign-in screen (`/signin`)."""

    PATH = "/signin"

    def __init__(self, page: Page):
        super().__init__(page)

        # Locators
        self.email_input = page.locator("#emailAddress")
        self.password_input = page.locator("#password")
        self.submit_button = page.locator("button[type='submit']")
        self.validation_errors = page.locator(".validation--errors")
        self.sign_out_link = page.get_by_role("link", name="Sign Out")

    def _verify_loaded(self) -> None:
        expect(self.email_input).to_be_visible()

    def navigate(self) -> "LoginPage":
        """Open the sign-in page (alias for the inherited `open`)."""
        return self.open()

    def login(self, email: str, password: str) -> None:
        """Fill credentials and submit the sign-in form."""
        self.email_input.fill(email)
        self.password_input.fill(password)
        self.submit_button.click()

    def expect_signed_in(self) -> None:
        """Assert the app reflects an authenticated session."""
        expect(self.page).to_have_url(f"{self.base_url}/")
        expect(self.sign_out_link).to_be_visible()
