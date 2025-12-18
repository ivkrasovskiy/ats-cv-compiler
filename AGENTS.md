# Agent Instructions (LLM Contract)

## Purpose
This file defines how LLM agents (Codex/ChatGPT/local) must operate in this repository.
The agent is a coding assistant, not a product owner.

## Prime Directive
Maintain a **CV compiler**:
- CLI-first
- deterministic pipeline by default
- ATS-safe rendering
- optional LLM assistance with strict non-fabrication rules

Do NOT turn this into a web app or “AI agent platform”.

## Non-Negotiable Rules
1. **No fabrication**: never introduce facts, metrics, employers, titles, dates, or claims not present in canonical data.
2. **Determinism first**: generic build must not require LLMs or network access.
3. **ATS-safe output**: no tables, no multi-column, no icons, no text boxes in the default template.
4. **No frontend for MVP** unless explicitly requested in an issue/task.
5. **No vector DB/RAG for MVP**. Use deterministic scoring and keyword matching.
6. **Minimal dependencies**. Prefer stdlib; justify every new dependency.

## Project Tooling
- Use **uv** for dependencies and scripts.
- Use **ruff** for linting and formatting (`ruff check`, `ruff format`).
- Prefer the Astral stack; do not introduce black/isort/flake8 alongside ruff.

## Code Quality Standards
- Python 3.11+.
- Type hints required for public functions.
- Pydantic (or equivalent) for schema validation if used in the codebase.
- Small, testable modules; avoid heavy abstractions.
- Add/adjust unit tests for any non-trivial logic.

## Change Management
When modifying behavior:
1. Update schema/validators if inputs change.
2. Update lint rules if output constraints change.
3. Update README/REQUIREMENTS if user-facing behavior changes.
4. Ensure `cv lint` remains strict and meaningful.

## Implementation Preferences
- Prefer a pipeline:
  - parse → validate → select → (optional rewrite) → render → lint
- Keep selection deterministic and explainable.
- LLM integration should be a provider interface with:
  - local model option
  - external API option
  - explicit prompts stored in-repo

## Prompts & LLM Outputs
- Prompts MUST contain:
  - explicit “do not invent facts” instruction
  - constraints on length and style
- LLM outputs MUST be attributable to inputs:
  - preserve internal IDs or provide a mapping (even if not shown in final CV)

## What to Ask vs What to Decide
- If requirements are ambiguous, prefer conservative defaults that protect ATS safety and determinism.
- If a change expands scope (UI, database, agents), stop and request explicit approval in an issue/task.

## Definition of Done
A change is done when:
- ruff passes
- unit tests pass
- `cv lint` passes
- output remains ATS-safe
- the change is documented where appropriate
