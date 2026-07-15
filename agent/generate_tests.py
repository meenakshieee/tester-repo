"""Test-writing AI agent.

Reads a target backend source file (by default the Express router at
``api/Routes/routes.js``), asks an LLM to analyse the *actual* routes it finds,
and writes a grounded Markdown test plan under ``agent/generated/``.

Design choices:

* **Markdown-first.** The agent produces human-readable, reviewable test cases
  (UI steps, API payloads, expected assertions) -- not executable code. A senior
  engineer reviews/curates the Markdown before any test is committed, which
  keeps a human in the loop and avoids blindly running machine-written code.
* **Strictly grounded.** The model is instructed to use *only* the endpoints,
  methods, and field names that appear in the supplied source. This is the main
  guard against hallucinated endpoints. We pass the raw source as the sole
  source of truth and forbid inventing anything not present in it.
* **Capability-agnostic.** The scope is derived from the target file (and an
  optional ``--feature`` flag), not hardcoded. With no ``--feature`` the agent
  plans every endpoint it finds; with one it focuses on that capability. The
  output filename follows the scope automatically.
* **Generic LLM Support.** Swapping model vendors (Gemini, Claude, or OpenAI)
  is supported out-of-the-box via a lightweight, native HTTP client wrapper.
  This avoids heavy compiled dependencies (like LiteLLM) that require Rust or C++ compilers.

Usage:
    # Plan every endpoint in the source -> agent/generated/routes_test_plan.md
    python agent/generate_tests.py --source ../app/course-catalog-app/api/Routes/routes.js

    # Focus on one capability -> agent/generated/course_creation.md
    python agent/generate_tests.py --feature "course creation"

    # Any vendor / explicit output
    python agent/generate_tests.py --feature "user login" \
        --model claude-3-5-sonnet-latest --output agent/generated/login.md

Requires the environment variable matching your chosen vendor (e.g. ``GEMINI_API_KEY``,
``ANTHROPIC_API_KEY``, or ``OPENAI_API_KEY``).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# Resolve paths relative to this file so the script works from any CWD.
AGENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = AGENT_DIR.parent

DEFAULT_SOURCE = (
    REPO_ROOT.parent / "app" / "course-catalog-app" / "api" / "Routes" / "routes.js"
)
GENERATED_DIR = AGENT_DIR / "generated"
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# Generic grounding instructions -- capability-agnostic. The specific scope is
# injected into the user prompt, not baked into the system prompt.
SYSTEM_INSTRUCTION = """\
You are a meticulous Senior SDET who writes precise, grounded test plans.

You will be given the complete source code of a backend file. Produce a Markdown
test plan that is grounded strictly in that source.

Hard rules -- follow them exactly:
1. Use ONLY the HTTP methods, URL paths, request fields, response status codes,
   and response body fields that are literally present in the provided source.
2. NEVER invent endpoints, query parameters, headers, or JSON fields that do not
   appear in the source. If information is not in the source, say
   "not specified in source" instead of guessing.
3. Authentication details (scheme, header format) must match the source exactly.
4. Every expected status code and response field you cite must be traceable to a
   specific line of the provided source.
5. Output valid GitHub-flavoured Markdown only. No preamble, no code fences
   around the whole document.
"""

USER_PROMPT_TEMPLATE = """\
Analyse the backend source below and produce a Markdown test plan titled
"# {title}".

Scope: {scope_instruction}

Include these sections:

## Endpoint(s) Under Test
- For each endpoint in scope: method, path, auth requirement, required vs.
  optional request fields, and the success status code + response body -- all
  taken directly from the source.

## UI Test Cases (End-to-End)
- Numbered, step-by-step user actions for exercising this scope through the app
  (e.g. sign in, navigate, fill fields, submit, verify) where a UI flow applies.
  Include at least one happy path and one validation/failure path per capability.
  If a UI flow cannot be inferred from the source, state that explicitly.

## API Test Cases
- For each case: the request (method, path, auth header format, example JSON
  payload) and the expected response (status code + body fields). For every
  mutating endpoint, cover a success case, a missing-required-field case, and an
  unauthenticated case where authentication is required by the source.

## Assertions Checklist
- A bullet list of concrete assertions a test should make.

Backend source file: `{source_name}`

```javascript
{source_code}
```
"""


def _slugify(text: str) -> str:
    """Turn a free-text feature name into a safe snake_case filename stem."""
    slug = re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")
    return slug or "test_plan"


def resolve_scope(feature: str | None, source_name: str) -> tuple[str, str, str]:
    """Derive (title, scope_instruction, output_stem) from the requested feature.

    - With ``--feature``: focus the plan on that capability.
    - Without it: cover every endpoint found in the source (fully generic).
    """
    if feature:
        title = f"{feature.strip().title()} - Test Plan"
        scope = (
            f"Focus specifically on the **{feature.strip()}** capability, but only "
            "if endpoints supporting it exist in the source."
        )
        stem = _slugify(feature)
    else:
        title = f"{source_name} - API Test Plan"
        scope = (
            "Cover **every** endpoint you find in the source. Group the plan by "
            "endpoint and derive each capability from the code itself."
        )
        stem = f"{_slugify(Path(source_name).stem)}_test_plan"
    return title, scope, stem


# Substrings that indicate a transient, retryable LLM API error (server busy /
# rate limited) rather than a permanent one (bad key, invalid model, bad request).
_TRANSIENT_MARKERS = (
    "503", "unavailable", "overloaded", "high demand",
    "429", "resource_exhausted", "rate limit", "try again",
)


def _is_transient(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(marker in message for marker in _TRANSIENT_MARKERS)


def _with_retry(fn, *, attempts: int = 4, base_delay: float = 2.0):
    """Call ``fn`` with exponential back-off on transient LLM API errors.

    Permanent errors (auth, invalid model, bad request) are re-raised
    immediately; only transient ones (503/429/overloaded) are retried.
    """
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - we re-raise non-transient below
            if attempt >= attempts or not _is_transient(exc):
                raise
            delay = base_delay * (2 ** (attempt - 1))
            print(
                f"[agent] Transient LLM error (attempt {attempt}/{attempts}): {exc}\n"
                f"[agent] Retrying in {delay:.0f}s...",
                file=sys.stderr,
            )
            time.sleep(delay)


def read_source(source_path: Path) -> str:
    """Read the target backend file, failing loudly if it is missing."""
    if not source_path.exists():
        raise FileNotFoundError(
            f"Target source file not found: {source_path}\n"
            "Pass a valid --source path (e.g. the Express router)."
        )
    return source_path.read_text(encoding="utf-8")


def generate_test_plan(
    model: str,
    source_name: str,
    source_code: str,
    title: str,
    scope_instruction: str,
) -> str:
    """Call the LLM using Gemini SDK or generic API requests (Claude, OpenAI)."""
    prompt = USER_PROMPT_TEMPLATE.format(
        title=title,
        scope_instruction=scope_instruction,
        source_name=source_name,
        source_code=source_code,
    )
    
    # 1. Gemini Models (Use the official SDK)
    if model.startswith("gemini/") or "gemini-" in model:
        from google import genai
        from google.genai import types
        
        # Clean prefix if user input was gemini/gemini-x
        clean_model = model.split("/")[-1]
        
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Missing GEMINI_API_KEY (or GOOGLE_API_KEY). Set it in your environment or a .env file."
            )
            
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=clean_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.1,
            ),
        )
        text = (response.text or "").strip()
        if not text:
            raise RuntimeError("The model returned an empty response.")
        return text
        
    # 2. Claude (Anthropic) Models
    elif model.startswith("anthropic/") or "claude-" in model:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("Missing ANTHROPIC_API_KEY environment variable.")
            
        clean_model = model.split("/")[-1]
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        data = {
            "model": clean_model,
            "max_tokens": 4000,
            "system": SYSTEM_INSTRUCTION,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        }
        res = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
        res.raise_for_status()
        return res.json()["content"][0]["text"].strip()
        
    # 3. OpenAI Models
    elif model.startswith("openai/") or "gpt-" in model:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY environment variable.")
            
        clean_model = model.split("/")[-1]
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": clean_model,
            "messages": [
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
        }
        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"].strip()
        
    else:
        raise ValueError(
            f"Unsupported or unrecognized model name: '{model}'. "
            "Please use gemini-3.5-flash, or prefix with gemini/, anthropic/, or openai/."
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Markdown test plan with an LLM.")
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Path to the backend source file to analyse (default: the Express router).",
    )
    parser.add_argument(
        "--feature",
        default=None,
        help=(
            "Optional capability to focus on (e.g. 'course creation', 'user login'). "
            "Omit to generate a plan covering every endpoint in the source."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Path to write the Markdown test plan. Defaults to "
            "agent/generated/<feature-or-source>.md derived from the scope."
        ),
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model identifier (default: {DEFAULT_MODEL}). Supports Gemini, Claude, and OpenAI.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = parse_args(argv)

    source_path: Path = args.source.resolve()

    # Derive the plan's title, scope, and default output name from the target
    # (and the optional --feature), instead of assuming a fixed capability.
    title, scope_instruction, output_stem = resolve_scope(args.feature, source_path.name)
    output_path: Path = (args.output or (GENERATED_DIR / f"{output_stem}.md")).resolve()

    print(f"[agent] Reading backend source: {source_path}")
    source_code = read_source(source_path)

    print(f"[agent] Scope: {title}")
    print(f"[agent] Requesting test plan from model: {args.model}")
    markdown = _with_retry(lambda: generate_test_plan(
        model=args.model,
        source_name=source_path.name,
        source_code=source_code,
        title=title,
        scope_instruction=scope_instruction,
    ))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown + "\n", encoding="utf-8")
    print(f"[agent] Wrote test plan ({len(markdown)} chars) to: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
