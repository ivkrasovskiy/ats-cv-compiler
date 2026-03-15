# Changelog

## [1.0.0] — Unreleased

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
