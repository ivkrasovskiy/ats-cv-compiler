# ats-cv-compiler
A CLI tool that compiles structured career data into ATS-safe CV PDFs, with optional job-specific tailoring using LLMs.
It also emits a deterministic Markdown CV that serves as the PDF source.

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
- `uv run cv build --example basic --no-pdf` (Markdown only)
- `uv run cv build --example basic --from-markdown examples/basic/out/cv_generic.md`

Optional:
- `uv run cv build --example basic --job examples/basic/jobs/backend_engineer.md`

Profile field change:
- `profile.md` now uses `about_me` (string paragraph) instead of `summary` (bullet list).

## LLM (optional, not required)

The default build is deterministic and does not require any LLM.

When enabled, the LLM is used only for constrained derivation of experience bullets from projects
(never as a source of truth).

Planned configuration (via environment variables):
- `CV_LLM_MODE`: `api` (endpoint) or `offline` (manual copy/paste)
- `CV_LLM_BASE_URL`: an OpenAI-compatible HTTP endpoint (e.g. a local server)
- `CV_LLM_MODEL`: model name/id served by that endpoint
- `CV_LLM_API_KEY`: optional (depends on your endpoint)
- `CV_LLM_TIMEOUT_SECONDS`: request timeout (default: 300)

Usage:
- `uv run cv build --example basic --llm openai`

Optional config file:
- Create `config/llm.env` with the same variables:
  - `CV_LLM_MODE=api`
  - `CV_LLM_BASE_URL=http://127.0.0.1:1234`
  - `CV_LLM_MODEL=lmstudio-community/qwen3-8b-mlx`
  - `CV_LLM_TIMEOUT_SECONDS=300`

Generated artifacts:
- LLM outputs are written to `data/experience/llm_<id>.md` (or `examples/.../data/experience/` for examples).
- If a user creates `data/experience/user_<id>.md`, it will be used instead and never overwritten.
  - IDs are deterministic: `exp_<company>_<start>` (derived from project data).
- Build always emits `out/cv_<name>.md` alongside the PDF (or alone with `--no-pdf`).

Regenerate experience overrides:
- `uv run cv build --llm openai --experience-regenerate`
- This renames active user overrides to `user_<id>.<unix_ts>.md` and re-runs LLM generation.

Manual/offline LLM mode:
- If `CV_LLM_MODE=offline`, the build writes `out/llm_request.json` and expects
  `out/llm_response.json`. Paste the model response (raw YAML/JSON or full OpenAI-style JSON)
  into the response file and re-run the build.
- If `CV_LLM_MODE` is not set, the CLI prompts once and stores it in `config/llm.env`.

Project requirements for LLM:
- Projects should include `company`, `role`, `start_date`, and optional `end_date` in frontmatter.
- LLM bullets must use only facts and metrics explicitly present in project data.

Prompt and templates:
- `prompts/experience_prompt.md`
- `prompts/experience_templates.yaml`

Structured output:
- The LLM request uses OpenAI-style `response_format` with a JSON schema by default.

Model sizing guidance (rule of thumb):
- Bullet rewriting is a relatively small task; a small instruct model is usually sufficient.
- Prefer a model that can reliably follow “do not invent facts” constraints; start around the 7B-class
  if you’re unsure, and go smaller only if quality is acceptable for your data.
