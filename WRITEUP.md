# Writeup

**Tester repo:** https://github.com/meenakshieee/tester-repo
**App under test:** Course Catalog App — a public open-source full-stack project (React client + Express/SQLite REST API): https://github.com/WeStOn2000/Full-Stack-App-with-React-and-a-REST-API. Cloned, not modified.
**Model / tooling:** pytest + playwright-python; AI agent via Gemini (`gemini-3.5-flash`), pluggable to Claude/OpenAI. Built with Claude.

## What I chose and why
I picked the Course Catalog App because the brief requires an app with **both a frontend and a backend**, and its **SQLite** backend runs locally with zero external infrastructure (no Postgres, no Docker). That let me spend the one-day budget on the parts that are weighted — the tester repo and the agent — instead of environment plumbing, which matches the "run locally / smaller and sharper" guidance.

For the suite I used a **single Python/Playwright stack** so API and UI tests share one language, one virtual environment, and one CI runner. Playwright covers both HTTP (`APIRequestContext`) and browser E2E, and its auto-waiting removes a whole class of timing flakes. Tests use the **Page Object Model** and a **central `config.py`** so there are no hardcoded URLs or credentials — everything is env-overridable for staging/CI.

The agent is **Markdown-first**: it reads the real Express router and emits a natural-language test *plan* (endpoints, payloads, expected assertions), strictly grounded — instructed to use only what exists in the source and to say "not specified in source" rather than invent. A human curates the plan before it becomes code; the committed `tests/generated/` tests close the loop and pass in CI.

## Biggest trade-off
Having the agent produce a **reviewable plan instead of auto-writing runnable tests**. The cost is a manual plan→code step. The benefit is that hallucinated endpoints or plausible-but-worthless cases are caught in plain English during review, before they ever land as committed tests. For a team whose guardrail must not "kill merge speed," an agent that silently commits bad tests is worse than one that hands a human a grounded plan.

## Single biggest threat to reliability — and how I'd handle it
**Flakiness from shared, mutable state.** The E2E and API tests run against a live app and one shared database; leftover data, a shared user, or interleaved parallel runs cause non-deterministic failures. Flaky tests get muted, and a muted guardrail is worthless. Mitigations in place: Playwright auto-waiting (timing flakes), unique per-test data (UUID titles), a `course_factory` + `created_courses` fixture that isolates and deletes what each test creates (making `pytest -n auto` safe), and a **quarantine policy** (`@pytest.mark.quarantine` auto-excluded from gate runs) so one flaky test never blocks a merge. Next: a dedicated seeded user per xdist worker and an ephemeral DB reset in CI so every run starts from a known state.

## What I'd build next
`POST /api/users` (signup) coverage; CI test **sharding** as the suite grows; and agent upgrades — feed it the model/validation files (not just routes), have it emit a **coverage diff** against existing tests, and auto-open a PR with the generated plan for review.
