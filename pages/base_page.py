"""Base class for all Page Objects.

Centralizes the driver handle, base URL resolution, and navigation so concrete
pages declare only their own locators and intent. A new page becomes a short
subclass: set ``PATH``, define locators, and (optionally) override
``_verify_loaded`` to assert its ready state.
"""

from __future__ import annotations

from playwright.sync_api import Page, Locator, expect

from config import settings


class BasePage:
    # Route for this page relative to the app base URL. "" == the app root.
    PATH: str = ""

    def __init__(self, page: Page):
        self.page = page
        self.base_url = settings.base_url

    @property
    def url(self) -> str:
        """Absolute URL for this page (base URL + PATH)."""
        return f"{self.base_url}{self.PATH}"

    def open(self) -> "BasePage":
        """Navigate to this page and wait until it reports ready. Chainable."""
        self.page.goto(self.url)
        self._verify_loaded()
        return self

    def _verify_loaded(self) -> None:
        """Hook: subclasses override to assert the page finished loading."""
        # Default: nothing to assert.

    # -- Shared, auto-waiting interaction helpers ---------------------------- #
    def expect_visible(self, locator: Locator) -> None:
        expect(locator).to_be_visible()
