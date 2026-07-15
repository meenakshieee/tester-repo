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

# Run by marker (api / e2e) or by path
pytest -m api
pytest tests/e2e -v

# Run in parallel (pytest-xdist) — safe: created data is cleaned up per test
pytest -n auto

# Run E2E with visible browser
pytest tests/e2e --headed

# Run a single test
pytest tests/e2e/test_courses_e2e.py::test_e2e_create_course_success

# Generate a Markdown test plan with the AI agent (scope derived from the target)
export GEMINI_API_KEY="your_key"  # or ANTHROPIC_API_KEY, OPENAI_API_KEY
python agent/generate_tests.py                        # plan for ALL endpoints in the source
python agent/generate_tests.py --feature "course creation"   # focus one capability
python agent/generate_tests.py --model claude-3-5-sonnet-latest --output agent/generated/plan.md

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
  - **Generated tests** (`tests/generated/`): Executable tests derived from the AI agent's Markdown plan
  - **Page Objects** (`pages/`): Encapsulate selectors and user interactions
  - **Fixtures** (`tests/fixtures/conftest.py`): Provide the API client, auth, credentials, and data cleanup
  - **Config** (`config.py`, repo root): single env-driven source of truth for URLs + credentials
- **Fixture loading**: the root `tests/conftest.py` registers the fixtures via
  `pytest_plugins = ["tests.fixtures.conftest"]`, making them available to every test module.

### Critical: React Session Model

The frontend stores auth state **in React memory only** (`useState` in `UserContext`). There is **no `localStorage`, no cookies**.

**Consequence**:
- E2E tests must drive the real sign-in UI via `LoginPage` (cannot seed a session via storage state).
- After login, a `page.goto()` / reload **drops the session**. It's safe only when heading to a
  *public* route (e.g. the dashboard `/` and course-detail pages, which render without auth —
  this is why `CoursesPage.navigate_to_dashboard` works despite using `goto`).
- To stay authenticated (for a protected action), navigate by clicking in-app links, not `goto`.

### Fixtures (in `tests/fixtures/conftest.py`)

| Fixture | Scope | Purpose |
|---|---|---|
| `api_client` | session | Playwright `APIRequestContext` for direct API calls |
| `auth_headers` | session | HTTP Basic auth header for the configured test user |
| `test_user` | session | `{"email", "password"}` from config (env-overridable) — use in E2E logins |
| `created_courses` | function | Append created course IDs; deletes them on teardown (enables safe parallel runs) |

All values come from [`config.py`](config.py), so nothing is hardcoded — override via env or `.env`.

### Page Objects (in `pages/`)

Page objects own **all** selectors and expose intent-revealing `expect_*` assertion
methods (using Playwright's auto-waiting `expect`). Tests never touch raw selectors
or hardcoded URLs.

| Class | Actions | Assertions |
|---|---|---|
| `LoginPage` | `navigate()`, `login(email, password)` | `expect_signed_in()` |
| `CoursesPage` | `navigate_to_dashboard()`, `navigate_to_create()`, `create_course(...)`, `get_current_course_id()` | `expect_on_detail_page(title)`, `expect_course_in_list(title)`, `expect_validation_errors()` |

Both read `BASE_URL` (default `http://localhost:5173`) internally, so tests stay
environment-agnostic — never hardcode URLs in a test.

### AI Agent (in `agent/generate_tests.py`)

Reads a backend source file (default: `api/Routes/routes.js`), calls an LLM, writes a
**Markdown test plan** (not executable code) under `agent/generated/`.

**Capability-agnostic** — scope is *derived*, never hardcoded:
- No `--feature` → plans **every** endpoint in the source → `<source>_test_plan.md`
- `--feature "course creation"` → focuses that capability → `course_creation.md`
- `--output` overrides the filename; `resolve_scope()` derives the title/scope/stem.

The system prompt is grounding-only (use only what's in the source, never invent). Providers:
- **Gemini** (default): `GEMINI_API_KEY` / `GOOGLE_API_KEY`
- **Claude**: `ANTHROPIC_API_KEY`
- **OpenAI**: `OPENAI_API_KEY`

Model comes from `--model` (or `GEMINI_MODEL`); vendor is inferred from the model name.

---

## Authentication

The backend uses **HTTP Basic Auth** (not OAuth, not sessions).

- Credentials are sent as `Authorization: Basic <base64(email:password)>`
- Default seeded user: `joe@smith.com` / `joepassword` (env-overridable via `config.py`)
- `config.py` builds the header (`settings.basic_auth_header`); the `auth_headers` fixture exposes it, API tests pass it to every request
- E2E tests sign in through the real UI using the `test_user` fixture

---

## Environment Variables

| Variable | Default | Notes |
|---|---|---|
| `BASE_URL` | `http://localhost:5173` | React frontend (read by page objects + fixtures) |
| `API_BASE_URL` | `http://localhost:5000` | Express backend (read by the `api_client` fixture) |
| `TEST_USER_EMAIL` | `joe@smith.com` | Seeded test user (override for CI/staging) |
| `TEST_USER_PASSWORD` | `joepassword` | Seeded test user password |
| `GEMINI_MODEL` | `gemini-3.5-flash` | Default model for the agent (overridable via `--model`) |
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | unset | Required to run `generate_tests.py` with Gemini |
| `ANTHROPIC_API_KEY` | unset | Required to run `generate_tests.py` with Claude |
| `OPENAI_API_KEY` | unset | Required to run `generate_tests.py` with OpenAI |

Copy `.env.example` to `.env` and fill in values. **All** of the above are read through
[`config.py`](config.py) (which calls `load_dotenv()`), so `.env` applies to both the tests
and the agent. There are **no hardcoded credentials or URLs** in the test/page modules —
the defaults live only in `config.py`.

---

## CI/CD

`.github/workflows/ci.yml` (job name: **CI Gating Suite**) runs on push/PR to `main`/`master`.
It does **not** assume the app is present — it clones the app under test into a sibling
`../app/course-catalog-app` directory, matching the path the tests and agent expect.

The workflow:
1. Checks out this repo
2. Clones the Course Catalog app from GitHub into `../app/course-catalog-app`
3. Sets up Node 20, then `npm install` + `npm run seed` + `npm start` for the backend, waiting on `:5000`
4. `npm install` + `npm run dev` for the frontend, waiting on `:5173`
5. Sets up Python 3.12, installs dependencies + the Playwright browser
6. Runs `pytest -v` (API + E2E + AI-grounded tests)
7. Runs the AI agent — only if the `GEMINI_API_KEY` secret is set (otherwise the step logs a skip and passes)

To enable the agent step: add `GEMINI_API_KEY` (or `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`)
as a GitHub Actions secret. Note: there is currently no artifact-upload step.

---

## Key Files & Their Roles

- **`config.py`** (repo root): single env-driven source of truth for URLs + credentials
- **`tests/conftest.py`**: Root conftest — registers the fixtures plugin
- **`tests/fixtures/conftest.py`**: Fixtures (`api_client`, `auth_headers`, `test_user`, `created_courses`)
- **`tests/api/test_courses_api.py`**: Contract tests for REST endpoints
- **`tests/e2e/test_courses_e2e.py`**: Full UI flows (login → create → verify)
- **`tests/generated/test_courses_agent.py`**: Executable tests derived from the agent's plan
- **`pages/login_page.py`**: Sign-in page object
- **`pages/courses_page.py`**: Dashboard + create-course page object
- **`agent/generate_tests.py`**: AI test-plan generator (capability-agnostic, multi-LLM)
- **`agent/generated/*.md`**: Generated test plans (filename follows the scope; human-reviewed)
- **`.github/workflows/ci.yml`**: GitHub Actions pipeline
- **`pytest.ini`**: Pytest config (markers, pythonpath)

---

## Common Changes & Patterns

### Adding a new E2E test

1. Import `LoginPage` and `CoursesPage` (or create a new page object)
2. Take `page`, `test_user`, and `created_courses` fixtures
3. Drive the UI through page objects — never raw selectors, never hardcoded URLs or credentials
4. Assert via the page object's `expect_*` methods (auto-waiting), not `page.wait_for_url(...)` with a literal URL
5. Register any created course for cleanup (keeps parallel runs safe)
6. Example:
```python
def test_new_flow(page, test_user, created_courses):
    login_page = LoginPage(page)
    courses_page = CoursesPage(page)

    login_page.navigate()
    login_page.login(test_user["email"], test_user["password"])   # NOT hardcoded creds
    login_page.expect_signed_in()                                  # NOT page.wait_for_url("http://localhost:5173/")
    # ...create a course...
    created_courses.append(courses_page.get_current_course_id())   # cleanup on teardown
```

### Adding a new API test

1. Use the `api_client` and `auth_headers` fixtures; add `created_courses` if the test creates data
2. Example:
```python
def test_my_endpoint(api_client, auth_headers, created_courses):
    response = api_client.post("/api/courses", data={...}, headers=auth_headers)
    assert response.status == 201
    created_courses.append(response.json()["courseId"])   # cleaned up on teardown
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
