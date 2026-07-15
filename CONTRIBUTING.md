# Contributing

How to add tests to this suite so it stays **reliable, fast, and trustworthy** as
it grows — the contract that lets many engineers add many tests without the
suite rotting or blocking merges.

## Architecture in one minute

- **`config.py`** — the only place URLs and credentials live (env-overridable). Never hardcode them in a test.
- **`clients/courses_client.py`** — typed, auth-aware API client. Tests call `courses_api.create_course(...)`, not raw `request.post(...)`.
- **`pages/`** — Page Objects. `BasePage` provides navigation/URL/waiting; a new page is a short subclass that declares locators and (optionally) `_verify_loaded`.
- **`tests/fixtures/conftest.py`** — fixtures: `courses_api`, `other_courses_api`, `test_user`, `created_courses`, `course_factory`.

## Adding a test

**API test** — use the typed client and the factory; register created data for cleanup:
```python
import pytest
pytestmark = [pytest.mark.api]

def test_update_course(courses_api, course_factory):
    course = course_factory()                       # created + auto-cleaned
    resp = courses_api.update_course(course["id"], {"title": "New", "description": "..."})
    assert resp.status == 204
```

**E2E test** — drive Page Objects only; use `test_user` (never hardcoded creds); register created courses:
```python
import pytest
pytestmark = [pytest.mark.e2e]

def test_flow(page, test_user, created_courses):
    login = LoginPage(page); login.navigate(); login.login(test_user["email"], test_user["password"])
    login.expect_signed_in()
    # ...create a course via CoursesPage...
    created_courses.append(courses_page.get_current_course_id())
```

### Rules
1. No hardcoded URLs or credentials — everything comes from `config.py` / fixtures.
2. No raw selectors in tests — they live in Page Objects only.
3. Anything you create, register with `created_courses` (or use `course_factory`) so the suite is isolation-safe and parallel-safe.
4. Assert something meaningful; tag it (see below).

## Tagging taxonomy (markers)

| Marker | Meaning | When it runs |
| --- | --- | --- |
| `smoke` | Fast, high-value critical-path checks | The pre-merge gate |
| `api` | Backend REST contract tests | Gate + full suite |
| `e2e` | Browser UI tests | Gate + full suite |
| `regression` | Broader coverage | Full/nightly suite |
| `quarantine` | Known-flaky, has an open ticket | **Excluded** from default & gate runs |

Select with `pytest -m smoke`, `pytest -m "api or e2e"`, etc.

## Quarantine policy (protecting merge speed)

A flaky test erodes trust and, worse, trains the team to ignore red. So:

1. When a test flakes and can't be fixed immediately, mark it `@pytest.mark.quarantine` and open a tracking ticket.
2. Quarantined tests are **auto-skipped** in default and gate runs (enforced in `tests/conftest.py`), so one flaky test never blocks a merge.
3. Run them deliberately with `pytest -m quarantine`. Quarantine is a short-lived debt, not a graveyard — fix or delete.

## Running fast (parallel & sharding)

```bash
pytest                # serial (default)
pytest -n auto        # parallel: one worker per core (safe — data is cleaned up per test)
pytest -m smoke       # the quick gate subset
```
Parallelism is opt-in locally because for a small suite worker startup dominates; enable it in CI as the suite grows.

## Observability

- Every run writes a JUnit report to `reports/junit.xml` for CI/reporting tools.
- In CI, failing tests capture a Playwright **trace, video, and screenshot** (uploaded as build artifacts).
- Locally, opt in when debugging (kept out of defaults to avoid a Windows + xdist output-dir race):
  ```bash
  pytest tests/e2e --tracing=retain-on-failure --video=retain-on-failure --screenshot=only-on-failure
  ```

## Review & gating

`CODEOWNERS` routes changes to tests, fixtures, and workflows to the automation
engineers for required review. The `CI Gating Suite` must be green before merge.
