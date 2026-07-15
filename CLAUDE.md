# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Quick Commands

```bash
# Install dependencies (first time only)
pip install -r requirements.txt
python -m playwright install chromium

# Run all tests (requires backend + frontend running on :5000 & :5173)
pytest -v

# Run only API tests
pytest tests/api -v

# Run only E2E tests
pytest tests/e2e -v

# Run E2E with visible browser
pytest tests/e2e --headed

# Run a single test
pytest tests/e2e/test_courses_e2e.py::test_e2e_create_course_success

# Generate Markdown test plan with AI agent
export GEMINI_API_KEY="your_key"  # or ANTHROPIC_API_KEY, OPENAI_API_KEY
python agent/generate_tests.py [--model gemini-3.5-flash|claude-3-5-sonnet|gpt-4o]

# Start the backend (Express on :5000)
cd ../app/course-catalog-app/api && npm start

# Start the frontend (Vite on :5173)
cd ../app/course-catalog-app/client && npm run dev
```

---

## Architecture

### Core Pattern: Unified Python Testing Stack

- **Framework**: `pytest` + `pytest-playwright` (not separate API + UI tools)
- **Layers**:
  - **API tests** (`tests/api/`): Direct REST calls via Playwright `APIRequestContext`
  - **E2E tests** (`tests/e2e/`): Browser automation via Playwright `Page`
  - **Page Objects** (`pages/`): Encapsulate selectors and user interactions
  - **Fixtures** (`tests/fixtures/conftest.py`): Provide `api_client` and authentication

### Critical: React Session Model

The frontend stores auth state **in React memory only** (`useState` in `UserContext`). There is **no `localStorage`, no cookies**.

**Consequence**: 
- `logged_in_page` fixtures must drive the real sign-in UI (cannot seed via storage state).
- Tests must never call `page.goto()` or reload after login—this clears the in-memory session.
- Use client-side navigation (clicking in-app links) to return home after creating a course.

### Fixtures (in `tests/fixtures/conftest.py`)

| Fixture | Scope | Purpose |
|---|---|---|
| `auth_headers` | session | Returns HTTP Basic auth header for joe@smith.com |
| `api_client` | session | Playwright `APIRequestContext` for direct API calls |

### Page Objects (in `pages/`)

| Class | Methods | Purpose |
|---|---|---|
| `LoginPage` | `navigate()`, `login(email, password)` | Sign-in flow |
| `CoursesPage` | `navigate_to_create()`, `create_course(...)`, `is_course_in_list(title)` | Dashboard + create form |

### AI Agent (in `agent/generate_tests.py`)

Reads the Express router (`api/Routes/routes.js`), calls an LLM, writes a **Markdown test plan** (not executable code). Supports three providers:

- **Gemini** (default): `GEMINI_API_KEY` env var
- **Claude**: `ANTHROPIC_API_KEY` env var
- **OpenAI**: `OPENAI_API_KEY` env var

Detects the model from the `--model` flag or `GEMINI_MODEL` env var. Example:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python agent/generate_tests.py --model claude-3-5-sonnet-latest
```

---

## Authentication

The backend uses **HTTP Basic Auth** (not OAuth, not sessions).

- Credentials are sent as `Authorization: Basic <base64(email:password)>`
- Default seeded user: `joe@smith.com` / `joepassword`
- Fixture `auth_headers` builds this header; API tests pass it to every request
- E2E tests use the real UI sign-in (submit the form, wait for redirect)

---

## Environment Variables

| Variable | Default | Notes |
|---|---|---|
| `BASE_URL` | `http://localhost:5173` | React frontend |
| `API_BASE_URL` | `http://localhost:5000` | Express backend |
| `TEST_USER_EMAIL` | `joe@smith.com` | Seeded user for tests |
| `TEST_USER_PASSWORD` | `joepassword` | Seeded password |
| `GEMINI_API_KEY` | unset | Required to run `generate_tests.py` with Gemini |
| `ANTHROPIC_API_KEY` | unset | Required to run `generate_tests.py` with Claude |
| `OPENAI_API_KEY` | unset | Required to run `generate_tests.py` with OpenAI |

Copy `.env.example` to `.env` and fill in your LLM key(s).

---

## CI/CD

`.github/workflows/ci.yml` assumes a **monorepo layout**:
```
ai-test-automation-framework/
├── app/course-catalog-app/  (system under test)
└── tester-repo/             (this project)
```

The workflow:
1. Checks out the repo
2. Installs Node, npm-installs backend + frontend
3. Starts Express (`:5000`) and Vite (`:5173`) in the background
4. Waits for both ports to respond
5. Installs Python dependencies and Playwright browser
6. Runs `pytest` (API + E2E)
7. Runs the AI agent (if `GEMINI_API_KEY` secret is set)
8. Uploads test reports and generated plans as artifacts

To integrate: add the `GEMINI_API_KEY` (or `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`) as a GitHub Actions secret.

---

## Key Files & Their Roles

- **`tests/fixtures/conftest.py`**: Fixture definitions (`api_client`, `auth_headers`)
- **`tests/api/test_courses_api.py`**: Contract tests for REST endpoints
- **`tests/e2e/test_courses_e2e.py`**: Full UI flows (login → create → verify)
- **`pages/login_page.py`**: Sign-in page object
- **`pages/courses_page.py`**: Dashboard + create-course page object
- **`agent/generate_tests.py`**: AI test-plan generator (multi-LLM support)
- **`agent/generated/create_course.md`**: Output of the generator (human-reviewed test plan)
- **`.github/workflows/ci.yml`**: GitHub Actions pipeline
- **`pytest.ini`**: Pytest config (markers, pythonpath)

---

## Common Changes & Patterns

### Adding a new E2E test

1. Import `LoginPage` and `CoursesPage` (or create a new page object)
2. Fixture receives a `page` object from pytest-playwright
3. Drive the UI through page objects, never raw selectors
4. Example:
```python
def test_new_flow(page):
    login_page = LoginPage(page)
    login_page.navigate()
    login_page.login("joe@smith.com", "joepassword")
    page.wait_for_url("http://localhost:5173/")
    # rest of test...
```

### Adding a new API test

1. Use the `api_client` and `auth_headers` fixtures
2. Example:
```python
def test_my_endpoint(api_client, auth_headers):
    response = api_client.get(
        "/api/courses/1",
        headers=auth_headers
    )
    assert response.status == 200
```

### Updating selectors after React changes

1. Find the selector in the real component (e.g., `client/src/components/CreateCourse.jsx`)
2. Update the page object (e.g., `pages/courses_page.py`) **once**
3. All tests using that page object automatically pick up the change

### Running the agent with a different LLM

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python agent/generate_tests.py --model claude-3-5-sonnet-latest

# or
export OPENAI_API_KEY="sk-..."
python agent/generate_tests.py --model gpt-4o
```

---

## Troubleshooting

| Symptom | Diagnosis | Fix |
|---|---|---|
| Tests fail with "connection refused" | Backend/frontend not running | Start both servers in separate terminals |
| E2E test hangs after login | Session lost due to page reload | Use client-side navigation (click links), not `page.goto()` |
| `ModuleNotFoundError: pages` | Python path not configured | Run `pytest` from `tester-repo/` root; `pytest.ini` sets `pythonpath = .` |
| Agent: "Missing API key" | No LLM key in environment or `.env` | Set `GEMINI_API_KEY` (or `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) |
| Playwright browser not found | Browser binaries not installed | Run `python -m playwright install chromium` |
