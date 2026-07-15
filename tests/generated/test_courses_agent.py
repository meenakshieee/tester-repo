import pytest
import uuid

def test_agent_happy_path_create_course(api_client, auth_headers):
    """
    Implements: Case 1 (Successful Course Creation) from agent/generated/create_course.md
    
    Verifies that POSTing a valid JSON payload to /api/courses with proper
    Authorization returns a 201 Created status and a JSON body containing a courseId.
    """
    unique_title = f"Agent Generated Course - {uuid.uuid4().hex[:8]}"
    
    # 1. Prepare JSON Payload grounded in agent plan
    payload = {
        "title": unique_title,
        "description": "This test case was outlined by the AI agent and implemented for closed-loop execution.",
        "estimatedTime": "3 hours",
        "materialsNeeded": "Markdown editor"
    }

    # 2. Execute Request
    response = api_client.post(
        "/api/courses",
        data=payload,
        headers=auth_headers
    )

    # 3. Assertions grounded in agent plan
    assert response.status == 201
    body = response.json()
    assert "courseId" in body
    assert isinstance(body["courseId"], int)

def test_agent_validation_failure_missing_title(api_client, auth_headers):
    """
    Implements: Case 2 (Create Course Missing Required Field: Title) from agent/generated/create_course.md
    
    Verifies that POSTing a payload without a title to /api/courses returns a 400 Bad Request
    and the error message 'Missing required fields'.
    """
    # 1. Prepare payload missing required field 'title'
    payload = {
        "description": "A course without a title."
    }

    # 2. Execute Request
    response = api_client.post(
        "/api/courses",
        data=payload,
        headers=auth_headers
    )

    # 3. Assertions grounded in agent plan
    assert response.status == 400
    body = response.json()
    assert body["message"] == "Missing required fields"
