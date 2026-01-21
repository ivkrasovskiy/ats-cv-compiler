# CV Compiler Requirements

## Problem
Maintaining and tailoring CVs is repetitive, error-prone, and often breaks ATS parsing.
This project treats a CV as compiled output:
- Career data is stored as structured, version-controlled files.
- CVs are generated deterministically.
- LLMs are optional helpers for selection/rewriting, not the source of truth.

## Goals
1. **Single source of truth** for experience/projects/skills in a structured, diff-friendly format.
2. **ATS-safe output** (PDF by default) that parses reliably in automated systems.
3. **Fast targeting**: generate a job-specific CV from the same source data.
4. **Optional LLM assistance**: content selection + bullet rewriting without inventing facts.
5. **Reproducible CLI** workflow suitable for local usage and CI.

## Non-Goals
- No hosted SaaS, accounts, or cloud backend.
- No GUI required for MVP (CLI-first).
- No “autonomous agents” that can change schema or invent content.
- No heavy RAG/vector DB for MVP (dataset is small; deterministic scoring is enough).

## Core Concepts
- **Canonical data**: structured entries describing experience/projects/skills.
- **Job spec**: a job description + constraints for tailoring.
- **Template**: a rendering layout producing ATS-safe output.

## Inputs

### 1) Canonical data (required)
Stored in `data/` as Markdown files with YAML frontmatter.

Minimum required entities:
- `profile.md` (name, headline, location, links, about_me)
- `experience/*.md`
- `projects/*.md`
- `skills.md`
- `education.md` (optional but recommended)

Frontmatter fields MUST be validated (schema enforced).
Body text MAY contain extra notes, but anything rendered must be derivable from validated fields.

### 2) Job description (optional)
Stored in `jobs/*.md` (or `.txt`) containing:
- raw job description text
- optional constraints (length, emphasis, excluded topics, keyword priorities)

### 3) LLM instructions (optional)
A user-provided instruction file (e.g. `instructions/llm.md`) that:
- sets tone and constraints
- never overrides factual truth
- never permits invented metrics/claims

## Outputs
### Required outputs (MVP)
- `out/cv_generic.pdf`
- `out/cv_<job>.pdf` (when job spec provided)
- `out/cv_generic.md` (markdown source used for PDF rendering)
- `out/cv_<job>.md` (when job spec provided)

### Optional outputs (post-MVP)
- `.docx` export (ATS-friendly)
- JSON debug artifacts (selected bullets, scoring, keyword coverage)

## CLI Interface (MVP)
Command names are illustrative; exact flags may evolve, but behavior must match.

- `cv build`
  - Generates generic CV from canonical data without LLM.
- `cv build --job jobs/<file> [--llm <provider>]`
  - Generates targeted CV using deterministic selection.
  - If `--llm` is provided, LLM may rewrite/condense bullets and/or assist ranking.
- `cv lint`
  - Validates schema and enforces ATS constraints.
- `cv explain --job jobs/<file>`
  - Shows why items were selected (scores, matched keywords, rules triggered).
- `cv to_mds_from_pdf`
  - Extracts a PDF CV into canonical Markdown files under `data/`.

## Deterministic Selection (MVP)
Selection must be deterministic given the same inputs:
- Base scoring from:
  - tag overlap (entry tags vs job keywords)
  - keyword overlap (job text vs entry text)
  - recency (newer roles/projects slightly favored)
  - role importance (explicit weights allowed)
- Hard rules:
  - no fabrication: only rewrite existing facts
  - limit bullets/section to fit target length

## LLM Behavior (MVP)
LLM is optional and constrained:
- Allowed:
  - rewrite bullets for clarity/compactness
  - reduce redundancy
  - map content to template slots
  - derive experience bullets from project data (no new facts)
- Disallowed:
  - adding new facts, numbers, employers, titles, dates
  - “guessing” metrics
  - changing chronology
- Every LLM run MUST:
  - include a “no fabrication” instruction
  - produce outputs traceable to original entries (e.g., via internal IDs)

## ATS & Formatting Constraints (Non-Negotiable)
- Single-column layout (MVP).
- No tables, text boxes, icons, or multi-column grids.
- Selectable text; embedded fonts.
- Simple headings; consistent structure.
- Avoid unusual Unicode that breaks parsers.
- Output must pass `cv lint` checks.

## Rendering
Rendering backend is implementation-defined but must be:
- reproducible on macOS/Linux
- automated (no manual editor steps)
- template-driven

## Tooling & Repo Standards
- Python tooling uses **uv** for dependency management.
- Linting/formatting uses **ruff** (including `ruff format`).
- CI should run: `uv run cv lint` and unit tests.

## Acceptance Criteria (MVP)
1. A user can add/edit entries in `data/` and regenerate a valid generic PDF.
2. A user can provide a job description and generate a targeted PDF without manual editing.
3. Output PDFs are ATS-safe according to repository lint rules.
4. Optional LLM mode improves concision/keyword alignment without inventing facts.
5. All behavior is reproducible via CLI and passes CI checks.
