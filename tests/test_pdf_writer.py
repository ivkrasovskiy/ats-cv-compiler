"""
Behavior tests for pdf_writer._slugify and filename generation.

Focuses on edge cases that caused production bugs:
  - Cyrillic company names collapsing to "item" (all Russian CVs lost identity)
  - Very long LLM-generated names causing ENAMETOOLONG on the filesystem
  - Non-Latin scripts outside the Cyrillic table (fallback to stable hash)
"""

from __future__ import annotations

import json

from cv_compiler.ingest.pdf_parser import parse_ingest_response
from cv_compiler.ingest.pdf_writer import _slugify, write_ingest_files

# ── _slugify unit tests ────────────────────────────────────────────────────────


def test_slugify_cyrillic_is_transliterated():
    assert _slugify("Газпром") == "gazprom"


def test_slugify_cyrillic_mixed_with_ascii():
    result = _slugify("Газпром Corp")
    assert "gazprom" in result
    assert "corp" in result


def test_slugify_accented_latin_is_normalized():
    # NFKD normalization: é → e
    assert _slugify("Société") == "societe"


def test_slugify_long_ascii_is_capped_at_50():
    long_text = "a" * 200
    result = _slugify(long_text)
    assert len(result) <= 50


def test_slugify_long_mixed_name_is_capped():
    name = "International Business Machines Corporation - Senior Principal Software Engineer"
    result = _slugify(name)
    assert len(result) <= 50
    assert result  # not empty


def test_slugify_pure_cyrillic_long_is_capped():
    # 100-char Cyrillic string → transliterated then capped
    text = "Международная Корпорация Технологий и Инноваций"
    result = _slugify(text)
    assert len(result) <= 50
    assert result.isascii()


def test_slugify_non_latin_non_cyrillic_returns_stable_hash():
    # Chinese — no transliteration rule, must fall back to hash
    result1 = _slugify("腾讯科技")
    result2 = _slugify("腾讯科技")
    assert result1 == result2  # stable
    assert result1.startswith("item_")
    assert len(result1) <= 50
    assert result1.isascii()


def test_slugify_empty_string_returns_item():
    assert _slugify("").startswith("item")


def test_slugify_only_punctuation_returns_item():
    result = _slugify("---///***")
    assert result.startswith("item")


# ── filename generation integration tests ─────────────────────────────────────


def _response_with_experience(company: str, title: str) -> str:
    return json.dumps(
        {
            "profile": {
                "name": "Ivan Petrov",
                "headline": "Engineer",
                "location": "Moscow",
                "email": "ivan@example.com",
                "links": [],
                "about_me": "Experienced backend engineer.",
            },
            "experience": [
                {
                    "company": company,
                    "title": title,
                    "location": "Moscow",
                    "start_date": "2020-01",
                    "end_date": "",
                    "bullets": ["Built systems."],
                    "tags": ["python"],
                }
            ],
            "projects": [],
            "skills": [{"name": "Languages", "items": ["Python"]}],
            "education": [],
        }
    )


def test_cyrillic_company_name_creates_file(tmp_path):
    parsed = parse_ingest_response(_response_with_experience("Газпром", "Старший инженер"))
    write_ingest_files(tmp_path, parsed, overwrite=False)
    proj_files = list((tmp_path / "projects").glob("*.md"))
    assert len(proj_files) == 1
    # Filename must be valid ASCII (no raw Cyrillic bytes)
    assert proj_files[0].name.isascii()


def test_cyrillic_filename_contains_transliterated_name(tmp_path):
    parsed = parse_ingest_response(_response_with_experience("Газпром", "Инженер"))
    write_ingest_files(tmp_path, parsed, overwrite=False)
    proj_files = list((tmp_path / "projects").glob("*.md"))
    # "Газпром" → "gazprom" should appear in the filename
    assert any("gazprom" in f.stem for f in proj_files)


def test_long_company_name_does_not_raise(tmp_path):
    long_name = "Extremely Long Company Name That Keeps Going " * 6  # ~270 chars
    parsed = parse_ingest_response(_response_with_experience(long_name, "Engineer"))
    # Must not raise OSError / ENAMETOOLONG
    write_ingest_files(tmp_path, parsed, overwrite=False)
    proj_files = list((tmp_path / "projects").glob("*.md"))
    assert len(proj_files) == 1


def test_long_name_filename_under_255_bytes(tmp_path):
    long_name = "Acme " * 60  # 300 chars
    parsed = parse_ingest_response(_response_with_experience(long_name, "Engineer"))
    write_ingest_files(tmp_path, parsed, overwrite=False)
    for f in (tmp_path / "projects").glob("*.md"):
        assert len(f.name.encode()) <= 255


def test_multiple_cyrillic_companies_get_distinct_filenames(tmp_path):
    payload = {
        "profile": {
            "name": "Ivan",
            "headline": "Eng",
            "location": "RU",
            "email": "i@i.com",
            "links": [],
            "about_me": "Engineer.",
        },
        "experience": [
            {
                "company": "Газпром",
                "title": "Инженер",
                "location": "",
                "start_date": "2020-01",
                "end_date": "",
                "bullets": ["A."],
                "tags": [],
            },
            {
                "company": "Сбербанк",
                "title": "Разработчик",
                "location": "",
                "start_date": "2018-01",
                "end_date": "2020-01",
                "bullets": ["B."],
                "tags": [],
            },
        ],
        "projects": [],
        "skills": [],
        "education": [],
    }
    parsed = parse_ingest_response(json.dumps(payload))
    write_ingest_files(tmp_path, parsed, overwrite=False)
    proj_files = list((tmp_path / "projects").glob("*.md"))
    assert len(proj_files) == 2
    stems = {f.stem for f in proj_files}
    assert len(stems) == 2  # distinct filenames
