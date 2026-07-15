# Create Course - Test Plan

## Endpoint Under Test

*   **Method:** `POST` (Line 79)
*   **Path:** `/api/courses` (Line 79)
*   **Auth Requirement:** Requires authentication via the `authenticateUser` middleware (Line 79). The exact authentication scheme and header format are not specified in the source.
*   **Required Request Fields:**
    *   `title` (Line 80)
    *   `description` (Line 80)
*   **Optional Request Fields:**
    *   `estimatedTime` (Not explicitly validated in `POST /api/courses`, but accepted via `...req.body` on Line 84 and defined as a course attribute on Line 51)
    *   `materialsNeeded` (Not explicitly validated in `POST /api/courses`, but accepted via `...req.body` on Line 84 and defined as a course attribute on Line 51)
*   **Success Status Code:** `201` (Line 89)
*   **Success Response Body:** (Line 89)
    ```json
    {
      "courseId": <course_id>
    }
    ```

---

## UI Test Cases (End-to-End)

*Note: The provided source code is a backend API file. Specific UI elements, page URLs, and client-side navigation flows are not specified in the source. The steps below are described conceptually based on the backend requirements.*

### Case 1: Happy Path - Create Course Successfully
1.  **Sign In:** Log into the application using valid user credentials (UI authentication mechanism is not specified in source).
2.  **Navigate to Create Form:** Open the "Create Course" form (UI path is not specified in source).
3.  **Fill Required Fields:** Enter a valid title (e.g., "Introduction to Testing") into the Title input field and a valid description (e.g., "Learn the fundamentals of QA.") into the Description input field.
4.  **Fill Optional Fields:** Enter "2 hours" into the Estimated Time input field and "A computer" into the Materials Needed input field.
5.  **Submit Form:** Click the submit button (UI element is not specified in source).
6.  **Expected Outcome:** The course is successfully created. The application handles the `201` status code and redirects the user or displays a success message (UI redirection/success behavior is not specified in source).

### Case 2: Validation Failure - Missing Required Fields
1.  **Sign In:** Log into the application using valid user credentials (UI authentication mechanism is not specified in source).
2.  **Navigate to Create Form:** Open the "Create Course" form (UI path is not specified in source).
3.  **Leave Required Fields Blank:** Leave the Title and Description input fields empty.
4.  **Submit Form:** Click the submit button.
5.  **Expected Outcome:** The submission fails. The UI displays an error message corresponding to the backend response `Missing required fields` (UI error display mechanism is not specified in source).

---

## API Test Cases

### Case 1: Successful Course Creation
*   **Method:** `POST`
*   **Path:** `/api/courses`
*   **Auth Header:** Format not specified in source (handled by `authenticateUser` middleware).
*   **Example JSON Payload:**
    ```json
    {
      "title": "Designing Test Plans",
      "description": "A comprehensive guide to writing test plans.",
      "estimatedTime": "3 hours",
      "materialsNeeded": "Markdown editor"
    }
    ```
*   **Expected Response:**
    *   **Status Code:** `201` (Line 89)
    *   **Body:** (Line 89)
        ```json
        {
          "courseId": 1
        }
        ```

### Case 2: Create Course Missing Required Field (Title)
*   **Method:** `POST`
*   **Path:** `/api/courses`
*   **Auth Header:** Format not specified in source (handled by `authenticateUser` middleware).
*   **Example JSON Payload:**
    ```json
    {
      "description": "A course without a title."
    }
    ```
*   **Expected Response:**
    *   **Status Code:** `400` (Line 81)
    *   **Body:** (Line 81)
        ```json
        {
          "message": "Missing required fields"
        }
        ```

### Case 3: Create Course Missing Required Field (Description)
*   **Method:** `POST`
*   **Path:** `/api/courses`
*   **Auth Header:** Format not specified in source (handled by `authenticateUser` middleware).
*   **Example JSON Payload:**
    ```json
    {
      "title": "A Course Without a Description"
    }
    ```
*   **Expected Response:**
    *   **Status Code:** `400` (Line 81)
    *   **Body:** (Line 81)
        ```json
        {
          "message": "Missing required fields"
        }
        ```

### Case 4: Unauthenticated Course Creation
*   **Method:** `POST`
*   **Path:** `/api/courses`
*   **Auth Header:** None (or invalid credentials).
*   **Example JSON Payload:**
    ```json
    {
      "title": "Unauthenticated Course",
      "description": "This request should fail authentication."
    }
    ```
*   **Expected Response:**
    *   **Status Code:** Not specified in source (handled by external `authenticateUser` middleware on Line 79).
    *   **Body:** Not specified in source (handled by external `authenticateUser` middleware on Line 79).

---

## Assertions Checklist

*   **Verify Success Status Code:** Assert that a successful `POST` request to `/api/courses` returns a `201` status code (Line 89).
*   **Verify Success Response Body Structure:** Assert that the response body for a successful creation contains exactly the `courseId` key (Line 89).
*   **Verify Success Response Body Data Type:** Assert that the returned `courseId` is an integer (Line 89).
*   **Verify Validation Failure Status Code:** Assert that sending a request missing `title` or `description` returns a `400` status code (Line 81).
*   **Verify Validation Failure Response Body:** Assert that the validation failure response body matches exactly `{ "message": "Missing required fields" }` (Line 81).
*   **Verify Database Association:** Assert that the newly created course record in the database is associated with the authenticated user's ID (`userId` matches `req.currentUser.id`) (Line 85).
