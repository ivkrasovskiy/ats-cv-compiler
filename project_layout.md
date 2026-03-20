ats-cv-compiler/          # project root
  data/                   # your canonical CV data (edit these)
    profile.md
    skills.md
    education.md
    experience/           # one .md per employer (user_* or llm_* prefix)
    projects/             # one .md per project
    experience_summary.md # optional one-time summary (generated with --experience-summary)
  jobs/                   # job descriptions for targeted builds (one .md per job)
  out/                    # generated CVs — do not edit
  tmp/                    # temporary working files — git-ignored
  templates/              # PDF layout (fonts, spacing, sections)
  prompts/                # AI instructions for bullet rewriting and skill highlighting
    skills_select_prompt.md  # skill selection prompt (which skills to include in CV)
    agents/               # prompts used by the --llm agents multi-agent pipeline
  examples/
    basic/                # bundled working example (safe reference, read-only)
  config/
    llm.env               # LLM settings (model, API key, timeouts) — git-ignored
    llm.env.example       # template for llm.env
  docs/
    ENTITIES.md           # public API signatures (data model, pipeline, providers)
    PROJECT_INDEX.md      # auto-generated import graph (uv run python scripts/project_index.py)
  scripts/
    project_index.py      # regenerates docs/PROJECT_INDEX.md
    task_index.py         # generates tmp/task_index.md for tracking work in progress
    onboard_test.sh       # integration test script (runs inside Docker)
    check_projects.py     # validate project .md files
    check_llm_drafts.py   # validate LLM experience draft JSON
  src/
    cv_compiler/
      cli.py              # CLI entry point (cv build, cv lint, cv doctor, cv explain, ...)
      pipeline.py         # build pipeline: parse → select → rewrite → render → lint
      doctor.py           # diagnostic checks (uv run cv doctor)
      types.py            # shared enums: Severity, LintIssue
      schema/             # dataclasses for validated CV entities
      parse/              # YAML frontmatter parsing and data loaders
      select/             # deterministic scoring and content selection
      render/             # Markdown and PDF rendering
      lint/               # ATS constraint checks
      llm/                # LLM provider interfaces and implementations
        base.py           # LLMProvider protocol, BulletRewriteRequest/Result, ExperienceDraft
        openai.py         # OpenAI-compatible HTTP provider (with retry on 429/5xx)
        chain.py          # AgentChainProvider: 5-agent pipeline via claude/gemini -p
        chain_config.py   # AgentChainConfig (env-driven)
        codex.py          # CodexExecProvider (Codex CLI)
        manual.py         # ManualProvider (offline copy/paste mode)
        config.py         # LLMConfig
        experience.py     # helpers for generating experience entries from projects
        skills.py         # helpers for skill highlighting
        summary.py        # helpers for experience summary paragraph
        bullet_polish.py  # helpers for bullet rewriting
        job_analysis.py   # helpers for job analysis agent
      ingest/
        pdf_ingest.py     # extract a PDF CV into canonical Markdown files
      tools/
        project_check.py  # project file validation helpers
        llm_draft_check.py# LLM draft validation helpers
  tests/                  # unit and integration tests (uv run pytest tests/ -q)
  onboard.sh              # bootstrap script for new users (bash onboard.sh)
  Dockerfile.onboard-test # Docker image for CI onboarding tests
  CLAUDE.md               # project guide for Claude Code users
  GEMINI.md               # project guide for Gemini CLI users
  AGENTS.md               # coding-agent contract (rules, workflow, standards)
  README.md
  REQUIREMENTS.md
  project_layout.md       # this file
  pyproject.toml
