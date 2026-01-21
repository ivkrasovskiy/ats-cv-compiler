# Main Entities (Signature-Only)

This document describes the public-ish entities we expect in the MVP, focusing on *signatures* (names, parameters, return types) rather than implementation.

## Data model (`src/cv_compiler/schema/models.py`)

- `Link(label: str, url: str)`
- `Profile(id: str, name: str, headline: str, location: str, email: str | None, links: tuple[Link, ...], about_me: str, source_path: Path | None = None)`
- `ExperienceEntry(id: str, company: str, title: str, location: str | None, start_date: str, end_date: str | None, tags: tuple[str, ...], bullets: tuple[str, ...], source_path: Path | None = None)`
- `ProjectEntry(id: str, name: str, company: str | None, role: str | None, start_date: str | None, end_date: str | None, tags: tuple[str, ...], bullets: tuple[str, ...], source_path: Path | None = None)`
- `SkillsCategory(name: str, items: tuple[str, ...])`
- `Skills(id: str, categories: tuple[SkillsCategory, ...], source_path: Path | None = None)`
- `EducationEntry(institution: str, degree: str, location: str | None, start_date: str | None, end_date: str | None)`
- `Education(id: str, entries: tuple[EducationEntry, ...], source_path: Path | None = None)`
- `CanonicalData(profile: Profile, experience: tuple[ExperienceEntry, ...], projects: tuple[ProjectEntry, ...], skills: Skills, education: Education | None)`
- `JobSpec(id: str, title: str | None, raw_text: str, keywords: tuple[str, ...], source_path: Path | None = None)`

Notes:
- Every renderable entity has an `id` and may carry `source_path` for traceability.
- Dates are represented as strings for now; validation/parsing is an implementation detail.

## Parsing (`src/cv_compiler/parse/*`)

- `parse_markdown_frontmatter(path: Path) -> MarkdownDocument` (`src/cv_compiler/parse/frontmatter.py`)
  - `MarkdownDocument(frontmatter: Mapping[str, Any], body: str, source_path: Path)`
- `load_canonical_data(data_dir: Path) -> CanonicalData` (`src/cv_compiler/parse/loaders.py`)
- `load_job_spec(path: Path) -> JobSpec` (`src/cv_compiler/parse/loaders.py`)

## Selection (`src/cv_compiler/select/*`)

- `select_content(data: CanonicalData, job: JobSpec | None) -> SelectionResult` (`src/cv_compiler/select/selector.py`)
- `SelectionDecision(item_id: str, score: float, matched_keywords: tuple[str, ...], reasons: tuple[str, ...])` (`src/cv_compiler/select/types.py`)
- `SelectionResult(selected_experience_ids: tuple[str, ...], selected_project_ids: tuple[str, ...], decisions: tuple[SelectionDecision, ...])` (`src/cv_compiler/select/types.py`)

## Optional LLM rewriting (`src/cv_compiler/llm/*`)

- `LLMProvider` protocol (`src/cv_compiler/llm/base.py`)
  - `name: str`
  - `rewrite_bullets(items: Sequence[BulletRewriteRequest], instructions: str | None) -> Sequence[BulletRewriteResult]`
  - `generate_experience(projects: Sequence[ProjectEntry], job: JobSpec | None) -> Sequence[ExperienceDraft]`
- `BulletRewriteRequest(item_id: str, bullets: tuple[str, ...], job_keywords: tuple[str, ...])`
- `BulletRewriteResult(item_id: str, bullets: tuple[str, ...])`
- `ExperienceDraft(id: str, role: str | None, bullets: tuple[str, ...], source_project_ids: tuple[str, ...])`
- `LLMConfig(base_url: str, model: str, api_key: str | None = None, timeout_seconds: int = 300)` (`src/cv_compiler/llm/config.py`)
  - `from_env(prefix: str = "CV_LLM_", env_path: Path | None = Path("config/llm.env")) -> LLMConfig | None`
- `OpenAIProvider(config: LLMConfig, prompt_path: Path, templates_path: Path)` (`src/cv_compiler/llm/openai.py`)
- `ManualProvider(request_path: Path, response_path: Path, model: str = "manual", base_url: str | None = None, prompt_path: Path, templates_path: Path)` (`src/cv_compiler/llm/manual.py`)

## Rendering (`src/cv_compiler/render/*`)

- `RenderFormat` enum (`src/cv_compiler/render/types.py`)
  - `RenderFormat.PDF`
  - `RenderFormat.MARKDOWN`
- `RenderRequest(data: CanonicalData, selection: SelectionResult, template_dir: Path, output_path: Path, format: RenderFormat = RenderFormat.PDF, markdown_path: Path | None = None)`
- `RenderResult(output_path: Path, markdown_path: Path, pdf_path: Path | None)`
- `build_markdown(data: CanonicalData, selection: SelectionResult) -> str` (`src/cv_compiler/render/markdown.py`)
- `render_cv(request: RenderRequest) -> RenderResult` (`src/cv_compiler/render/renderer.py`)
- `render_markdown_to_pdf(markdown: str, output_path: Path) -> None` (`src/cv_compiler/render/renderer.py`)

## Linting (`src/cv_compiler/lint/*`)

- `Severity` enum (`src/cv_compiler/types.py`)
  - `Severity.ERROR`, `Severity.WARNING`
- `LintIssue(code: str, message: str, severity: Severity, source_path: Path | None = None)` (`src/cv_compiler/types.py`)
- `lint_build_inputs(data: CanonicalData) -> Sequence[LintIssue]` (`src/cv_compiler/lint/linter.py`)
- `lint_rendered_output(output_path: Path) -> Sequence[LintIssue]` (`src/cv_compiler/lint/linter.py`)

## Pipeline (`src/cv_compiler/pipeline.py`)

- `BuildRequest(data_dir: Path, job_path: Path | None, template_dir: Path, out_dir: Path, format: RenderFormat = RenderFormat.PDF, llm: LLMProvider | None = None, llm_instructions_path: Path | None = None, experience_regenerate: bool = False, render_from_markdown: Path | None = None)`
- `BuildResult(output_path: Path, markdown_path: Path | None, pdf_path: Path | None, issues: tuple[LintIssue, ...])`
- `build_cv(request: BuildRequest) -> BuildResult`

## Explain (`src/cv_compiler/explain.py`)

- `format_selection_explanation(selection: SelectionResult) -> str`
