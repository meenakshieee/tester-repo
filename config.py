"""Single source of truth for framework configuration.

Every URL and credential the tests use is resolved here, from environment
variables, with sensible local-development defaults. Nothing is hardcoded in the
test or fixture modules -- override any value via the environment or a local
`.env` file (loaded by python-dotenv) without touching code.

Example:
    BASE_URL=https://staging.example.com \\
    TEST_USER_EMAIL=qa@example.com \\
    TEST_USER_PASSWORD=... \\
    pytest
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load a local .env (if present) before reading any variable, so overrides apply
# to the whole test run. Safe to call at import time; python-dotenv is idempotent.
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Immutable, environment-driven configuration for the test suite."""

    # Application endpoints
    base_url: str = os.getenv("BASE_URL", "http://localhost:5173").rstrip("/")
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:5000").rstrip("/")

    # Seeded test user (override in CI/staging; defaults match the app's seed data)
    test_user_email: str = os.getenv("TEST_USER_EMAIL", "joe@smith.com")
    test_user_password: str = os.getenv("TEST_USER_PASSWORD", "joepassword")

    # A second seeded user, used only for cross-user authorization tests (403s).
    other_user_email: str = os.getenv("OTHER_USER_EMAIL", "sally@jones.com")
    other_user_password: str = os.getenv("OTHER_USER_PASSWORD", "sallypassword")

    @staticmethod
    def _basic_header(email: str, password: str) -> str:
        raw = f"{email}:{password}".encode("utf-8")
        return "Basic " + base64.b64encode(raw).decode("ascii")

    @property
    def basic_auth_header(self) -> str:
        """HTTP Basic ``Authorization`` header value for the primary user."""
        return self._basic_header(self.test_user_email, self.test_user_password)

    @property
    def other_basic_auth_header(self) -> str:
        """HTTP Basic ``Authorization`` header value for the secondary user."""
        return self._basic_header(self.other_user_email, self.other_user_password)


# A single shared instance imported everywhere config is needed.
settings = Settings()
