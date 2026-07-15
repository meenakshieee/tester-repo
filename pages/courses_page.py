import re
from playwright.sync_api import Page, expect

from config import settings

class CoursesPage:
    def __init__(self, page: Page):
        self.page = page
        self.base_url = settings.base_url
        self.dashboard_url = f"{self.base_url}/"
        self.create_url = f"{self.base_url}/courses/create"

        # Dashboard locators
        self.new_course_link = page.locator(".course--add--module")
        self.course_titles = page.locator(".course--title")

        # Create-course form locators
        self.title_input = page.locator("#courseTitle")
        self.description_input = page.locator("#courseDescription")
        self.estimated_time_input = page.locator("#estimatedTime")
        self.materials_input = page.locator("#materialsNeeded")
        self.submit_button = page.locator("button[type='submit']")
        self.validation_errors = page.locator(".validation--errors")

        # Detail-page locator
        self.detail_title = page.locator("h4.course--name")

    def navigate_to_dashboard(self):
        """Navigate to the dashboard.

        Uses a full page load. The dashboard `/` is a public route, so this is
        fine for *viewing* courses even though it drops the in-memory auth
        session. Do not rely on staying authenticated after calling this.
        """
        self.page.goto(self.dashboard_url)
        expect(self.new_course_link).to_be_visible()

    def navigate_to_create(self):
        """Click 'New Course' to open the creation form."""
        self.new_course_link.click()
        expect(self.title_input).to_be_visible()

    def create_course(self, title: str, description: str, estimated_time: str = "", materials_needed: str = ""):
        """Fill and submit the course creation form."""
        self.title_input.fill(title)
        self.description_input.fill(description)
        if estimated_time:
            self.estimated_time_input.fill(estimated_time)
        if materials_needed:
            self.materials_input.fill(materials_needed)
        self.submit_button.click()

    def expect_on_detail_page(self, title: str):
        """Assert the app navigated to the course detail page with the expected title."""
        expect(self.page).to_have_url(re.compile(rf"{re.escape(self.base_url)}/courses/\d+$"))
        expect(self.detail_title).to_have_text(title)

    def get_current_course_id(self) -> int:
        """Extract the course id from the current detail-page URL (`/courses/:id`)."""
        match = re.search(r"/courses/(\d+)", self.page.url)
        assert match, f"Expected a course detail URL, got: {self.page.url}"
        return int(match.group(1))

    def expect_course_in_list(self, title: str):
        """Assert a course appears in the dashboard list."""
        self.navigate_to_dashboard()
        expect(self.course_titles.filter(has_text=title)).to_have_count(1)

    def expect_validation_errors(self):
        """Assert that validation errors are displayed."""
        expect(self.validation_errors).to_be_visible()
