"""Typed, auth-aware client for the Course Catalog REST API.

Tests call intent-revealing methods (`create_course`, `update_course`, ...)
instead of assembling raw URLs, headers, and payloads. Authentication is
attached automatically; pass ``authed=False`` for negative (401) tests.

This is the single place that knows the API's URL shape and auth scheme — if the
contract changes, this file changes, not the tests.
"""

from __future__ import annotations

from typing import Any

from playwright.sync_api import APIRequestContext, APIResponse


class CoursesApiClient:
    def __init__(self, request: APIRequestContext, auth_header: str | None = None):
        self._request = request
        self._auth_header = auth_header

    def _headers(self, authed: bool) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if authed and self._auth_header:
            headers["Authorization"] = self._auth_header
        return headers

    # -- Users -------------------------------------------------------------- #
    def get_current_user(self) -> APIResponse:
        """GET /api/users — the app's authenticated 'who am I' check."""
        return self._request.get("/api/users", headers=self._headers(True))

    # -- Courses ------------------------------------------------------------ #
    def list_courses(self) -> APIResponse:
        """GET /api/courses (public)."""
        return self._request.get("/api/courses", headers=self._headers(False))

    def get_course(self, course_id: int) -> APIResponse:
        """GET /api/courses/:id (public)."""
        return self._request.get(f"/api/courses/{course_id}", headers=self._headers(False))

    def create_course(self, payload: dict[str, Any], *, authed: bool = True) -> APIResponse:
        """POST /api/courses (auth required). ``authed=False`` for 401 tests."""
        return self._request.post("/api/courses", data=payload, headers=self._headers(authed))

    def update_course(self, course_id: int, payload: dict[str, Any]) -> APIResponse:
        """PUT /api/courses/:id (auth + ownership required)."""
        return self._request.put(f"/api/courses/{course_id}", data=payload, headers=self._headers(True))

    def delete_course(self, course_id: int) -> APIResponse:
        """DELETE /api/courses/:id (auth + ownership required)."""
        return self._request.delete(f"/api/courses/{course_id}", headers=self._headers(True))
