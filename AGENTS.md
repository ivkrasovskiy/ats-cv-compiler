# Agent Instructions (LLM Contract)

## Purpose
This file defines how LLM agents (Codex/ChatGPT/local) must operate in this repository.
The agent is a coding assistant, not a product owner.

## Prime Directive
Maintain a **CV compiler** with two interfaces:
- **CLI** (`uv run cv ...`) — deterministic pipeline, ATS-safe rendering, optional LLM assistance
- **Web UI** (`app/`) — FastAPI backend + React/TypeScript frontend served at `http://localhost:8000`

Both interfaces share the same core pipeline (`src/cv_compiler/`). The web UI is a first-class citizen, not a prototype.

## Non-Negotiable Rules
1. **No fabrication**: never introduce facts, metrics, employers, titles, dates, or claims not present in canonical data.
2. **Determinism first**: generic build must not require LLMs or network access.
3. **ATS-safe output**: no tables, no multi-column, no icons, no text boxes in the default template.
4. **No vector DB/RAG**. Use deterministic scoring and keyword matching.
5. **Minimal dependencies**. Prefer stdlib; justify every new dependency.

## Project Tooling

### Python (CLI + backend)
- Use **uv** for dependencies and scripts.
- Use **ruff** for linting and formatting (`ruff check`, `ruff format`).
- Prefer the Astral stack; do not introduce black/isort/flake8 alongside ruff.
- Tests: `uv run pytest`

### Frontend (`app/frontend/`)
- Framework: **React 18 + TypeScript + Vite**
- Styling: **Tailwind CSS**
- Data fetching: **TanStack Query**
- Tests: **Vitest + Testing Library** (`npm --prefix app/frontend run test`)
- Build check: `npm --prefix app/frontend run build`

## Code Quality Standards
- Python 3.11+. Type hints required for public functions.
- Small, testable modules; avoid heavy abstractions.
- Add/adjust unit tests for any non-trivial logic.
- Frontend components should have smoke tests at minimum.

## Web App Architecture
```
app/
  backend/          ← FastAPI app (API layer only — no business logic)
    api/            ← route modules (build, config, doctor, files, form, health, lint)
    services/       ← file_service, build_service
    tests/          ← pytest tests for API routes
  frontend/         ← React SPA
    src/
      api/client.ts ← all fetch calls (single source of truth)
      components/   ← shared UI components
      pages/        ← page-level components (DataBrowser, OutputPage, JobsPage, …)
      hooks/        ← custom React hooks
```

The backend forwards requests to `src/cv_compiler/` — it does not re-implement pipeline logic.

## Change Management
When modifying behavior:
1. Update schema/validators if inputs change.
2. Update lint rules if output constraints change.
3. Update `app/frontend/src/api/client.ts` if API surface changes.
4. Ensure `cv lint` remains strict and meaningful.

## Implementation Preferences
- Pipeline: parse → validate → select → (optional rewrite) → render → lint
- Keep selection deterministic and explainable.
- LLM integration uses a provider interface with:
  - local model option
  - external API option
  - explicit prompts stored in `prompts/`

## Prompts & LLM Outputs
- Prompts MUST contain:
  - explicit "do not invent facts" instruction
  - constraints on length and style
- LLM outputs MUST be attributable to inputs.

## What to Ask vs What to Decide
- If requirements are ambiguous, prefer conservative defaults that protect ATS safety and determinism.
- If a change expands core pipeline behavior significantly, confirm before proceeding.

## Definition of Done
A change is done when:
- `ruff check` + `ruff format` pass (Python)
- Python unit tests pass (`uv run pytest`)
- Frontend tests pass (`npm --prefix app/frontend run test`)
- `cv lint` passes on example data
- Output remains ATS-safe

## Repo Navigation Workflow

For non-trivial debugging/refactors:
1. Regenerate the project index:
   - `uv run python scripts/project_index.py` → `docs/PROJECT_INDEX.md`
2. Generate a per-file task checklist:
   - `uv run python scripts/task_index.py --goal "..."` → `tmp/task_index.md`
3. Execute tasks top-to-bottom, updating the checklist as you go.
4. When done: `uv run python scripts/task_index.py --clear`

## AI Assistant Files
- `CLAUDE.md` — instructions for Claude Code users
- `GEMINI.md` — instructions for Gemini CLI users

Both contain onboarding sequences, key commands, file format references, and rules.

## Non-Technical User Guidance
- Suggest `uv run cv doctor` before any manual debugging.
- Direct them to edit only: `data/`, `jobs/`, `config/llm.env`.
- Never ask them to edit `pyproject.toml` or run Python scripts directly.
- Seed `data/` from `examples/basic/data/` if it doesn't exist yet.
- Onboarding is handled by `onboard.sh`.
- The web UI is available via `uv run --extra app cv-app` → `http://localhost:8000`.
