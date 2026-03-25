# Behavior-Based Test Plan

**Principle:** every test starts with a concrete input and asserts a concrete observable
output — files written, error messages, return values. No mocking of internal logic.
Tests describe what the system *should* do, not how it currently implements it.

---

## What is already covered (skip)

- CLI argument parsing — `tests/test_cli_parsing.py`
- Deterministic build with example data — `tests/test_build_example.py`
- YAML frontmatter writing helpers — `tests/test_pdf_ingest.py`
- Provider resolution + model config — `tests/test_pdf_ingest.py::TestProviderResolution`
- Backend API ingest endpoint — `app/backend/tests/test_ingest_api.py`

---

## 1. PDF Ingest — `ingest_pdf_to_markdown()`

**File:** `tests/test_ingest_behavior.py`
**Mode:** `llm_mode="offline"` — write a fixture JSON response, call the function, assert files.
No subprocess or network calls needed.

| # | Test | Input | Expected output |
|---|------|-------|----------------|
| 1 | `test_profile_md_written_with_correct_fields` | Valid LLM response with name/headline/email/links | `data/profile.md` exists; frontmatter has correct name, email, links |
| 2 | `test_skills_md_written_with_categories` | Response with 2 skill categories | `data/skills.md` has both categories with all items |
| 3 | `test_one_project_file_per_experience_entry` | Response with 3 experience entries | 3 files in `data/projects/`; each has correct company and bullets |
| 4 | `test_education_md_written_with_all_entries` | Response with 2 degrees + 1 language entry | `data/education.md` frontmatter has 3 entries |
| 5 | `test_empty_experience_writes_no_project_files` | Response with `experience=[]`, `projects=[]` | `data/projects/` is empty or absent |
| 6 | `test_empty_name_produces_warning` | Response with `profile.name = ""` | `IngestResult.warnings` contains a string mentioning "name" |
| 7 | `test_overwrite_true_removes_old_project_files` | Old `data/projects/old.md` exists, `overwrite=True` | `old.md` gone; new project files present |
| 8 | `test_overwrite_false_keeps_old_project_files` | Old `data/projects/old.md` exists, `overwrite=False` | `old.md` still present |
| 9 | `test_invalid_json_response_raises` | Offline response file contains non-JSON text | `ValueError` raised |
| 10 | `test_cli_command_not_found_raises` | `CodexExecConfig(command="nonexistent_cli_xyz")` | `ValueError` with "not found" / "PATH" in message |
| 11 | `test_cli_nonzero_exit_includes_stderr` | CLI exits code 1, stderr = "quota exceeded" | `ValueError` message includes "quota exceeded" |
| 12 | `test_mailto_links_excluded_from_profile_links` | Response where `links` includes a mailto entry | Written `profile.md` links do not contain any mailto URL |
| 13 | `test_written_paths_returned_in_result` | Valid response, 3 experience entries | `IngestResult.written_paths` includes profile, skills, education, project files |
| 14 | `test_all_returned_paths_exist_on_disk` | Valid response | Every path in `result.written_paths` exists on disk |

---

## 2. CV Generation — `build_cv(BuildRequest)`

**File:** `tests/test_build_behavior.py`
Data source: `examples/basic/data/` (golden fixture, read-only).
LLM: `NoopProvider` (already in codebase) or `llm=None` — fully deterministic.

| # | Test | Input | Expected output |
|---|------|-------|----------------|
| 1 | `test_generic_build_produces_pdf` | `job_path=None`, default settings | `out/cv_generic.pdf` exists and is > 1 KB |
| 2 | `test_generic_build_produces_markdown` | `format=MARKDOWN` | `out/cv_generic.md` contains candidate's name from profile |
| 3 | `test_job_targeted_build_uses_job_id_in_filename` | `job_path=jobs/example.md` | Output file is `cv_<job_id>.pdf`, not `cv_generic.pdf` |
| 4 | `test_valid_build_has_no_error_issues` | Valid example data, `llm=None` | `BuildResult.issues` has zero ERROR-severity entries |
| 5 | `test_missing_profile_returns_error_issue` | `data/profile.md` removed from temp copy | `BuildResult.issues` has ≥ 1 ERROR; message mentions "profile" |
| 6 | `test_build_from_markdown_produces_pdf` | `render_from_markdown=<existing .md>` | PDF produced without re-reading data files |
| 7 | `test_build_from_markdown_nonexistent_path_errors` | `render_from_markdown=Path("ghost.md")` | `ValueError` raised or ERROR issue returned |
| 8 | `test_noop_llm_produces_same_output_as_no_llm` | `llm=NoopProvider()` vs `llm=None` | Both produce identical output bytes |
| 9 | `test_llm_failure_is_warning_not_error` | LLM provider raises on `generate_experience` | Build completes; result has WARNING, not ERROR; PDF still written |
| 10 | `test_build_is_deterministic` | Same input, called twice | Both output PDFs are byte-for-byte identical |
| 11 | `test_job_build_output_contains_job_keyword` | Job with keyword "Kubernetes" present in data skills | Output markdown contains "Kubernetes" |
| 12 | `test_markdown_output_contains_candidate_name` | `format=MARKDOWN` | Output `.md` contains the name from `profile.md` |

---

## 3. LLM Provider Contract

**File:** `tests/test_llm_provider_contract.py`
Tests run against real implementations with controlled inputs.

| # | Test | Input | Expected output |
|---|------|-------|----------------|
| 1 | `test_noop_rewrite_returns_bullets_unchanged` | `BulletRewriteRequest(id="x", bullets=("a","b"))` | Same bullets returned, same id |
| 2 | `test_noop_generate_experience_returns_empty` | Any projects sequence | Empty sequence returned |
| 3 | `test_noop_highlight_skills_returns_empty` | Any skills list | Empty sequence returned |
| 4 | `test_manual_highlight_skills_ignores_unknown_skills` | Response JSON lists skills not in allowed input | Only skills from allowed input are returned |
| 5 | `test_manual_highlight_skills_caps_at_five` | Response JSON lists 10 skills, all valid | At most 5 returned |
| 6 | `test_codex_config_default_command` | `CodexExecConfig.from_env()` with empty env file | `command == "codex"` |
| 7 | `test_codex_config_env_var_overrides_file` | Both env var and `.env` file set same key differently | Env var value wins |
| 8 | `test_codex_config_invalid_timeout_uses_default` | `CV_CODEX_TIMEOUT_SECONDS=notanumber` | `timeout_seconds` is 300 or 600 (not a crash) |
| 9 | `test_codex_config_invalid_prompt_mode_defaults_to_stdin` | `CV_CODEX_PROMPT_MODE=badvalue` | `prompt_mode == "stdin"` |
| 10 | `test_provider_gemini_default_model_is_flash` | `CV_AI_PROVIDER=gemini`, no `CV_GEMINI_MODEL` | `codex_config.model == "gemini-2.0-flash"` |
| 11 | `test_provider_custom_without_base_url_returns_none_llm_config` | `CV_AI_PROVIDER=custom`, no `CV_LLM_BASE_URL` | `llm_config is None` |
| 12 | `test_provider_unknown_falls_back_to_api_mode` | `CV_AI_PROVIDER=someunknownvalue` | `ingest_mode == "api"` |

---

## 4. Data Loading & Lint

**File:** `tests/test_lint_behavior.py`
Uses temp copies of `examples/basic/data/` with targeted mutations.

| # | Test | Input | Expected output |
|---|------|-------|----------------|
| 1 | `test_valid_example_has_no_errors` | `examples/basic/data/` unchanged | Zero ERROR-severity `LintIssue`s |
| 2 | `test_missing_name_produces_error` | `profile.md` with `name: ""` | ≥ 1 ERROR mentioning "name" |
| 3 | `test_duplicate_experience_ids_produces_error` | Two experience files with same `id:` value | ≥ 1 ERROR mentioning "duplicate" or the shared id |
| 4 | `test_bullet_over_limit_produces_warning` | Experience file with a 500-char bullet | ≥ 1 WARNING mentioning bullet length or the file |
| 5 | `test_missing_skills_file_raises` | `data/skills.md` deleted | `ValueError` or `FileNotFoundError` raised |

---

## Implementation notes

- **Offline mode for ingest tests**: write a fixture JSON to a temp file, pass as
  `response_path=`. No CLI or API keys needed.
- **`NoopProvider`** for build tests: already in codebase, makes all LLM paths
  deterministic no-ops.
- **`examples/basic/data/`** as golden fixture: copy to `tmp_path` per test so mutations
  don't affect other tests.
- **Avoid**: mocking `subprocess.run`, patching `ingest_pdf_to_markdown`, asserting on
  call counts. Assert on observable state only.
- **Error messages**: assert substrings (`"quota" in str(exc)`), not exact strings — allows
  messages to be improved without breaking tests.

---

## Files to create

| File | Section |
|------|---------|
| `tests/test_ingest_behavior.py` | §1 PDF Ingest |
| `tests/test_build_behavior.py` | §2 CV Generation |
| `tests/test_llm_provider_contract.py` | §3 LLM Provider |
| `tests/test_lint_behavior.py` | §4 Lint |
