# Automation Framework & Test-Writing Agent

[![CI Gating Suite](https://github.com/meenakshieee/tester-repo/actions/workflows/ci.yml/badge.svg)](https://github.com/meenakshieee/tester-repo/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Playwright 1.44](https://img.shields.io/badge/Playwright-1.44-2EAD33.svg)](https://playwright.dev/python/)
[![pytest](https://img.shields.io/badge/pytest-8.2-0A9EDC.svg)](https://docs.pytest.org/)
[![Tests](https://img.shields.io/badge/tests-8%20passing-success.svg)](tests/)

A professional test automation framework and an AI-powered test-generation agent, built for the **Course Catalog App** (React client + Express/SQLite backend). It unifies **API contract testing** and **UI end-to-end testing** in a single Python/Playwright stack, and includes a grounded LLM agent that turns backend source code into reviewable Markdown test plans.

---

## Contents

- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Local Setup & Execution](#️-local-setup--execution)
- [AI Test-Writing Agent](#-ai-test-writing-agent)
- [CI Pipeline & Gating](#-ci-pipeline--gating)
- [Troubleshooting](#-troubleshooting)
- [Known Gaps & Roadmap](#-known-gaps--roadmap)

---

## ⚡ Quick Start

Already have the app running on `:5000` (API) and `:5173` (client)? Run the full suite in three commands:

```bash
# From inside tester-repo/
pip install -r requirements.txt
playwright install chromium
pytest -v
```

All **8 tests** (API + E2E + AI-grounded) run in ~3 seconds against your local servers — no configuration required.

> First time? See [Local Setup & Execution](#️-local-setup--execution) for how to start the app and create the virtual environment.

---

## 🏛 Architecture

This framework makes a few deliberate design choices. Full rationale lives in [`docs/architecture.md`](docs/architecture.md).

| Decision | Why |
| --- | --- |
| **Unified Python stack** (`pytest` + `pytest-playwright`) | One language and one virtual environment for API tests, UI tests, and the AI agent — no JavaScript/Python split. |
| **Playwright** (over Selenium/Cypress) | Native support for *both* browser automation and HTTP API testing via `APIRequestContext`, plus auto-waiting that removes flaky sleeps. |
| **Page Object Model** (`pages/`) | Selectors live in exactly one place; tests express intent, not CSS. UI changes touch one file, not every test. |
| **Markdown-first AI agent** | The agent emits a human-readable test *plan*, not executable code — a senior engineer reviews it before anything is committed. |
| **SQLite backend** | The app self-seeds a file-based database, so the whole stack boots in seconds with zero external infra (no Postgres, no Docker). |

**One critical constraint worth knowing:** the React client stores its auth session in memory (`useState`), not in `localStorage` or cookies. E2E tests therefore drive the real sign-in UI and must use client-side navigation after login — a hard page reload discards the session. This shaped the fixture and page-object design.

---

## 📂 Project Structure

```
tester-repo/
├── config.py             # Single source of truth for URLs + credentials (env-driven)
├── clients/              # Typed, auth-aware API client (courses_client.py)
├── pages/                # Page Object Model — BasePage + concrete pages
├── tests/
│   ├── api/              # API contract + CRUD/authorization tests
│   ├── e2e/              # UI end-to-end tests (POM-based)
│   ├── generated/        # Executable tests derived from the AI agent's plan
│   ├── fixtures/         # Shared fixtures (client, factory, cleanup, auth)
│   └── conftest.py       # Fixture registration + quarantine policy hook
├── agent/                # AI test-writing agent
│   └── generated/        # AI-generated Markdown test plans
├── docs/                 # Architecture decision record (architecture.md)
├── .github/workflows/    # CI/CD pipeline (ci.yml)
├── requirements.txt      # Python dependencies
├── CODEOWNERS            # Review-gating configuration
├── CONTRIBUTING.md       # How to add tests (taxonomy, quarantine, cleanup)
└── README.md            # This document
```

---

## 🛠️ Local Setup & Execution

### Prerequisites
- **Node.js 20 LTS** (Node 24 fails to compile the native `sqlite3` driver)
- **Python 3.12** (Python 3.14 fails to compile Playwright's `greenlet`)

### 1. Start the Target Application
In your application workspace:

1. **Start the API backend:**
   ```bash
   cd app/course-catalog-app/api
   npm install
   npm run seed
   npm start
   ```
   *The API listens on port 5000.*

2. **Start the React client:**
   ```bash
   cd app/course-catalog-app/client
   npm install
   npm run dev
   ```
   *The client listens on port 5173.*

### 2. Set Up the Tester Environment
Inside this `tester-repo` directory:

1. **Create and activate a virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     py -3.12 -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux:**
     ```bash
     python3.12 -m venv venv
     source venv/bin/activate
     ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

### 3. Run the Tests

**Run everything** (API, UI, and AI-grounded tests):
```bash
pytest -v
```

**Run a subset:**
```bash
pytest tests/api -v            # API contract tests only
pytest -m api                  # ...or by marker (api / e2e)
pytest tests/e2e --headed      # Watch the browser
pytest tests/e2e/test_courses_e2e.py::test_e2e_create_course_success   # A single test
```

**Run in parallel** (via `pytest-xdist`):
```bash
pytest -n auto                 # one worker per CPU core
pytest -n 4                    # a fixed number of workers
```
Parallel execution is **safe** here: each test that creates data registers it with the
`created_courses` fixture, which deletes it on teardown — so workers never collide on
shared database state. Parallelism is kept **opt-in** (not enabled by default) because for
a suite this small the per-worker startup and browser overhead outweighs the savings;
it pays off as the suite grows.

**Run against a hosted environment** (Staging / QA) by overriding the defaults:
- **Windows (PowerShell):**
  ```powershell
  $env:BASE_URL="http://staging-frontend.example.com"
  $env:API_BASE_URL="http://staging-backend.example.com"
  pytest -v
  ```
- **macOS / Linux:**
  ```bash
  BASE_URL="http://staging-frontend.example.com" API_BASE_URL="http://staging-backend.example.com" pytest -v
  ```

### What's Covered

| Layer | Tests | Scope |
| --- | --- | --- |
| **API contract** | 4 | `GET`/`POST /api/courses`, missing-field validation, unauthenticated rejection |
| **API CRUD + authz** | 6 | `GET`/`PUT`/`DELETE /api/courses/:id`, 404s, and a cross-user **403** authorization check |
| **E2E (UI)** | 2 | Sign in → create course → verify on dashboard; empty-form validation |
| **AI-generated** | 2 | Executable tests derived from the agent's grounded Markdown plan |
| **Total** | **14** | Full course lifecycle, exercised through a typed client + data factory. |

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the tagging taxonomy, quarantine policy, and how to add tests.

---

## 🤖 AI Test-Writing Agent

The agent reads the Express backend source and generates a natural-language Markdown test plan at `agent/generated/create_course.md`, strictly grounded in the endpoints that actually exist in the source.

```powershell
# Set your API key
$env:GEMINI_API_KEY="your_api_key_here"

# Run the agent (defaults to gemini-3.5-flash)
python agent/generate_tests.py
```

### Swapping LLM Providers (Optional)
The agent supports multiple providers with no code changes — set the matching key and pass `--model`:

- **Claude (Anthropic):**
  ```powershell
  $env:ANTHROPIC_API_KEY="your_anthropic_key_here"
  python agent/generate_tests.py --model claude-3-5-sonnet-latest
  ```
- **OpenAI (e.g. GPT-4o):**
  ```powershell
  $env:OPENAI_API_KEY="your_openai_key_here"
  python agent/generate_tests.py --model gpt-4o
  ```

---

## 🚀 CI Pipeline & Gating

### GitHub Actions Pipeline
The workflow in [`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push or pull request to `main`/`master`:

1. Checks out this repository
2. Clones the Course Catalog app into a sibling directory
3. Installs Node, seeds SQLite, and starts the backend (`:5000`) and frontend (`:5173`)
4. Waits until both servers respond
5. Installs Python + the Playwright browser
6. Runs `pytest` (API + E2E + AI-grounded tests)
7. Runs the AI agent (only if the `GEMINI_API_KEY` secret is set)

**To enable the agent step:** add `GEMINI_API_KEY` under GitHub → Settings → Secrets and variables → Actions.

### PR Gating Workflow
To protect `main` from regressions:
1. **Branch Protection:** Direct merges to `main` are disabled.
2. **Required Status Checks:** PRs cannot merge until the `CI Gating Suite` reports a **Pass**.
3. **CODEOWNERS Review:** Edits to tests, fixtures, or workflows require approval from the `@automation-engineers-team`.

---

## 🩺 Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Tests fail with **"connection refused"** | Backend/frontend not running | Start both servers (`:5000` and `:5173`) before running `pytest`. |
| **E2E test hangs or logs out** after login | A hard page reload cleared the in-memory React session | Navigate via in-app links, never `page.goto()` after login. |
| **`ModuleNotFoundError: pages`** | Python path not set | Run `pytest` from the `tester-repo/` root — `pytest.ini` sets `pythonpath = .`. |
| Agent: **"Missing API key"** | No LLM key configured | Set `GEMINI_API_KEY` (or `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`) in your shell or `.env`. |
| **Playwright browser not found** | Browser binaries not installed | Run `playwright install chromium`. |
| `sqlite3` build error during `npm install` | Node version too new | Use Node 20 LTS. |
| `greenlet` build error during `pip install` | Python version too new | Use Python 3.12. |

See [`docs/architecture.md`](docs/architecture.md) for the full design rationale and analysis.

---

## 🗺 Known Gaps & Roadmap

This framework covers the **course-creation** flow as a reference implementation, and is
built to scale from there.

**Already in place for scale:**
- Centralized, env-overridable config ([`config.py`](config.py)) — no hardcoded URLs or credentials.
- Per-test data cleanup (`created_courses` fixture), which also exercises `DELETE /api/courses/:id`.
- Safe parallel execution via `pytest-xdist` (`pytest -n auto`).
- A capability-agnostic AI agent (`--feature` derives scope; not welded to one endpoint).

**Planned extensions:**
- [ ] `PUT /api/courses/:id` — dedicated update-course tests (ownership + validation)
- [ ] `DELETE /api/courses/:id` — dedicated delete tests, incl. `403` for non-owners (currently only exercised as cleanup)
- [ ] `GET /api/courses/:id` — course-detail contract
- [ ] `POST /api/users` — sign-up flow
- [ ] Reusable test-data factories for payload generation
- [ ] Trace/video capture on failure in CI
