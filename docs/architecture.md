# System Architecture & Technical Decisions

This document outlines the architectural decisions, design choices, and technical trade-offs made in the design of the automation testing framework and the test-writing AI agent.

---

## 1. Why Playwright (Python)?
Playwright was chosen as the core automation tool for the following reasons:
*   **Unified API & E2E Testing:** Playwright provides native support for both browser-based UI automation and HTTP-based API testing via `APIRequestContext`. This eliminates the need for separate tools (like Axios/SuperTest for API and Cypress for UI).
*   **Built-in Resilience (Auto-waiting):** Unlike Selenium, Playwright automatically waits for elements to be actionable before performing actions, which drastically reduces test flakiness.
*   **Python Ecosystem Alignment:** Playwright Python integrates seamlessly with `pytest`, which is the industry standard for Python testing and supports advanced features like fixtures, parameterization, and parallel execution.

---

## 2. Why One Framework for API + UI?
Maintaining separate frameworks for API and UI testing creates a split codebase and duplicate environment configurations. By housing both in a single Python `pytest` suite:
*   **Shared Authentication State:** E2E UI tests can reuse API-level authentication to skip login screens, saving significant test execution time.
*   **Simplified CI/CD:** A single runner pipeline installs Python dependencies once, executing both the API and UI suites in a single workflow.
*   **Reduced Context-Switching:** SDETs can write backend and frontend tests in the same language and environment, using shared utilities.

---

## 3. Why SQLite?
The application uses SQLite as its database engine for development:
*   **Portability & Zero Setup:** SQLite stores the entire database in a single local file (`fsjstd-restapi.db`). This allows the entire stack (backend, frontend, database) to spin up locally on Windows in seconds without requiring heavy external engines (like PostgreSQL) or running Docker Desktop.
*   **Deterministic State Restoration:** For integration testing, resetting or seeding database state is as simple as copying a fresh seeded SQLite file, ensuring a clean, predictable state before every test run.

---

## 4. Why Markdown-First AI Test Case Generation?
For the AI agent (`generate_tests.py`), we adopted a "Markdown-first" generation pattern rather than letting the AI write and run code directly:
*   **Human-in-the-Loop Review:** Generating natural-language test plans (steps, payloads, assertions) allows senior engineers to audit the test cases for accuracy and correctness *before* converting them to executable code. This prevents hallucinated endpoints or bad code from cluttering the repository.
*   **Grounding and Reliability:** The agent reads the raw Express router code (`routes.js`) and is strictly instructed to only outline tests for endpoints that physically exist in the file. This keeps the agent's output grounded in the actual codebase.
