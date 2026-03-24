# Changelog

All notable changes are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.2.0] — 2026-03-24

### Fixed

- **Agent Terminal keyboard input** — typing in the terminal now works correctly, including
  interactive prompts from Gemini ("Do you trust this folder?") and Claude.

- **Agent Terminal connection** — the terminal now connects properly when the app is accessed
  via `localhost:5173` (the normal way to open the app with `bash start.sh`).

- **Terminal clears on restart** — stopping and starting the terminal no longer shows output
  from the previous session.

---

## [1.1.0] — 2026-03-24

### Added

- **Agent Terminal (`/agent`)** — xterm.js embedded terminal in the browser; connects over
  WebSocket to a PTY bridge that spawns `claude` or `gemini` interactively. Full ANSI color,
  resize support, and provider selection.

- **Self-Repair system** — background service polls `logs/backend.log` for 4xx/5xx errors,
  classifies them with the configured CLI (`-p` mode), and reacts based on `CV_REPAIR_MODE`:
  - `silent` (default): auto-applies fix via CLI + `git stash` safety net; backend reloads; frontend polls `/api/health` and reloads.
  - `approval`: shows fix proposal toast with Approve/Dismiss buttons.
  - `inform`: shows traceback toast with "Fix with AI →" link to Agent Terminal.

- **Error logging middleware** — `ErrorLoggingMiddleware` captures all 4xx/5xx responses and
  exceptions to `logs/backend.log` (JSON lines, rotating 5 MB × 3 files).

- **Frontend error boundary** — catches React render errors, POSTs to `/api/client-errors`,
  shows a friendly "Reload page" UI.

- **`/api/repair/*` endpoints** — SSE stream, status, apply, dismiss, GitHub issue creation.

- **`/api/client-errors`** — receives frontend JS errors, logs to `logs/frontend.log`.

- **`CV_REPAIR_MODE` config key** — selectable in Gen Config → Auto-Repair Mode radio group.
  Default: `silent`. Existing installs without the key default to `silent`.

- **GitHub issue creation** — "Create GitHub Issue" button in repair toast (shown when `gh`
  CLI is on PATH).

---

## [1.0.0] — 2026-03-24

### Added

- **Web GUI** (`app/`) — local browser interface for non-technical users
  - FastAPI backend with SSE build streaming, file CRUD, doctor, lint, PDF ingest
  - React + Vite + TypeScript frontend with 5 pages (Dashboard, Data, Jobs, Output, Build)
  - Form-based editor for profile, experience, projects, and skills with validation
  - Build progress tracking with live log streaming
  - PDF and Markdown viewer for generated CVs
  - Playwright E2E tests and GitHub Actions CI
  - `uv run --extra app cv-app` → http://localhost:8000

- **Two-line CV header** — headline + location on line 1, email + links on line 2;
  improves ATS parsing and PDF readability.

- **URL labels in PDF contact line** — profile links with a `label` render as a blue
  hyperlink (`LinkedIn`) instead of the raw URL. Bare URLs still render correctly.

- **LLM-based skill selection** (`select_skills`) — when `--llm agents` is used, an agent
  selects skills using fuzzy scoring hints (`exact_matches`, `fuzzy_matches`). Synonyms
  like `PyTorch`/`torch` are no longer silently excluded. Capped at 25 skills via prompt
  guidance, JSON schema `maxItems`, and a hard parser guard.

- **Fuzzy skill scoring** in deterministic fallback — substring matching so synonym aliases
  pass through without AI.

- **`make update`** — pulls latest code from `origin/main` without touching `data/`,
  `jobs/`, or `config/`; re-installs deps on success; prints actionable help on conflict.

- **`start.sh`** — port conflict detection with PID and `kill` command; polls
  `/api/health` before launching the frontend to eliminate ECONNREFUSED noise.

- `prompts/skills_select_prompt.md` — new prompt for the skill selection agent.
- `LLM_SKILL_SELECT_FAILED` lint issue code for the web GUI auto-build fallback chain.

### Fixed

- **Gemini CLI PDF ingest returning 500** — `gemini -p` requires a value argument; the
  prompt is now passed as `gemini -p "<prompt>"` instead of via stdin.

- **`[Telegram](url)` rendering as raw Markdown text in PDF** — old single-line contact
  format (headline + links on one line) is now detected and rendered correctly alongside
  the new two-line format.

- **Email rendering as `[Email](mailto:…)` in PDF** — `mailto:` links are now normalised
  to the `email` field at ingest time and rendered as plain text.

- **"Generate CV" from Generated CVs tab producing cv_generic** — `jobPathForBase` now
  handles both `cv_job_<name>` and `cv_<name>` file naming patterns.

- **CV download returning 404** — `cvFileName()` checks both `cv_job_<name>.pdf` and
  `cv_<name>.pdf` so downloads and previews work regardless of job file `id` format.

### Tests

- CLI ingest prompt modes: stdin (Claude), arg (Gemini), non-zero exit, command not found.

## [0.1.0] — Initial release

### Added
- CLI (`uv run cv build`) generating ATS-safe PDFs from YAML/Markdown career data
- Deterministic content selection with optional job targeting
- LLM bullet rewriting (OpenAI-compatible, Codex, agent chain)
- PDF ingestion (`uv run cv to_mds_from_pdf`)
- Doctor and lint commands
