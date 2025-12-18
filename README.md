# ats-cv-compiler
A CLI tool that compiles structured career data into ATS-safe CV PDFs, with optional job-specific tailoring using LLMs.

cv-compiler is an open-source CLI tool that turns structured career data (Markdown/YAML) into clean, ATS-compatible CV PDFs.

It supports:

 - a single source of truth for your experience and projects

 - deterministic CV generation without LLMs

 - optional job-specific tailoring using local or external LLMs

 - strict formatting for compatibility with automated screening systems

## Setup (uv)

- `uv venv`
- `uv sync --dev`

## Try the example dataset

- `uv run cv --help`
- `uv run cv build --example basic`

Optional:
- `uv run cv build --example basic --job examples/basic/jobs/backend_engineer.md`

## LLM (optional, not required)

The default build is deterministic and does not require any LLM.

When enabled later, the LLM will be used only for constrained rewriting/condensing of already-selected
bullets (never as a source of truth).

Planned configuration (via environment variables):
- `CV_LLM_BASE_URL`: an OpenAI-compatible HTTP endpoint (e.g. a local server)
- `CV_LLM_MODEL`: model name/id served by that endpoint
- `CV_LLM_API_KEY`: optional (depends on your endpoint)

Model sizing guidance (rule of thumb):
- Bullet rewriting is a relatively small task; a small instruct model is usually sufficient.
- Prefer a model that can reliably follow “do not invent facts” constraints; start around the 7B-class
  if you’re unsure, and go smaller only if quality is acceptable for your data.
