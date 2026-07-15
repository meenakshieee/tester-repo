import pytest
from playwright.sync_api import APIRequestContext, Playwright

from config import settings


@pytest.fixture(scope="session")
def test_user() -> dict[str, str]:
    """The credentials for the seeded test user (env-overridable via config)."""
    return {
        "email": settings.test_user_email,
        "password": settings.test_user_password,
    }


@pytest.fixture(scope="session")
def auth_headers() -> dict[str, str]:
    """HTTP Basic Authorization header for the configured test user."""
    return {
        "Authorization": settings.basic_auth_header,
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="session")
def api_client(playwright: Playwright) -> APIRequestContext:
    """A Playwright API request context pointing to the backend API."""
    request_context = playwright.request.new_context(base_url=settings.api_base_url)
    yield request_context
    request_context.dispose()
