import pytest
import base64
import os
from playwright.sync_api import APIRequestContext, Playwright

# Base URL definitions (Configurable via environment variables for enterprise deployment)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
UI_BASE_URL = os.getenv("BASE_URL", "http://localhost:5173")

# Mock User Credentials for Joe Smith (Seeded by default)
JOE_EMAIL = "joe@smith.com"
JOE_PASSWORD = "joepassword"

@pytest.fixture(scope="session")
def auth_headers():
    """Generates the Basic Authorization header for Joe Smith."""
    credentials = f"{JOE_EMAIL}:{JOE_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json"
    }

@pytest.fixture(scope="session")
def api_client(playwright: Playwright) -> APIRequestContext:
    """Provides a Playwright API request context pointing to the backend API."""
    request_context = playwright.request.new_context(base_url=API_BASE_URL)
    yield request_context
    request_context.dispose()
