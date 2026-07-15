"""CRUD + authorization contract tests for /api/courses/:id.

These demonstrate the framework generalizing across the full lifecycle using the
typed `courses_api` client and the `course_factory` (which handles creation and
cleanup), so each test contains only its unique assertion.
"""

import uuid

import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]


def test_get_course_by_id(courses_api, course_factory):
    """GET /api/courses/:id returns the created course with its fields."""
    course = course_factory(title=f"Get-By-Id {uuid.uuid4().hex[:8]}")

    response = courses_api.get_course(course["id"])
    assert response.status == 200
    body = response.json()
    assert body["id"] == course["id"]
    assert body["title"] == course["title"]
    assert "user" in body  # nested author association


def test_get_missing_course_returns_404(courses_api):
    """GET /api/courses/:id for a non-existent id returns 404."""
    response = courses_api.get_course(99999999)
    assert response.status == 404


def test_update_course(courses_api, course_factory):
    """PUT /api/courses/:id updates an owned course (204) and persists."""
    course = course_factory()
    new_title = f"Updated {uuid.uuid4().hex[:8]}"

    update = courses_api.update_course(
        course["id"],
        {"title": new_title, "description": "Updated by the CRUD test."},
    )
    assert update.status == 204

    # Verify the change persisted.
    fetched = courses_api.get_course(course["id"])
    assert fetched.status == 200
    assert fetched.json()["title"] == new_title


def test_update_course_validation_error(courses_api, course_factory):
    """PUT with a missing required field returns 400."""
    course = course_factory()
    response = courses_api.update_course(course["id"], {"title": "No description"})
    assert response.status == 400


def test_delete_course(courses_api, course_factory):
    """DELETE /api/courses/:id removes an owned course (204), then 404."""
    course = course_factory()

    deleted = courses_api.delete_course(course["id"])
    assert deleted.status == 204

    # It is now gone.
    assert courses_api.get_course(course["id"]).status == 404


def test_cannot_modify_another_users_course(courses_api, other_courses_api):
    """A user cannot update or delete a course owned by someone else (403)."""
    # A different user (the 'other' seeded account) owns this course.
    created = other_courses_api.create_course({
        "title": f"Other User's Course - {uuid.uuid4().hex[:8]}",
        "description": "Owned by a different user.",
    })
    assert created.status == 201
    course_id = created.json()["courseId"]

    try:
        forbidden_update = courses_api.update_course(
            course_id, {"title": "Hijacked", "description": "Should not be allowed."}
        )
        assert forbidden_update.status == 403

        forbidden_delete = courses_api.delete_course(course_id)
        assert forbidden_delete.status == 403
    finally:
        # Clean up as the actual owner (our client would get a 403).
        other_courses_api.delete_course(course_id)
