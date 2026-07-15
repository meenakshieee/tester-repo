import pytest
import uuid
from pages.login_page import LoginPage
from pages.courses_page import CoursesPage

# Test Credentials (seeded by default in the app)
EMAIL = "joe@smith.com"
PASSWORD = "joepassword"


def test_e2e_create_course_success(page):
    """Happy Path: User logs in, creates a course, and verifies it appears on the dashboard.

    This test uses Page Objects exclusively to avoid brittle hardcoded URLs and
    text-based assertions.
    """
    login_page = LoginPage(page)
    courses_page = CoursesPage(page)

    # 1. Sign In
    login_page.navigate()
    login_page.login(EMAIL, PASSWORD)
    login_page.expect_signed_in()

    # 2. Navigate to Create Form & Submit
    unique_title = f"E2E Test Course - {uuid.uuid4().hex[:8]}"
    courses_page.navigate_to_create()
    courses_page.create_course(
        title=unique_title,
        description="A hands-on E2E UI test course.",
        estimated_time="5 hours",
        materials_needed="Wood, saw, nails"
    )

    # 3. Verify redirect to detail page with correct title
    courses_page.expect_on_detail_page(unique_title)

    # 4. Navigate back to dashboard and verify course is listed
    courses_page.expect_course_in_list(unique_title)


def test_e2e_create_course_validation_failure(page):
    """Validation Failure: Submitting an empty form displays error messages.

    Verifies that the frontend validation catches missing required fields.
    """
    login_page = LoginPage(page)
    courses_page = CoursesPage(page)

    # 1. Sign In
    login_page.navigate()
    login_page.login(EMAIL, PASSWORD)
    login_page.expect_signed_in()

    # 2. Navigate to Create Course Form
    courses_page.navigate_to_create()

    # 3. Submit empty form
    courses_page.create_course(title="", description="")

    # 4. Verify validation error messages are displayed
    courses_page.expect_validation_errors()
    error_texts = courses_page.validation_errors.locator("li").all_text_contents()
    assert "Please provide a value for Title" in error_texts
    assert "Please provide a value for Description" in error_texts
