# Project Index

Deterministic index of files + local import connections (includes tests).

## Overview

- Python modules indexed: 59
- Other files indexed: 62

## Python Modules

### `scripts/check_llm_drafts.py`

- Module: `scripts.check_llm_drafts`
- Doc: Validate LLM experience drafts against project data.
- Defines: `main`
- Imports (local): `cv_compiler.parse.loaders` → `src/cv_compiler/parse/loaders.py`, `cv_compiler.tools.llm_draft_check` → `src/cv_compiler/tools/llm_draft_check.py`
- Imported by (local): (none)
- External import roots: `argparse`, `pathlib`, `sys`

### `scripts/check_projects.py`

- Module: `scripts.check_projects`
- Doc: Validate project Markdown files and report per-file issues.
- Defines: `main`
- Imports (local): `cv_compiler.tools.project_check` → `src/cv_compiler/tools/project_check.py`
- Imported by (local): (none)
- External import roots: `argparse`, `pathlib`, `sys`

### `scripts/generate_experience_summary.py`

- Module: `scripts.generate_experience_summary`
- Doc: Generate the one-time experience summary file via Codex.
- Defines: `main`
- Imports (local): `cv_compiler.llm.codex` → `src/cv_compiler/llm/codex.py`, `cv_compiler.parse.loaders` → `src/cv_compiler/parse/loaders.py`, `cv_compiler.pipeline` → `src/cv_compiler/pipeline.py`
- Imported by (local): (none)
- External import roots: `argparse`, `pathlib`, `sys`

### `scripts/project_index.py`

- Module: `scripts.project_index`
- Doc: Generate a navigable project index (local import graph + per-file summary).
- Defines: `PythonModuleInfo`, `_build_module_info`, `_defined_symbols`, `_ensure_module_docstring`, `_extract_imports`, `_is_package_file`, `_iter_files`, `_module_name_for_path`, `_render_markdown_index`, `_resolve_relative_module`, `main`
- Imports (local): (none)
- Imported by (local): (none)
- External import roots: `argparse`, `ast`, `collections`, `dataclasses`, `pathlib`

### `scripts/task_index.py`

- Module: `scripts.task_index`
- Doc: Generate a per-file task index as a temporary working checklist.
- Defines: `Stub`, `_extract_local_import_edges`, `_find_stubs`, `_is_not_implemented_raise`, `_is_stub_body`, `_iter_python_files`, `_module_name_for_path`, `_render_task_index`, `_topo_order`, `main`
- Imports (local): (none)
- Imported by (local): (none)
- External import roots: `argparse`, `ast`, `collections`, `dataclasses`, `pathlib`

### `src/cv_compiler/__init__.py`

- Module: `cv_compiler`
- Doc: ATS CV compiler package.
- Defines: (none)
- Imports (local): (none)
- Imported by (local): (none)
- External import roots: (none)

### `src/cv_compiler/__main__.py`

- Module: `cv_compiler.__main__`
- Doc: Module entrypoint for `python -m cv_compiler`.
- Defines: (none)
- Imports (local): `cv_compiler.cli` → `src/cv_compiler/cli.py`
- Imported by (local): (none)
- External import roots: (none)

### `src/cv_compiler/cli.py`

- Module: `cv_compiler.cli`
- Doc: CLI argument parsing and command dispatch.
- Defines: `_build_parser`, `_filter_warnings`, `_normalize_llm_mode`, `_prompt_llm_mode`, `_resolve_example_root`, `_resolve_job_paths`, `_resolve_llm_mode`, `main`
- Imports (local): `cv_compiler.explain` → `src/cv_compiler/explain.py`, `cv_compiler.ingest` → `src/cv_compiler/ingest/__init__.py`, `cv_compiler.lint.linter` → `src/cv_compiler/lint/linter.py`, `cv_compiler.llm` → `src/cv_compiler/llm/__init__.py`, `cv_compiler.llm.config` → `src/cv_compiler/llm/config.py`, `cv_compiler.parse.loaders` → `src/cv_compiler/parse/loaders.py`, `cv_compiler.pipeline` → `src/cv_compiler/pipeline.py`, `cv_compiler.render.types` → `src/cv_compiler/render/types.py`, `cv_compiler.select.selector` → `src/cv_compiler/select/selector.py`, `cv_compiler.types` → `src/cv_compiler/types.py`
- Imported by (local): `cv_compiler.__main__`, `tests.test_cli_job_resolution`, `tests.test_cli_parsing`
- External import roots: `argparse`, `collections`, `os`, `pathlib`, `sys`

### `src/cv_compiler/explain.py`

- Module: `cv_compiler.explain`
- Doc: Formatting helpers for selection explanations.
- Defines: `format_selection_explanation`
- Imports (local): `cv_compiler.select.types` → `src/cv_compiler/select/types.py`
- Imported by (local): `cv_compiler.cli`, `tests.test_signatures`
- External import roots: (none)

### `src/cv_compiler/ingest/__init__.py`

- Module: `cv_compiler.ingest`
- Doc: Ingestion helpers for bootstrapping canonical data.
- Defines: (none)
- Imports (local): `cv_compiler.ingest.pdf_ingest` → `src/cv_compiler/ingest/pdf_ingest.py`
- Imported by (local): `cv_compiler.cli`
- External import roots: (none)

### `src/cv_compiler/ingest/pdf_ingest.py`

- Module: `cv_compiler.ingest.pdf_ingest`
- Doc: PDF ingestion helpers for bootstrapping canonical Markdown files.
- Defines: `IngestResult`, `ParsedCv`, `ParsedEducation`, `ParsedExperience`, `ParsedLink`, `ParsedProfile`, `ParsedProject`, `ParsedSkillCategory`, `_backup_ingest_files`, `_build_ingest_prompt`, `_coerce_str`, `_coerce_str_list`, `_collect_ingest_files`, `_ensure_writable`, `_ingest_schema`, `_manual_llm_content`, `_parse_education`, `_parse_experience`, `_parse_links`, `_parse_projects`, `_parse_skills`, `_remove_written_files`, `_request_llm_content`, `_require_field`, `_restore_ingest_backup`, `_slugify`, `_unique_id`, `_write_frontmatter`, `extract_pdf_text`, `ingest_pdf_to_markdown`, `parse_ingest_payload`, `parse_ingest_response`, `write_ingest_files`
- Imports (local): `cv_compiler.llm.config` → `src/cv_compiler/llm/config.py`, `cv_compiler.llm.openai` → `src/cv_compiler/llm/openai.py`
- Imported by (local): `cv_compiler.ingest`, `tests.test_pdf_ingest`
- External import roots: `dataclasses`, `json`, `pathlib`, `pypdf`, `re`, `shutil`, `time`, `typing`, `urllib`, `yaml`

### `src/cv_compiler/lint/__init__.py`

- Module: `cv_compiler.lint`
- Doc: Linting entrypoints for inputs and outputs.
- Defines: (none)
- Imports (local): `cv_compiler.lint.linter` → `src/cv_compiler/lint/linter.py`
- Imported by (local): (none)
- External import roots: (none)

### `src/cv_compiler/lint/linter.py`

- Module: `cv_compiler.lint.linter`
- Doc: Lint interfaces for inputs and outputs.
- Defines: `lint_build_inputs`, `lint_rendered_output`
- Imports (local): `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`, `cv_compiler.types` → `src/cv_compiler/types.py`
- Imported by (local): `cv_compiler.cli`, `cv_compiler.lint`, `cv_compiler.pipeline`, `tests.test_signatures`
- External import roots: `collections`, `pathlib`

### `src/cv_compiler/llm/__init__.py`

- Module: `cv_compiler.llm`
- Doc: Optional LLM interfaces and providers.
- Defines: (none)
- Imports (local): `cv_compiler.llm.base` → `src/cv_compiler/llm/base.py`, `cv_compiler.llm.codex` → `src/cv_compiler/llm/codex.py`, `cv_compiler.llm.config` → `src/cv_compiler/llm/config.py`, `cv_compiler.llm.manual` → `src/cv_compiler/llm/manual.py`, `cv_compiler.llm.openai` → `src/cv_compiler/llm/openai.py`
- Imported by (local): `cv_compiler.cli`
- External import roots: (none)

### `src/cv_compiler/llm/base.py`

- Module: `cv_compiler.llm.base`
- Doc: Optional LLM provider protocol and request types.
- Defines: `BulletRewriteRequest`, `BulletRewriteResult`, `ExperienceDraft`, `LLMProvider`, `NoopProvider`
- Imports (local): `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): `cv_compiler.llm`, `cv_compiler.llm.codex`, `cv_compiler.llm.experience`, `cv_compiler.llm.manual`, `cv_compiler.llm.openai`, `cv_compiler.pipeline`, `tests.test_llm_experience_numbers`, `tests.test_llm_experience_role`, `tests.test_signatures`
- External import roots: `collections`, `dataclasses`, `typing`

### `src/cv_compiler/llm/codex.py`

- Module: `cv_compiler.llm.codex`
- Doc: Codex CLI-backed LLM provider.
- Defines: `CodexExecConfig`, `CodexExecProvider`, `_ensure_full_auto`, `_extract_json_payload`, `_get_output_last_message`, `_has_exec_mode_flag`, `_parse_bool`, `_parse_timeout`, `_prepare_json_exec`, `_read_last_message`, `_run_codex_with_spinner`
- Imports (local): `cv_compiler.llm.base` → `src/cv_compiler/llm/base.py`, `cv_compiler.llm.config` → `src/cv_compiler/llm/config.py`, `cv_compiler.llm.experience` → `src/cv_compiler/llm/experience.py`, `cv_compiler.llm.skills` → `src/cv_compiler/llm/skills.py`, `cv_compiler.llm.summary` → `src/cv_compiler/llm/summary.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): `cv_compiler.llm`, `scripts.generate_experience_summary`, `tests.test_codex_exec_config`
- External import roots: `collections`, `dataclasses`, `json`, `os`, `pathlib`, `shlex`, `subprocess`, `sys`, `tempfile`, `time`

### `src/cv_compiler/llm/config.py`

- Module: `cv_compiler.llm.config`
- Doc: LLM configuration (optional).
- Defines: `LLMConfig`, `_parse_timeout`, `read_env_file`, `upsert_env_value`
- Imports (local): (none)
- Imported by (local): `cv_compiler.cli`, `cv_compiler.ingest.pdf_ingest`, `cv_compiler.llm`, `cv_compiler.llm.codex`, `cv_compiler.llm.openai`, `tests.test_llm_config`
- External import roots: `dataclasses`, `os`, `pathlib`

### `src/cv_compiler/llm/experience.py`

- Module: `cv_compiler.llm.experience`
- Doc: Helpers for LLM-derived experience generation.
- Defines: `ExperienceTemplate`, `_collect_allowed_keywords`, `_collect_allowed_numbers`, `_derive_experience_id`, `_extract_yaml_payload`, `_parse_keywords`, `_safe_id`, `_strip_code_fence`, `_strip_fence_language`, `_validate_bullet_numbers`, `_validate_keywords`, `archive_user_experience_files`, `backup_llm_experience_files`, `build_experience_prompt`, `load_experience_templates`, `parse_experience_drafts`, `restore_llm_experience_files`, `write_experience_artifacts`
- Imports (local): `cv_compiler.llm.base` → `src/cv_compiler/llm/base.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): `cv_compiler.llm.codex`, `cv_compiler.llm.manual`, `cv_compiler.llm.openai`, `cv_compiler.pipeline`, `cv_compiler.tools.llm_draft_check`, `tests.test_llm_experience_backup`, `tests.test_llm_experience_numbers`, `tests.test_llm_experience_parsing`, `tests.test_llm_experience_role`
- External import roots: `dataclasses`, `pathlib`, `re`, `shutil`, `time`, `typing`, `yaml`

### `src/cv_compiler/llm/manual.py`

- Module: `cv_compiler.llm.manual`
- Doc: Manual/offline LLM provider.
- Defines: `ManualProvider`, `_extract_response_content`
- Imports (local): `cv_compiler.llm.base` → `src/cv_compiler/llm/base.py`, `cv_compiler.llm.experience` → `src/cv_compiler/llm/experience.py`, `cv_compiler.llm.openai` → `src/cv_compiler/llm/openai.py`, `cv_compiler.llm.skills` → `src/cv_compiler/llm/skills.py`, `cv_compiler.llm.summary` → `src/cv_compiler/llm/summary.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): `cv_compiler.llm`, `tests.test_llm_manual_provider`
- External import roots: `collections`, `json`, `pathlib`

### `src/cv_compiler/llm/openai.py`

- Module: `cv_compiler.llm.openai`
- Doc: OpenAI-compatible LLM provider (chat-completions).
- Defines: `OpenAIProvider`, `build_chat_endpoint`, `build_chat_payload`, `experience_response_schema`, `extract_chat_content`, `request_chat_completion`
- Imports (local): `cv_compiler.llm.base` → `src/cv_compiler/llm/base.py`, `cv_compiler.llm.config` → `src/cv_compiler/llm/config.py`, `cv_compiler.llm.experience` → `src/cv_compiler/llm/experience.py`, `cv_compiler.llm.skills` → `src/cv_compiler/llm/skills.py`, `cv_compiler.llm.summary` → `src/cv_compiler/llm/summary.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): `cv_compiler.ingest.pdf_ingest`, `cv_compiler.llm`, `cv_compiler.llm.manual`, `cv_compiler.tools.llm_draft_check`
- External import roots: `collections`, `json`, `pathlib`, `urllib`

### `src/cv_compiler/llm/skills.py`

- Module: `cv_compiler.llm.skills`
- Doc: LLM helpers for highlighting skills/tools.
- Defines: `SkillHighlightRequest`, `build_skills_prompt`, `parse_skill_highlights`, `skills_highlight_schema`
- Imports (local): `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): `cv_compiler.llm.codex`, `cv_compiler.llm.manual`, `cv_compiler.llm.openai`, `tests.test_skill_highlights`
- External import roots: `dataclasses`, `json`, `pathlib`, `typing`, `yaml`

### `src/cv_compiler/llm/summary.py`

- Module: `cv_compiler.llm.summary`
- Doc: LLM helpers for generating an experience summary paragraph.
- Defines: `ExperienceSummaryRequest`, `build_experience_summary_prompt`, `experience_summary_schema`, `parse_experience_summary`
- Imports (local): `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): `cv_compiler.llm.codex`, `cv_compiler.llm.manual`, `cv_compiler.llm.openai`
- External import roots: `dataclasses`, `json`, `pathlib`, `typing`, `yaml`

### `src/cv_compiler/parse/__init__.py`

- Module: `cv_compiler.parse`
- Doc: Parsing and loading utilities.
- Defines: (none)
- Imports (local): `cv_compiler.parse.loaders` → `src/cv_compiler/parse/loaders.py`
- Imported by (local): (none)
- External import roots: (none)

### `src/cv_compiler/parse/frontmatter.py`

- Module: `cv_compiler.parse.frontmatter`
- Doc: Frontmatter parsing for Markdown sources.
- Defines: `MarkdownDocument`, `parse_markdown_frontmatter`
- Imports (local): (none)
- Imported by (local): `cv_compiler.parse.loaders`, `cv_compiler.tools.project_check`, `tests.test_llm_experience_role`, `tests.test_pdf_ingest`, `tests.test_signatures`
- External import roots: `collections`, `dataclasses`, `pathlib`, `typing`, `yaml`

### `src/cv_compiler/parse/loaders.py`

- Module: `cv_compiler.parse.loaders`
- Doc: Load canonical data and job specs from disk.
- Defines: `_experience_base_and_priority`, `_load_education`, `_load_experience_entry`, `_load_profile`, `_load_project_entry`, `_load_skills`, `_optional_list_of_str`, `_optional_str`, `_optional_str_or_none`, `_require_list_of_mapping`, `_require_list_of_str`, `_require_mapping`, `_require_str`, `_select_experience_files`, `load_canonical_data`, `load_job_spec`
- Imports (local): `cv_compiler.parse.frontmatter` → `src/cv_compiler/parse/frontmatter.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): `cv_compiler.cli`, `cv_compiler.parse`, `cv_compiler.pipeline`, `scripts.check_llm_drafts`, `scripts.generate_experience_summary`, `tests.test_experience_loading`, `tests.test_profile_about_me`, `tests.test_signatures`
- External import roots: `collections`, `pathlib`, `re`, `typing`

### `src/cv_compiler/pipeline.py`

- Module: `cv_compiler.pipeline`
- Doc: Build pipeline request/response types and entrypoint.
- Defines: `BuildRequest`, `BuildResult`, `_apply_rewrites`, `_deterministic_skill_filter`, `_deterministic_skill_highlights`, `_format_experience_summary`, `_job_keyword_set`, `_load_experience_summary`, `_load_text_optional`, `_sanitize_stem`, `_tokenize_skill`, `build_cv`
- Imports (local): `cv_compiler.lint.linter` → `src/cv_compiler/lint/linter.py`, `cv_compiler.llm.base` → `src/cv_compiler/llm/base.py`, `cv_compiler.llm.experience` → `src/cv_compiler/llm/experience.py`, `cv_compiler.parse.loaders` → `src/cv_compiler/parse/loaders.py`, `cv_compiler.render.renderer` → `src/cv_compiler/render/renderer.py`, `cv_compiler.render.types` → `src/cv_compiler/render/types.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`, `cv_compiler.select.selector` → `src/cv_compiler/select/selector.py`, `cv_compiler.types` → `src/cv_compiler/types.py`
- Imported by (local): `cv_compiler.cli`, `scripts.generate_experience_summary`, `tests.test_build_example`, `tests.test_signatures`, `tests.test_skills_filtering`
- External import roots: `dataclasses`, `pathlib`, `re`, `shutil`

### `src/cv_compiler/render/__init__.py`

- Module: `cv_compiler.render`
- Doc: Rendering interfaces for producing ATS-safe outputs.
- Defines: (none)
- Imports (local): `cv_compiler.render.renderer` → `src/cv_compiler/render/renderer.py`, `cv_compiler.render.types` → `src/cv_compiler/render/types.py`
- Imported by (local): (none)
- External import roots: (none)

### `src/cv_compiler/render/markdown.py`

- Module: `cv_compiler.render.markdown`
- Doc: Markdown rendering for CV content.
- Defines: `_bold_first_keyword`, `_bold_numeric_tokens`, `_emphasize_experience_bullet`, `_first_clause_end`, `_fix_spacing`, `build_markdown`, `normalize_markdown_text`
- Imports (local): `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`, `cv_compiler.select.types` → `src/cv_compiler/select/types.py`
- Imported by (local): `cv_compiler.render.renderer`, `tests.test_markdown_normalization`, `tests.test_skills_filtering`
- External import roots: `re`, `unicodedata`

### `src/cv_compiler/render/renderer.py`

- Module: `cv_compiler.render.renderer`
- Doc: Rendering interface for CV output.
- Defines: `_normalize_pdf_text`, `_render_rich_line`, `_split_bold`, `_write_tokens_line`, `render_cv`, `render_markdown_to_pdf`
- Imports (local): `cv_compiler.render.markdown` → `src/cv_compiler/render/markdown.py`, `cv_compiler.render.types` → `src/cv_compiler/render/types.py`
- Imported by (local): `cv_compiler.pipeline`, `cv_compiler.render`, `tests.test_signatures`
- External import roots: `datetime`, `fpdf`, `pathlib`

### `src/cv_compiler/render/types.py`

- Module: `cv_compiler.render.types`
- Doc: Rendering request/response types.
- Defines: `RenderFormat`, `RenderRequest`, `RenderResult`
- Imports (local): `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`, `cv_compiler.select.types` → `src/cv_compiler/select/types.py`
- Imported by (local): `cv_compiler.cli`, `cv_compiler.pipeline`, `cv_compiler.render`, `cv_compiler.render.renderer`, `tests.test_build_example`, `tests.test_signatures`
- External import roots: `dataclasses`, `enum`, `pathlib`

### `src/cv_compiler/schema/__init__.py`

- Module: `cv_compiler.schema`
- Doc: Schema models for validated CV inputs.
- Defines: (none)
- Imports (local): `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): (none)
- External import roots: (none)

### `src/cv_compiler/schema/models.py`

- Module: `cv_compiler.schema.models`
- Doc: Dataclasses representing validated CV entities.
- Defines: `CanonicalData`, `Education`, `EducationEntry`, `ExperienceEntry`, `JobSpec`, `Link`, `Profile`, `ProjectEntry`, `Skills`, `SkillsCategory`
- Imports (local): (none)
- Imported by (local): `cv_compiler.lint.linter`, `cv_compiler.llm.base`, `cv_compiler.llm.codex`, `cv_compiler.llm.experience`, `cv_compiler.llm.manual`, `cv_compiler.llm.openai`, `cv_compiler.llm.skills`, `cv_compiler.llm.summary`, `cv_compiler.parse.loaders`, `cv_compiler.pipeline`, `cv_compiler.render.markdown`, `cv_compiler.render.types`, `cv_compiler.schema`, `cv_compiler.select.selector`, `cv_compiler.tools.llm_draft_check`, `tests.test_llm_draft_check`, `tests.test_llm_experience_numbers`, `tests.test_llm_experience_role`, `tests.test_llm_manual_provider`, `tests.test_markdown_normalization`, `tests.test_signatures`, `tests.test_skills_filtering`
- External import roots: `dataclasses`, `pathlib`

### `src/cv_compiler/select/__init__.py`

- Module: `cv_compiler.select`
- Doc: Deterministic selection API and result types.
- Defines: (none)
- Imports (local): `cv_compiler.select.selector` → `src/cv_compiler/select/selector.py`, `cv_compiler.select.types` → `src/cv_compiler/select/types.py`
- Imported by (local): (none)
- External import roots: (none)

### `src/cv_compiler/select/selector.py`

- Module: `cv_compiler.select.selector`
- Doc: Deterministic selection interface.
- Defines: `_job_keywords`, `_parse_ym`, `_recency_score`, `_tokenize`, `select_content`
- Imports (local): `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`, `cv_compiler.select.types` → `src/cv_compiler/select/types.py`
- Imported by (local): `cv_compiler.cli`, `cv_compiler.pipeline`, `cv_compiler.select`, `tests.test_signatures`
- External import roots: `re`

### `src/cv_compiler/select/types.py`

- Module: `cv_compiler.select.types`
- Doc: Selection result and decision types.
- Defines: `SelectionDecision`, `SelectionResult`
- Imports (local): (none)
- Imported by (local): `cv_compiler.explain`, `cv_compiler.render.markdown`, `cv_compiler.render.types`, `cv_compiler.select`, `cv_compiler.select.selector`, `tests.test_markdown_normalization`, `tests.test_signatures`, `tests.test_skills_filtering`
- External import roots: `dataclasses`

### `src/cv_compiler/tools/__init__.py`

- Module: `cv_compiler.tools`
- Doc: Utility helpers for validating and inspecting canonical data.
- Defines: (none)
- Imports (local): `cv_compiler.tools.llm_draft_check` → `src/cv_compiler/tools/llm_draft_check.py`, `cv_compiler.tools.project_check` → `src/cv_compiler/tools/project_check.py`
- Imported by (local): (none)
- External import roots: (none)

### `src/cv_compiler/tools/llm_draft_check.py`

- Module: `cv_compiler.tools.llm_draft_check`
- Doc: Validate LLM experience drafts against canonical project data.
- Defines: `DraftIssue`, `collect_draft_issues`, `load_draft_text`
- Imports (local): `cv_compiler.llm.experience` → `src/cv_compiler/llm/experience.py`, `cv_compiler.llm.openai` → `src/cv_compiler/llm/openai.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): `cv_compiler.tools`, `scripts.check_llm_drafts`, `tests.test_llm_draft_check`
- External import roots: `dataclasses`, `json`, `pathlib`

### `src/cv_compiler/tools/project_check.py`

- Module: `cv_compiler.tools.project_check`
- Doc: Project file validation helpers.
- Defines: `ProjectIssue`, `_check_optional_str`, `_check_required_list_of_str`, `_check_required_str`, `collect_project_issues`
- Imports (local): `cv_compiler.parse.frontmatter` → `src/cv_compiler/parse/frontmatter.py`
- Imported by (local): `cv_compiler.tools`, `scripts.check_projects`, `tests.test_project_check`
- External import roots: `collections`, `dataclasses`, `pathlib`, `typing`

### `src/cv_compiler/types.py`

- Module: `cv_compiler.types`
- Doc: Shared enums and lint issue types.
- Defines: `LintIssue`, `Severity`
- Imports (local): (none)
- Imported by (local): `cv_compiler.cli`, `cv_compiler.lint.linter`, `cv_compiler.pipeline`, `tests.test_build_example`, `tests.test_signatures`
- External import roots: `dataclasses`, `enum`, `pathlib`

### `tests/__init__.py`

- Module: `tests.__init__`
- Doc: Test package marker for unittest discovery.
- Defines: (none)
- Imports (local): (none)
- Imported by (local): (none)
- External import roots: (none)

### `tests/test_build_example.py`

- Module: `tests.test_build_example`
- Doc: Smoke tests for building the bundled example dataset.
- Defines: `TestBuildExample`, `_sha256`
- Imports (local): `cv_compiler.pipeline` → `src/cv_compiler/pipeline.py`, `cv_compiler.render.types` → `src/cv_compiler/render/types.py`, `cv_compiler.types` → `src/cv_compiler/types.py`
- Imported by (local): (none)
- External import roots: `hashlib`, `pathlib`, `tempfile`, `unittest`

### `tests/test_cli_job_resolution.py`

- Module: `tests.test_cli_job_resolution`
- Doc: Tests for job path resolution logic.
- Defines: `TestJobResolution`
- Imports (local): `cv_compiler.cli` → `src/cv_compiler/cli.py`
- Imported by (local): (none)
- External import roots: `pathlib`, `tempfile`, `unittest`

### `tests/test_cli_parsing.py`

- Module: `tests.test_cli_parsing`
- Doc: Tests for CLI argument parsing.
- Defines: `TestCliParsing`
- Imports (local): `cv_compiler.cli` → `src/cv_compiler/cli.py`
- Imported by (local): (none)
- External import roots: `contextlib`, `io`, `unittest`

### `tests/test_codex_exec_config.py`

- Module: `tests.test_codex_exec_config`
- Doc: Tests for Codex exec config parsing.
- Defines: `TestCodexExecConfig`, `_clear_env`, `_temp_env`
- Imports (local): `cv_compiler.llm.codex` → `src/cv_compiler/llm/codex.py`
- Imported by (local): (none)
- External import roots: `contextlib`, `os`, `unittest`

### `tests/test_experience_loading.py`

- Module: `tests.test_experience_loading`
- Doc: Tests for experience file selection precedence.
- Defines: `TestExperienceLoading`, `_experience_md`, `_profile_md`, `_project_md`, `_skills_md`, `_write`
- Imports (local): `cv_compiler.parse.loaders` → `src/cv_compiler/parse/loaders.py`
- Imported by (local): (none)
- External import roots: `pathlib`, `tempfile`, `unittest`

### `tests/test_llm_config.py`

- Module: `tests.test_llm_config`
- Doc: Tests for loading LLM config from env files.
- Defines: `TestLLMConfig`
- Imports (local): `cv_compiler.llm.config` → `src/cv_compiler/llm/config.py`
- Imported by (local): (none)
- External import roots: `os`, `pathlib`, `tempfile`, `unittest`

### `tests/test_llm_draft_check.py`

- Module: `tests.test_llm_draft_check`
- Doc: Tests for LLM draft validation helpers.
- Defines: `TestLlmDraftCheck`
- Imports (local): `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`, `cv_compiler.tools.llm_draft_check` → `src/cv_compiler/tools/llm_draft_check.py`
- Imported by (local): (none)
- External import roots: `unittest`

### `tests/test_llm_experience_backup.py`

- Module: `tests.test_llm_experience_backup`
- Doc: Tests for LLM experience backup helpers.
- Defines: `TestLlmExperienceBackup`
- Imports (local): `cv_compiler.llm.experience` → `src/cv_compiler/llm/experience.py`
- Imported by (local): (none)
- External import roots: `pathlib`, `tempfile`, `unittest`

### `tests/test_llm_experience_numbers.py`

- Module: `tests.test_llm_experience_numbers`
- Doc: Tests for allowed numeric tokens in LLM experience bullets.
- Defines: `TestLlmExperienceNumbers`
- Imports (local): `cv_compiler.llm.base` → `src/cv_compiler/llm/base.py`, `cv_compiler.llm.experience` → `src/cv_compiler/llm/experience.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): (none)
- External import roots: `pathlib`, `tempfile`, `unittest`

### `tests/test_llm_experience_parsing.py`

- Module: `tests.test_llm_experience_parsing`
- Doc: Tests for parsing LLM experience responses with extra text.
- Defines: `TestLLMExperienceParsing`
- Imports (local): `cv_compiler.llm.experience` → `src/cv_compiler/llm/experience.py`
- Imported by (local): (none)
- External import roots: `unittest`

### `tests/test_llm_experience_role.py`

- Module: `tests.test_llm_experience_role`
- Doc: Tests for experience role fallback behavior.
- Defines: `TestLlmExperienceRole`
- Imports (local): `cv_compiler.llm.base` → `src/cv_compiler/llm/base.py`, `cv_compiler.llm.experience` → `src/cv_compiler/llm/experience.py`, `cv_compiler.parse.frontmatter` → `src/cv_compiler/parse/frontmatter.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): (none)
- External import roots: `pathlib`, `tempfile`, `unittest`

### `tests/test_llm_manual_provider.py`

- Module: `tests.test_llm_manual_provider`
- Doc: Tests for the manual/offline LLM provider.
- Defines: `TestManualProvider`
- Imports (local): `cv_compiler.llm.manual` → `src/cv_compiler/llm/manual.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): (none)
- External import roots: `json`, `pathlib`, `tempfile`, `unittest`

### `tests/test_markdown_normalization.py`

- Module: `tests.test_markdown_normalization`
- Doc: Tests for Markdown normalization to ASCII.
- Defines: `TestMarkdownNormalization`
- Imports (local): `cv_compiler.render.markdown` → `src/cv_compiler/render/markdown.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`, `cv_compiler.select.types` → `src/cv_compiler/select/types.py`
- Imported by (local): (none)
- External import roots: `unittest`

### `tests/test_pdf_ingest.py`

- Module: `tests.test_pdf_ingest`
- Doc: Tests for PDF ingestion helpers.
- Defines: `TestPdfIngest`
- Imports (local): `cv_compiler.ingest.pdf_ingest` → `src/cv_compiler/ingest/pdf_ingest.py`, `cv_compiler.parse.frontmatter` → `src/cv_compiler/parse/frontmatter.py`
- Imported by (local): (none)
- External import roots: `pathlib`, `tempfile`, `unittest`

### `tests/test_profile_about_me.py`

- Module: `tests.test_profile_about_me`
- Doc: Tests for profile about_me parsing.
- Defines: `TestProfileAboutMe`, `_write`
- Imports (local): `cv_compiler.parse.loaders` → `src/cv_compiler/parse/loaders.py`
- Imported by (local): (none)
- External import roots: `pathlib`, `tempfile`, `unittest`

### `tests/test_project_check.py`

- Module: `tests.test_project_check`
- Doc: Tests for project file validation helper.
- Defines: `TestProjectCheck`
- Imports (local): `cv_compiler.tools.project_check` → `src/cv_compiler/tools/project_check.py`
- Imported by (local): (none)
- External import roots: `pathlib`, `tempfile`, `unittest`

### `tests/test_signatures.py`

- Module: `tests.test_signatures`
- Doc: Signature-level tests for the scaffolded public API.
- Defines: `TestSignatures`
- Imports (local): `cv_compiler.explain` → `src/cv_compiler/explain.py`, `cv_compiler.lint.linter` → `src/cv_compiler/lint/linter.py`, `cv_compiler.llm.base` → `src/cv_compiler/llm/base.py`, `cv_compiler.parse.frontmatter` → `src/cv_compiler/parse/frontmatter.py`, `cv_compiler.parse.loaders` → `src/cv_compiler/parse/loaders.py`, `cv_compiler.pipeline` → `src/cv_compiler/pipeline.py`, `cv_compiler.render.renderer` → `src/cv_compiler/render/renderer.py`, `cv_compiler.render.types` → `src/cv_compiler/render/types.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`, `cv_compiler.select.selector` → `src/cv_compiler/select/selector.py`, `cv_compiler.select.types` → `src/cv_compiler/select/types.py`, `cv_compiler.types` → `src/cv_compiler/types.py`
- Imported by (local): (none)
- External import roots: `dataclasses`, `inspect`, `unittest`

### `tests/test_skill_highlights.py`

- Module: `tests.test_skill_highlights`
- Doc: Tests for LLM skill highlight parsing.
- Defines: `TestSkillHighlights`
- Imports (local): `cv_compiler.llm.skills` → `src/cv_compiler/llm/skills.py`
- Imported by (local): (none)
- External import roots: `unittest`

### `tests/test_skills_filtering.py`

- Module: `tests.test_skills_filtering`
- Doc: Tests for skills filtering in Markdown rendering.
- Defines: `TestSkillsFiltering`
- Imports (local): `cv_compiler.pipeline` → `src/cv_compiler/pipeline.py`, `cv_compiler.render.markdown` → `src/cv_compiler/render/markdown.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`, `cv_compiler.select.types` → `src/cv_compiler/select/types.py`
- Imported by (local): (none)
- External import roots: `unittest`

## Other Files

- `.DS_Store`
- `.gitignore`
- `.uv_cache/.gitignore`
- `.uv_cache/CACHEDIR.TAG`
- `.uv_cache/interpreter-v4/aarch64/a34cbc46e97e356f.msgpack`
- `.uv_cache/sdists-v6/.gitignore`
- `AGENTS.md`
- `LICENSE`
- `README.md`
- `REQUIREMENTS.md`
- `config/llm.env`
- `config/llm.env.example`
- `config/mcp.json`
- `data/.DS_Store`
- `data/README.md`
- `data/cv.pdf`
- `data/education.md`
- `data/experience/llm_exp_avito_leading_classifieds_platform_2018.md`
- `data/experience/llm_exp_avito_leading_classifieds_platform_2021.md`
- `data/experience/llm_exp_eldorado_llc_m_video_group_electronics_retail_2016.md`
- `data/experience/llm_exp_startup_consulting_2024.md`
- `data/experience/llm_exp_velotix_ml_powered_data_security_platform_2023.md`
- `data/experience_summary.md`
- `data/profile.md`
- `data/projects/proj_avito_attribute_autotrain_pipeline.md`
- `data/projects/proj_avito_bert_latency_optimization.md`
- `data/projects/proj_avito_deal_scam_detection_bert.md`
- `data/projects/proj_avito_exec_dashboards_metrics_tree.md`
- `data/projects/proj_avito_offline_marketing_ab_tests.md`
- `data/projects/proj_avito_reviews_models.md`
- `data/projects/proj_eldorado_fraud_kpi_profitability.md`
- `data/projects/proj_glowbyte_rosbank_dwh.md`
- `data/projects/proj_leader.md`
- `data/projects/proj_startup_consulting.md`
- `data/projects/proj_velotix_cicd_docker_optimization.md`
- `data/projects/proj_velotix_ml_microservice_ha.md`
- `data/projects/proj_velotix_synthetic_data_foundation_model.md`
- `data/skills.md`
- `docs/ENTITIES.md`
- `docs/PROJECT_INDEX.md`
- `examples/README.md`
- `examples/basic/README.md`
- `examples/basic/data/education.md`
- `examples/basic/data/experience/2023-example-corp.md`
- `examples/basic/data/experience/llm_exp_example_corp_2023_02.md`
- `examples/basic/data/profile.md`
- `examples/basic/data/projects/cli-cv-compiler.md`
- `examples/basic/data/skills.md`
- `examples/basic/jobs/backend_engineer.md`
- `examples/basic/templates/README.md`
- `jobs/README.md`
- `jobs/uzum_ml_engineer.md`
- `jobs/xpanceo.md`
- `project_layout.md`
- `prompts/experience_prompt.md`
- `prompts/experience_summary_prompt.md`
- `prompts/experience_templates.yaml`
- `prompts/pdf_ingest_prompt.md`
- `prompts/skills_highlight_prompt.md`
- `pyproject.toml`
- `templates/README.md`
- `uv.lock`
