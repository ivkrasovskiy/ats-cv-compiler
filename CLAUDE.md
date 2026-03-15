# Claude Code — Project Guide

This repo is **ats-cv-compiler**: a CLI tool that turns structured Markdown/YAML career data
into ATS-safe CV PDFs. No web server, no database — just files and a build command.

---

## Onboarding new users

If `data/` does not exist, or `data/profile.md` contains the name "Alex Example",
**greet the user warmly** and offer to walk them through setup one step at a time.

Do **not** dump all steps at once — ask one question, wait for confirmation, then proceed.

**Start by asking:** "Do you have an existing CV as a PDF file?"

### Path A — existing PDF (fastest)
1. Copy the PDF to `data/cv.pdf`
2. Run: `uv run cv to_mds_from_pdf` — this creates all data files automatically
3. Review and edit the generated files in `data/` for accuracy
4. Run: `uv run cv build --job false`
5. Open `out/cv_generic.pdf`

### Path B — from scratch
1. Copy examples: `cp -r examples/basic/data data`
2. Edit `data/profile.md` — name, email, headline, links, about_me
3. Edit `data/skills.md` — skill categories and items
4. Edit `data/education.md` — institution, degree, dates
5. Add experience files to `data/experience/` — one `.md` file per employer
6. Add project files to `data/projects/` — one `.md` file per project
7. Run: `uv run cv build --job false`
8. Open `out/cv_generic.pdf`

### Step for both paths — target a specific job (optional but recommended)
Once they have a working generic CV, ask:
"Do you have a specific job you're applying to?"
- If yes: create `jobs/` directory, save the job description as `jobs/<company>.md`
- Then run: `uv run cv build --job jobs/<company>.md`
- This produces a CV tailored to that job's keywords and requirements
- For AI-written bullets: `uv run cv build --llm agents --job jobs/<company>.md`

After each step, confirm the user is ready before moving on.

---

## Key commands

| Command | What it does |
|---|---|
| `uv run cv build --job false` | Build a generic PDF (no job targeting) |
| `uv run cv build --job jobs/myjob.md` | Build targeted for a specific job |
| `uv run cv build --llm agents --job jobs/myjob.md` | Use Claude to write bullets |
| `uv run cv doctor` | Diagnose why build is failing |
| `uv run cv lint` | Validate data files |
| `uv run cv build --example basic` | Try the bundled example (safe to run) |
| `uv run --extra app cv-app` | Start the local web GUI → http://localhost:8000 |

---

## File format cheat sheet

All data files use **YAML frontmatter** (between `---` markers). No raw prose below the
frontmatter — the pipeline reads only the frontmatter fields.

**`data/profile.md`** — required fields: `id`, `name`, `headline`, `location`, `about_me`, `links`

**`data/skills.md`** — required: `id`, `categories` (list of `{name, items[]}`)

**`data/education.md`** — required: `id`, `entries` (list of `{institution, degree}`)

**`data/experience/*.md`** — one file per employer
- Required: `id`, `company`, `title`, `start_date`, `tags[]`, `bullets[]`
- File naming: prefix `user_` (your edits) or `llm_` (LLM-generated)
- Example: `data/experience/user_acme_2022.md`

**`data/projects/*.md`** — one file per project
- Required: `id`, `name`, `tags[]`, `bullets[]`

**`jobs/*.md`** — optional job description files (used for targeted CV builds)
- Optional frontmatter: `id`, `title`, `keywords[]`
- Free text below frontmatter: the job description

See `examples/basic/data/` for working examples of every file type.

---

## Rules for Claude Code in this repo

- **NEVER** invent metrics, employers, titles, dates, or numbers not present in the user's data files.
- **NEVER** modify files in `out/` or `tmp/` (generated artifacts).
- **ALWAYS** show corrected YAML to the user before writing it.
- Run `uv run ruff check src/ && uv run ruff format src/` before committing Python changes.
- Run `uv run cv lint` after editing any data file.
- `data/` contains private career information — never log or summarize it unless asked.
- When the user seems stuck, suggest: `uv run cv doctor`
- When editing experience/project bullets, preserve every fact; only improve phrasing.

---

## Repo layout (quick reference)

```
data/               ← your career data (edit these)
  profile.md
  skills.md
  education.md
  experience/       ← one .md per employer (user_* or llm_* prefix)
  projects/         ← one .md per project
jobs/               ← job descriptions for targeted builds
out/                ← generated CVs (do not edit)
templates/          ← PDF layout templates
prompts/            ← AI instructions for bullet rewriting
examples/basic/     ← safe working example (read-only reference)
config/llm.env      ← LLM settings (optional)
src/cv_compiler/    ← Python source
onboard.sh          ← bootstrap script for new users
GEMINI.md           ← project guide for Gemini CLI users
```

---

## Common problems and fixes

| Symptom | Fix |
|---|---|
| `Missing required file: data/profile.md` | Run `uv run cv doctor` or copy from examples |
| `Failed to load data` YAML parse error | Run `uv run cv doctor` — it will show which file and line |
| Build output looks wrong | Run `uv run cv lint` to check for constraint violations |
| Claude bullets sound invented | Check that `data/projects/` files have accurate `bullets[]` |
| `uv: command not found` | Run `./onboard.sh` — it installs uv automatically |
