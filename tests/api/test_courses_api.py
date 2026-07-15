import pytest
import uuid

def test_get_courses(api_client):
    """Verifies that public users can fetch the list of courses."""
    response = api_client.get("/api/courses")
    assert response.status == 200
    courses = response.json()
    assert isinstance(courses, list)
    assert len(courses) > 0
    # Check that courses have the required fields
    for course in courses:
        assert "id" in course
        assert "title" in course
        assert "description" in course

def test_create_course_success(api_client, auth_headers):
    """Verifies that an authenticated user can successfully create a course."""
    unique_title = f"API Woodworking Course - {uuid.uuid4().hex[:8]}"
    course_data = {
        "title": unique_title,
        "description": "Learn to carve wooden joints with hand tools.",
        "estimatedTime": "10 hours",
        "materialsNeeded": "Chisel, mallet, oak wood block"
    }
    
    response = api_client.post(
        "/api/courses",
        data=course_data,
        headers=auth_headers
    )
    
    assert response.status == 201
    body = response.json()
    assert "courseId" in body
    assert isinstance(body["courseId"], int)

def test_create_course_missing_fields(api_client, auth_headers):
    """Verifies that validation fails if required fields are missing."""
    # Case A: Missing title
    response = api_client.post(
        "/api/courses",
        data={"description": "Missing title"},
        headers=auth_headers
    )
    assert response.status == 400
    assert response.json()["message"] == "Missing required fields"

    # Case B: Missing description
    response = api_client.post(
        "/api/courses",
        data={"title": "Missing description"},
        headers=auth_headers
    )
    assert response.status == 400
    assert response.json()["message"] == "Missing required fields"

def test_create_course_unauthorized(api_client):
    """Verifies that unauthenticated users cannot create courses."""
    response = api_client.post(
        "/api/courses",
        data={
            "title": "Unauthorized Course",
            "description": "This should fail because no auth headers are provided."
        }
    )
    assert response.status == 401
