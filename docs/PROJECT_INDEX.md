# Project Index

Deterministic index of files + local import connections (includes tests).

## Overview

- Python modules indexed: 36
- Other files indexed: 31

## Python Modules

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
- Defines: `_build_parser`, `_normalize_llm_mode`, `_prompt_llm_mode`, `_resolve_example_root`, `_resolve_llm_mode`, `main`
- Imports (local): `cv_compiler.explain` → `src/cv_compiler/explain.py`, `cv_compiler.lint.linter` → `src/cv_compiler/lint/linter.py`, `cv_compiler.llm` → `src/cv_compiler/llm/__init__.py`, `cv_compiler.llm.config` → `src/cv_compiler/llm/config.py`, `cv_compiler.parse.loaders` → `src/cv_compiler/parse/loaders.py`, `cv_compiler.pipeline` → `src/cv_compiler/pipeline.py`, `cv_compiler.render.types` → `src/cv_compiler/render/types.py`, `cv_compiler.select.selector` → `src/cv_compiler/select/selector.py`, `cv_compiler.types` → `src/cv_compiler/types.py`
- Imported by (local): `cv_compiler.__main__`, `tests.test_cli_parsing`
- External import roots: `argparse`, `collections`, `os`, `pathlib`, `sys`

### `src/cv_compiler/explain.py`

- Module: `cv_compiler.explain`
- Doc: Formatting helpers for selection explanations.
- Defines: `format_selection_explanation`
- Imports (local): `cv_compiler.select.types` → `src/cv_compiler/select/types.py`
- Imported by (local): `cv_compiler.cli`, `tests.test_signatures`
- External import roots: (none)

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
- Imports (local): `cv_compiler.llm.base` → `src/cv_compiler/llm/base.py`, `cv_compiler.llm.config` → `src/cv_compiler/llm/config.py`, `cv_compiler.llm.manual` → `src/cv_compiler/llm/manual.py`, `cv_compiler.llm.openai` → `src/cv_compiler/llm/openai.py`
- Imported by (local): `cv_compiler.cli`
- External import roots: (none)

### `src/cv_compiler/llm/base.py`

- Module: `cv_compiler.llm.base`
- Doc: Optional LLM provider protocol and request types.
- Defines: `BulletRewriteRequest`, `BulletRewriteResult`, `ExperienceDraft`, `LLMProvider`, `NoopProvider`
- Imports (local): `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): `cv_compiler.llm`, `cv_compiler.llm.experience`, `cv_compiler.llm.manual`, `cv_compiler.llm.openai`, `cv_compiler.pipeline`, `tests.test_signatures`
- External import roots: `collections`, `dataclasses`, `typing`

### `src/cv_compiler/llm/config.py`

- Module: `cv_compiler.llm.config`
- Doc: LLM configuration (optional).
- Defines: `LLMConfig`, `_parse_timeout`, `read_env_file`, `upsert_env_value`
- Imports (local): (none)
- Imported by (local): `cv_compiler.cli`, `cv_compiler.llm`, `cv_compiler.llm.openai`, `tests.test_llm_config`
- External import roots: `dataclasses`, `os`, `pathlib`

### `src/cv_compiler/llm/experience.py`

- Module: `cv_compiler.llm.experience`
- Doc: Helpers for LLM-derived experience generation.
- Defines: `ExperienceTemplate`, `_collect_allowed_numbers`, `_derive_experience_id`, `_extract_yaml_payload`, `_safe_id`, `_strip_code_fence`, `_strip_fence_language`, `_validate_bullet_numbers`, `archive_user_experience_files`, `build_experience_prompt`, `load_experience_templates`, `parse_experience_drafts`, `write_experience_artifacts`
- Imports (local): `cv_compiler.llm.base` → `src/cv_compiler/llm/base.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): `cv_compiler.llm.manual`, `cv_compiler.llm.openai`, `cv_compiler.pipeline`, `tests.test_llm_experience_parsing`
- External import roots: `dataclasses`, `pathlib`, `re`, `time`, `typing`, `yaml`

### `src/cv_compiler/llm/manual.py`

- Module: `cv_compiler.llm.manual`
- Doc: Manual/offline LLM provider.
- Defines: `ManualProvider`, `_extract_response_content`
- Imports (local): `cv_compiler.llm.base` → `src/cv_compiler/llm/base.py`, `cv_compiler.llm.experience` → `src/cv_compiler/llm/experience.py`, `cv_compiler.llm.openai` → `src/cv_compiler/llm/openai.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): `cv_compiler.llm`, `tests.test_llm_manual_provider`
- External import roots: `collections`, `json`, `pathlib`

### `src/cv_compiler/llm/openai.py`

- Module: `cv_compiler.llm.openai`
- Doc: OpenAI-compatible LLM provider (chat-completions).
- Defines: `OpenAIProvider`, `_chat_completion`, `build_chat_endpoint`, `build_chat_payload`, `experience_response_schema`, `extract_chat_content`
- Imports (local): `cv_compiler.llm.base` → `src/cv_compiler/llm/base.py`, `cv_compiler.llm.config` → `src/cv_compiler/llm/config.py`, `cv_compiler.llm.experience` → `src/cv_compiler/llm/experience.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): `cv_compiler.llm`, `cv_compiler.llm.manual`
- External import roots: `collections`, `json`, `pathlib`, `urllib`

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
- Imported by (local): `cv_compiler.parse.loaders`, `tests.test_signatures`
- External import roots: `collections`, `dataclasses`, `pathlib`, `typing`, `yaml`

### `src/cv_compiler/parse/loaders.py`

- Module: `cv_compiler.parse.loaders`
- Doc: Load canonical data and job specs from disk.
- Defines: `_experience_base_and_priority`, `_load_education`, `_load_experience_entry`, `_load_profile`, `_load_project_entry`, `_load_skills`, `_optional_str`, `_optional_str_or_none`, `_require_list_of_mapping`, `_require_list_of_str`, `_require_mapping`, `_require_str`, `_select_experience_files`, `load_canonical_data`, `load_job_spec`
- Imports (local): `cv_compiler.parse.frontmatter` → `src/cv_compiler/parse/frontmatter.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): `cv_compiler.cli`, `cv_compiler.parse`, `cv_compiler.pipeline`, `tests.test_experience_loading`, `tests.test_profile_about_me`, `tests.test_signatures`
- External import roots: `collections`, `pathlib`, `re`, `typing`

### `src/cv_compiler/pipeline.py`

- Module: `cv_compiler.pipeline`
- Doc: Build pipeline request/response types and entrypoint.
- Defines: `BuildRequest`, `BuildResult`, `_apply_rewrites`, `_load_text_optional`, `_sanitize_stem`, `build_cv`
- Imports (local): `cv_compiler.lint.linter` → `src/cv_compiler/lint/linter.py`, `cv_compiler.llm.base` → `src/cv_compiler/llm/base.py`, `cv_compiler.llm.experience` → `src/cv_compiler/llm/experience.py`, `cv_compiler.parse.loaders` → `src/cv_compiler/parse/loaders.py`, `cv_compiler.render.renderer` → `src/cv_compiler/render/renderer.py`, `cv_compiler.render.types` → `src/cv_compiler/render/types.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`, `cv_compiler.select.selector` → `src/cv_compiler/select/selector.py`, `cv_compiler.types` → `src/cv_compiler/types.py`
- Imported by (local): `cv_compiler.cli`, `tests.test_build_example`, `tests.test_signatures`
- External import roots: `dataclasses`, `pathlib`

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
- Defines: `build_markdown`
- Imports (local): `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`, `cv_compiler.select.types` → `src/cv_compiler/select/types.py`
- Imported by (local): `cv_compiler.render.renderer`
- External import roots: (none)

### `src/cv_compiler/render/renderer.py`

- Module: `cv_compiler.render.renderer`
- Doc: Rendering interface for CV output.
- Defines: `_strip_markdown_markup`, `render_cv`, `render_markdown_to_pdf`
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
- Imported by (local): `cv_compiler.lint.linter`, `cv_compiler.llm.base`, `cv_compiler.llm.experience`, `cv_compiler.llm.manual`, `cv_compiler.llm.openai`, `cv_compiler.parse.loaders`, `cv_compiler.pipeline`, `cv_compiler.render.markdown`, `cv_compiler.render.types`, `cv_compiler.schema`, `cv_compiler.select.selector`, `tests.test_llm_manual_provider`, `tests.test_signatures`
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
- Imported by (local): `cv_compiler.explain`, `cv_compiler.render.markdown`, `cv_compiler.render.types`, `cv_compiler.select`, `cv_compiler.select.selector`, `tests.test_signatures`
- External import roots: `dataclasses`

### `src/cv_compiler/types.py`

- Module: `cv_compiler.types`
- Doc: Shared enums and lint issue types.
- Defines: `LintIssue`, `Severity`
- Imports (local): (none)
- Imported by (local): `cv_compiler.cli`, `cv_compiler.lint.linter`, `cv_compiler.pipeline`, `tests.test_build_example`, `tests.test_signatures`
- External import roots: `dataclasses`, `enum`, `pathlib`

### `tests/test_build_example.py`

- Module: `tests.test_build_example`
- Doc: Smoke tests for building the bundled example dataset.
- Defines: `TestBuildExample`, `_sha256`
- Imports (local): `cv_compiler.pipeline` → `src/cv_compiler/pipeline.py`, `cv_compiler.render.types` → `src/cv_compiler/render/types.py`, `cv_compiler.types` → `src/cv_compiler/types.py`
- Imported by (local): (none)
- External import roots: `hashlib`, `pathlib`, `tempfile`, `unittest`

### `tests/test_cli_parsing.py`

- Module: `tests.test_cli_parsing`
- Doc: Tests for CLI argument parsing.
- Defines: `TestCliParsing`
- Imports (local): `cv_compiler.cli` → `src/cv_compiler/cli.py`
- Imported by (local): (none)
- External import roots: `unittest`

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

### `tests/test_llm_experience_parsing.py`

- Module: `tests.test_llm_experience_parsing`
- Doc: Tests for parsing LLM experience responses with extra text.
- Defines: `TestLLMExperienceParsing`
- Imports (local): `cv_compiler.llm.experience` → `src/cv_compiler/llm/experience.py`
- Imported by (local): (none)
- External import roots: `unittest`

### `tests/test_llm_manual_provider.py`

- Module: `tests.test_llm_manual_provider`
- Doc: Tests for the manual/offline LLM provider.
- Defines: `TestManualProvider`
- Imports (local): `cv_compiler.llm.manual` → `src/cv_compiler/llm/manual.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): (none)
- External import roots: `json`, `pathlib`, `tempfile`, `unittest`

### `tests/test_profile_about_me.py`

- Module: `tests.test_profile_about_me`
- Doc: Tests for profile about_me parsing.
- Defines: `TestProfileAboutMe`, `_write`
- Imports (local): `cv_compiler.parse.loaders` → `src/cv_compiler/parse/loaders.py`
- Imported by (local): (none)
- External import roots: `pathlib`, `tempfile`, `unittest`

### `tests/test_signatures.py`

- Module: `tests.test_signatures`
- Doc: Signature-level tests for the scaffolded public API.
- Defines: `TestSignatures`
- Imports (local): `cv_compiler.explain` → `src/cv_compiler/explain.py`, `cv_compiler.lint.linter` → `src/cv_compiler/lint/linter.py`, `cv_compiler.llm.base` → `src/cv_compiler/llm/base.py`, `cv_compiler.parse.frontmatter` → `src/cv_compiler/parse/frontmatter.py`, `cv_compiler.parse.loaders` → `src/cv_compiler/parse/loaders.py`, `cv_compiler.pipeline` → `src/cv_compiler/pipeline.py`, `cv_compiler.render.renderer` → `src/cv_compiler/render/renderer.py`, `cv_compiler.render.types` → `src/cv_compiler/render/types.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`, `cv_compiler.select.selector` → `src/cv_compiler/select/selector.py`, `cv_compiler.select.types` → `src/cv_compiler/select/types.py`, `cv_compiler.types` → `src/cv_compiler/types.py`
- Imported by (local): (none)
- External import roots: `dataclasses`, `inspect`, `unittest`

## Other Files

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
- `data/README.md`
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
- `project_layout.md`
- `prompts/experience_prompt.md`
- `prompts/experience_templates.yaml`
- `pyproject.toml`
- `templates/README.md`
- `uv.lock`
