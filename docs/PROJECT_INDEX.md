# Project Index

Deterministic index of files + local import connections (includes tests).

## Overview

- Python modules indexed: 25
- Other files indexed: 22

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
- Defines: `_build_parser`, `_resolve_example_root`, `main`
- Imports (local): `cv_compiler.pipeline` → `src/cv_compiler/pipeline.py`, `cv_compiler.render.types` → `src/cv_compiler/render/types.py`
- Imported by (local): `cv_compiler.__main__`, `tests.test_cli_parsing`
- External import roots: `argparse`, `collections`, `pathlib`, `sys`

### `src/cv_compiler/explain.py`

- Module: `cv_compiler.explain`
- Doc: Formatting helpers for selection explanations.
- Defines: `format_selection_explanation`
- Imports (local): `cv_compiler.select.types` → `src/cv_compiler/select/types.py`
- Imported by (local): `tests.test_signatures`
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
- Imported by (local): `cv_compiler.lint`, `tests.test_signatures`
- External import roots: `collections`, `pathlib`

### `src/cv_compiler/llm/__init__.py`

- Module: `cv_compiler.llm`
- Doc: Optional LLM interfaces and providers.
- Defines: (none)
- Imports (local): `cv_compiler.llm.base` → `src/cv_compiler/llm/base.py`
- Imported by (local): (none)
- External import roots: (none)

### `src/cv_compiler/llm/base.py`

- Module: `cv_compiler.llm.base`
- Doc: Optional LLM provider protocol and request types.
- Defines: `BulletRewriteRequest`, `BulletRewriteResult`, `LLMProvider`, `NoopProvider`
- Imports (local): (none)
- Imported by (local): `cv_compiler.llm`, `cv_compiler.pipeline`, `tests.test_signatures`
- External import roots: `collections`, `dataclasses`, `typing`

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
- Imported by (local): `tests.test_signatures`
- External import roots: `collections`, `dataclasses`, `pathlib`, `typing`

### `src/cv_compiler/parse/loaders.py`

- Module: `cv_compiler.parse.loaders`
- Doc: Load canonical data and job specs from disk.
- Defines: `load_canonical_data`, `load_job_spec`
- Imports (local): `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`
- Imported by (local): `cv_compiler.parse`, `tests.test_signatures`
- External import roots: `pathlib`

### `src/cv_compiler/pipeline.py`

- Module: `cv_compiler.pipeline`
- Doc: Build pipeline request/response types and entrypoint.
- Defines: `BuildRequest`, `BuildResult`, `build_cv`
- Imports (local): `cv_compiler.llm.base` → `src/cv_compiler/llm/base.py`, `cv_compiler.render.types` → `src/cv_compiler/render/types.py`, `cv_compiler.types` → `src/cv_compiler/types.py`
- Imported by (local): `cv_compiler.cli`, `tests.test_signatures`
- External import roots: `dataclasses`, `pathlib`

### `src/cv_compiler/render/__init__.py`

- Module: `cv_compiler.render`
- Doc: Rendering interfaces for producing ATS-safe outputs.
- Defines: (none)
- Imports (local): `cv_compiler.render.renderer` → `src/cv_compiler/render/renderer.py`, `cv_compiler.render.types` → `src/cv_compiler/render/types.py`
- Imported by (local): (none)
- External import roots: (none)

### `src/cv_compiler/render/renderer.py`

- Module: `cv_compiler.render.renderer`
- Doc: Rendering interface for CV output.
- Defines: `render_cv`
- Imports (local): `cv_compiler.render.types` → `src/cv_compiler/render/types.py`
- Imported by (local): `cv_compiler.render`, `tests.test_signatures`
- External import roots: (none)

### `src/cv_compiler/render/types.py`

- Module: `cv_compiler.render.types`
- Doc: Rendering request/response types.
- Defines: `RenderFormat`, `RenderRequest`, `RenderResult`
- Imports (local): `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`, `cv_compiler.select.types` → `src/cv_compiler/select/types.py`
- Imported by (local): `cv_compiler.cli`, `cv_compiler.pipeline`, `cv_compiler.render`, `cv_compiler.render.renderer`, `tests.test_signatures`
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
- Imported by (local): `cv_compiler.lint.linter`, `cv_compiler.parse.loaders`, `cv_compiler.render.types`, `cv_compiler.schema`, `cv_compiler.select.selector`, `tests.test_signatures`
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
- Defines: `select_content`
- Imports (local): `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`, `cv_compiler.select.types` → `src/cv_compiler/select/types.py`
- Imported by (local): `cv_compiler.select`, `tests.test_signatures`
- External import roots: (none)

### `src/cv_compiler/select/types.py`

- Module: `cv_compiler.select.types`
- Doc: Selection result and decision types.
- Defines: `SelectionDecision`, `SelectionResult`
- Imports (local): (none)
- Imported by (local): `cv_compiler.explain`, `cv_compiler.render.types`, `cv_compiler.select`, `cv_compiler.select.selector`, `tests.test_signatures`
- External import roots: `dataclasses`

### `src/cv_compiler/types.py`

- Module: `cv_compiler.types`
- Doc: Shared enums and lint issue types.
- Defines: `LintIssue`, `Severity`
- Imports (local): (none)
- Imported by (local): `cv_compiler.lint.linter`, `cv_compiler.pipeline`, `tests.test_signatures`
- External import roots: `dataclasses`, `enum`, `pathlib`

### `tests/test_cli_parsing.py`

- Module: `tests.test_cli_parsing`
- Doc: Tests for CLI argument parsing.
- Defines: `TestCliParsing`
- Imports (local): `cv_compiler.cli` → `src/cv_compiler/cli.py`
- Imported by (local): (none)
- External import roots: `unittest`

### `tests/test_signatures.py`

- Module: `tests.test_signatures`
- Doc: Signature-level tests for the scaffolded public API.
- Defines: `TestSignatures`
- Imports (local): `cv_compiler.explain` → `src/cv_compiler/explain.py`, `cv_compiler.lint.linter` → `src/cv_compiler/lint/linter.py`, `cv_compiler.llm.base` → `src/cv_compiler/llm/base.py`, `cv_compiler.parse.frontmatter` → `src/cv_compiler/parse/frontmatter.py`, `cv_compiler.parse.loaders` → `src/cv_compiler/parse/loaders.py`, `cv_compiler.pipeline` → `src/cv_compiler/pipeline.py`, `cv_compiler.render.renderer` → `src/cv_compiler/render/renderer.py`, `cv_compiler.render.types` → `src/cv_compiler/render/types.py`, `cv_compiler.schema.models` → `src/cv_compiler/schema/models.py`, `cv_compiler.select.selector` → `src/cv_compiler/select/selector.py`, `cv_compiler.select.types` → `src/cv_compiler/select/types.py`, `cv_compiler.types` → `src/cv_compiler/types.py`
- Imported by (local): (none)
- External import roots: `dataclasses`, `inspect`, `unittest`

## Other Files

- `.gitignore`
- `AGENTS.md`
- `LICENSE`
- `README.md`
- `REQUIREMENTS.md`
- `data/README.md`
- `docs/ENTITIES.md`
- `docs/PROJECT_INDEX.md`
- `examples/README.md`
- `examples/basic/README.md`
- `examples/basic/data/education.md`
- `examples/basic/data/experience/2023-example-corp.md`
- `examples/basic/data/profile.md`
- `examples/basic/data/projects/cli-cv-compiler.md`
- `examples/basic/data/skills.md`
- `examples/basic/jobs/backend_engineer.md`
- `examples/basic/templates/README.md`
- `jobs/README.md`
- `project_layout.md`
- `pyproject.toml`
- `templates/README.md`
- `uv.lock`
