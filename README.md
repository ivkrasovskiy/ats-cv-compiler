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

Note: the build pipeline is currently scaffolded (signatures + tests) but not implemented yet.
