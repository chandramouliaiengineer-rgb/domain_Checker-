# Project: brandgen — From Start to End

This document describes what is used in this project and how to build & run it, from start to end.

## Overview
- Purpose: coin brandable domain-name candidates for a user-provided idea and check .com availability.
- Architecture: single FastAPI backend serving a static frontend. Backend composes a rule-based naming skill, an LLM-based generator, and live domain checks via Verisign RDAP.

## Tech stack & Libraries
- Python 3.10+ (uses modern typing features like `list[str]`)
- FastAPI — HTTP API server
- Uvicorn — ASGI server
- httpx — async HTTP client (used for RDAP domain checks)
- openai (AsyncOpenAI client) — used to call the LLM API
- python-dotenv — load environment variables from `.env`

Declared dependencies: see `requirements.txt`.

## Key files and responsibilities
- `main.py` — FastAPI app, serves `static/index.html`, exposes `/generate`, `/variations`, and `/health` endpoints. Coordinates LLM generation, filtering, and domain checks.
- `llm.py` — Async LLM client wrapper. Calls an AsyncOpenAI client configured for an NVIDIA inference endpoint and extracts JSON arrays of candidate names from model output.
- `naming_rules.py` — The naming skill: taxonomy, construction techniques, quality filters (`passes_quality_filter`), LLM system prompt (`build_llm_system_prompt`), and variations builder (`build_variations`).
- `domain_check.py` — Async domain availability checker using Verisign RDAP (`rdap.verisign.com`). `check_many` runs parallel checks with `httpx.AsyncClient`.
- `static/index.html` — Minimal frontend UI that calls `/generate` and `/variations` and renders results.
- `requirements.txt` — Python package list needed to run the project.

## How it works (request flow)
1. The user types a description in the frontend and clicks "Generate names".
2. Frontend sends POST `/generate` with `description` and optional `desired_name`.
3. `main.generate` calls `llm.generate_names(description, count=28)` to get raw candidates from the model.
4. Results are de-duplicated and filtered with `naming_rules.passes_quality_filter` to remove unsuitable names.
5. Optionally the user's desired name is inserted at the top (after normalization).
6. `domain_check.check_many(filtered)` queries Verisign RDAP for each candidate: 200 => `taken`, 404 => `available`, others => `unknown`.
7. Results are sorted (available first, unknown second, taken last), and the JSON response is returned to the frontend.

Variations: when a taken name is chosen, the frontend can call POST `/variations` with a `name`; the server builds prefixed/suffixed variations via `build_variations` and checks their availability.

## Configuration / Secrets
- The LLM client expects an environment variable `NVIDIA_API_KEY`. Create a `.env` file in the project root with:

```
NVIDIA_API_KEY=your_key_here
```

Replace `your_key_here` with your actual API key.

llm.py uses:
- `base_url="https://integrate.api.nvidia.com/v1"`
- `MODEL = "nvidia/nemotron-3-ultra-550b-a55b"`

If you use a different provider or model, update `llm.py` accordingly.

## Setup and Run (Development)
1. Create and activate a virtual environment (example for Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Add your `NVIDIA_API_KEY` to a `.env` file (see above).

4. Start the server with uvicorn:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

5. Open a browser to `http://localhost:8000/` and use the frontend UI.

## API Endpoints
- `GET /` — serves `static/index.html`.
- `GET /health` — simple health check returning `{ "status": "ok" }`.
- `POST /generate` — body: `{ "description": <string>, "desired_name": <string|null> }`.
  Returns `{ "results": [ { "name": "...", "status": "available|taken|unknown", ... } ] }`.
- `POST /variations` — body: `{ "name": <string> }`. Returns a small list of variation candidates and their statuses.

## Domain checking details
- `domain_check.py` queries Verisign RDAP at `https://rdap.verisign.com/com/v1/domain/{name}.com`.
- Interprets HTTP 200 as `taken`, 404 as `available`.
- Timeouts and network errors yield `unknown`.

## Notes & Considerations
- The LLM output is parsed permissively: `llm._extract_names` first tries to parse the whole response as JSON; if that fails it searches for the first `[...]` block.
- `naming_rules` enforces strict character rules: only letters, length between 4 and 12, and blocks troublesome letter clusters.
- The frontend links to a registrar (Namecheap) to let users claim open names.
- If you plan to deploy, secure the `NVIDIA_API_KEY` (do not embed it in client code), consider rate limits, and restrict public access or add authentication.

## Troubleshooting
- If the frontend shows "Couldn't reach the generator", check the terminal running `uvicorn` for tracebacks.
- If LLM requests fail, verify `NVIDIA_API_KEY` and network connectivity to `integrate.api.nvidia.com`.
- If many results return `unknown`, RDAP requests may be timing out; consider increasing the HTTP timeout in `domain_check.check_one`.

## Tests & Next Steps
- There are no automated tests in this repo. Recommended small tests:
  - Unit tests for `naming_rules.passes_quality_filter` and `build_variations`.
  - Integration test for `/generate` mocking LLM and RDAP responses.

## File list (quick)
- main.py
- llm.py
- naming_rules.py
- domain_check.py
- requirements.txt
- static/index.html

---
Generated by tooling to capture the repository's usage and build steps.
