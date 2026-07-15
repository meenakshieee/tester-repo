import uuid

import pytest

# Applies the 'api' marker to every test in this module (enables `pytest -m api`).
pytestmark = pytest.mark.api


def test_get_courses(courses_api):
    """Public users can fetch the list of courses."""
    response = courses_api.list_courses()
    assert response.status == 200
    courses = response.json()
    assert isinstance(courses, list)
    assert len(courses) > 0
    for course in courses:
        assert "id" in course
        assert "title" in course
        assert "description" in course


def test_create_course_success(courses_api, created_courses):
    """An authenticated user can create a course (201 + courseId)."""
    unique_title = f"API Woodworking Course - {uuid.uuid4().hex[:8]}"
    response = courses_api.create_course({
        "title": unique_title,
        "description": "Learn to carve wooden joints with hand tools.",
        "estimatedTime": "10 hours",
        "materialsNeeded": "Chisel, mallet, oak wood block",
    })

    assert response.status == 201
    body = response.json()
    assert "courseId" in body
    assert isinstance(body["courseId"], int)

    created_courses.append(body["courseId"])  # cleanup on teardown


def test_create_course_missing_fields(courses_api):
    """Validation fails (400) when required fields are missing."""
    missing_title = courses_api.create_course({"description": "Missing title"})
    assert missing_title.status == 400
    assert missing_title.json()["message"] == "Missing required fields"

    missing_description = courses_api.create_course({"title": "Missing description"})
    assert missing_description.status == 400
    assert missing_description.json()["message"] == "Missing required fields"


def test_create_course_unauthorized(courses_api):
    """Unauthenticated users cannot create courses (401)."""
    response = courses_api.create_course(
        {"title": "Unauthorized Course", "description": "No auth header supplied."},
        authed=False,
    )
    assert response.status == 401
