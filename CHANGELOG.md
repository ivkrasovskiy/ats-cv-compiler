# Changelog

## [1.0.0] — Unreleased

### Added
- **URL labels in PDF contact line**: profile links with a `label` field now render as
  `LinkedIn` (blue hyperlink) instead of the raw URL in both PDF and Markdown output.
  Backward-compatible: bare URLs still render correctly via the `--from-markdown` path.
- **LLM-based skill selection** (`select_skills`): when `--llm agents` is used with a job,
  an agent now selects which skills to include in the CV using fuzzy scoring hints
  (`exact_matches`, `fuzzy_matches`). Synonyms like `PyTorch`/`torch` and `Spark`/`pyspark`
  are no longer silently excluded.
- **Fuzzy skill scoring** in deterministic fallback: `_deterministic_skill_filter` now uses
  substring matching so synonym aliases pass through even without AI (score = `exact*2 + fuzzy`).
- `prompts/skills_select_prompt.md`: new prompt for the skill selection agent.
- `LLM_SKILL_SELECT_FAILED` lint issue code; treated as an LLM failure marker in the web GUI
  auto-build fallback chain.

### Added
- **Web GUI** (`app/`) — local browser interface for non-technical users
  - FastAPI backend (`app/backend/`) with SSE build streaming, file CRUD, doctor, lint
  - React + Vite + TypeScript frontend (`app/frontend/`) with 5 pages
  - Playwright E2E tests (`app/e2e/`) with 4 test suites
  - MCP Playwright server config for agent-driven browser testing
  - GitHub Actions CI workflow (backend pytest, frontend vitest+tsc, ruff, e2e)
- `uv run --extra app cv-app` launches the GUI at http://localhost:8000

## [0.1.0] — Initial release

### Added
- CLI (`uv run cv build`) generating ATS-safe PDFs from YAML/Markdown career data
- Deterministic content selection with optional job targeting
- LLM bullet rewriting (OpenAI-compatible, Codex, agent chain)
- PDF ingestion (`uv run cv to_mds_from_pdf`)
- Doctor and lint commands
