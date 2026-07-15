# Automation Framework & Test-Writing Agent

This repository contains a professional automation testing framework and an AI-powered test-generation agent built for the **Course Catalog App** (React client + Express SQLite backend).

---

## 📂 Project Structure

```
tester-repo/
├── tests/
│   ├── api/              # Reference API tests (Basic Auth & Course CRUD)
│   ├── e2e/              # Reference UI End-to-End tests (POM-based)
│   ├── generated/         # Executable generated test cases (grounded in AI output)
│   └── fixtures/         # Shared pytest fixtures (conftest.py)
├── pages/                # Page Object Model (POM) classes
├── agent/                # Python AI agent scripts
│   └── generated/        # AI generated Markdown test cases (create_course.md)
├── docs/                 # Architectural decision documents (architecture.md)
├── .github/workflows/    # CI/CD pipelines (ci.yml)
├── requirements.txt      # Python dependencies
├── CODEOWNERS            # Access control configuration for gating
└── README.md             # This document
```

---

## 🛠️ Local Setup & Execution

### Prerequisites
*   **Node.js 20 LTS**
*   **Python 3.12**

### 1. Start the Target Application
Ensure the Course Catalog App is running locally. In your application workspace:
1.  **Start API Backend:**
    ```bash
    cd app/course-catalog-app/api
    npm install
    npm run seed
    npm start
    ```
    *The API will start listening on port 5000.*
2.  **Start React Client:**
    ```bash
    cd app/course-catalog-app/client
    npm install
    npm run dev
    ```
    *The client will start listening on port 5173.*

### 2. Setup the Tester Environment
Inside this `tester-repo` directory:
1.  **Create and Activate Virtual Environment:**
    ```powershell
    # Windows PowerShell
    py -3.12 -m venv venv
    .\venv\Scripts\Activate.ps1
    ```
2.  **Install Dependencies:**
    ```powershell
    pip install -r requirements.txt
    playwright install chromium
    ```

### 3. Run the Automated Tests
Execute the pytest suite (API, E2E UI, and AI-grounded tests) locally:
```powershell
# Runs against localhost by default
pytest -v

# (Optional) Run tests against a different deployment environment (Staging/QA)
$env:BASE_URL="http://staging-frontend.example.com"
$env:API_BASE_URL="http://staging-backend.example.com"
pytest -v
```

### 4. Run the AI Test-Writing Agent
The agent reads the Express backend source code and generates a natural-language markdown test plan (`agent/generated/create_course.md`):
```powershell
# Set your API Key
$env:GEMINI_API_KEY="your_api_key_here"

# Execute Agent (defaults to gemini-3.5-flash)
python agent/generate_tests.py
```

### 5. Swapping LLM Providers (Optional)
The agent supports multiple LLM providers out of the box. You can swap models without any code modifications by setting the correct environment variable and passing the `--model` flag:

*   **Claude (Anthropic):**
    ```powershell
    $env:ANTHROPIC_API_KEY="your_anthropic_key_here"
    python agent/generate_tests.py --model claude-3-5-sonnet-latest
    ```
*   **OpenAI (e.g. GPT-4o / GPT-5):**
    ```powershell
    $env:OPENAI_API_KEY="your_openai_key_here"
    python agent/generate_tests.py --model gpt-4o
    ```

---

## 🚀 CI Pipeline & Gating Sketch

### GitHub Actions Pipeline
The pipeline configured in `.github/workflows/ci.yml` triggers on every push or pull request to `main`/`master`. It dynamically boots a fresh instance of the application (cloning it from GitHub, seeding SQLite, and starting Node servers) before executing the Playwright suite.

### PR Gating Workflow
To protect production from regressions:
1.  **Branch Protection Rules:** The `main` branch of the frontend/backend repository is protected. Direct merges are disabled.
2.  **Required Status Checks:** Pull requests are blocked from merging until the `CI Gating Suite` workflow in this repository runs and reports a **Green/Pass** status.
3.  **CODEOWNERS Review:** Any edits modifying test files, fixtures, or workflows require mandatory review and approval from the `@automation-engineers-team` before the branch can be merged.
