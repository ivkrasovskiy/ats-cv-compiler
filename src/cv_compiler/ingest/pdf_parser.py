"""Parse LLM JSON responses into structured CV data models."""

from __future__ import annotations

import json

from .pdf_models import (
    ParsedCv,
    ParsedEducation,
    ParsedExperience,
    ParsedLink,
    ParsedProfile,
    ParsedProject,
    ParsedSkillCategory,
)


def parse_ingest_response(text: str) -> ParsedCv:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM response must be valid JSON") from exc
    return parse_ingest_payload(payload)


def parse_ingest_payload(payload: object) -> ParsedCv:
    if not isinstance(payload, dict):
        raise ValueError("Ingest payload must be a JSON object")

    profile_raw = payload.get("profile")
    if not isinstance(profile_raw, dict):
        raise ValueError("Missing or invalid profile section")

    links = _parse_links(profile_raw.get("links"))
    email = _coerce_str(profile_raw.get("email"))

    # LLMs often put email as a mailto: link — normalise
    clean_links: list[ParsedLink] = []
    for link in links:
        if link.url and link.url.startswith("mailto:"):
            addr = link.url[len("mailto:"):]
            if addr and not email:
                email = addr
        else:
            clean_links.append(link)

    profile = ParsedProfile(
        name=_coerce_str(profile_raw.get("name")),
        headline=_coerce_str(profile_raw.get("headline")),
        location=_coerce_str(profile_raw.get("location")),
        email=email,
        about_me=_coerce_str(profile_raw.get("about_me")),
        links=tuple(clean_links),
    )

    return ParsedCv(
        profile=profile,
        experience=_parse_experience(payload.get("experience")),
        projects=_parse_projects(payload.get("projects")),
        skills=_parse_skills(payload.get("skills")),
        education=_parse_education(payload.get("education")),
    )


def _parse_links(value: object) -> tuple[ParsedLink, ...]:
    if not isinstance(value, list):
        return ()
    links: list[ParsedLink] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        links.append(ParsedLink(
            label=_coerce_str(item.get("label")),
            url=_coerce_str(item.get("url")),
        ))
    return tuple(links)


def _parse_experience(value: object) -> tuple[ParsedExperience, ...]:
    if not isinstance(value, list):
        return ()
    items: list[ParsedExperience] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        items.append(ParsedExperience(
            company=_coerce_str(item.get("company")),
            title=_coerce_str(item.get("title")),
            location=_coerce_str(item.get("location")),
            start_date=_coerce_str(item.get("start_date")),
            end_date=_coerce_str(item.get("end_date")),
            bullets=_coerce_str_list(item.get("bullets")),
            tags=_coerce_str_list(item.get("tags")),
        ))
    return tuple(items)


def _parse_projects(value: object) -> tuple[ParsedProject, ...]:
    if not isinstance(value, list):
        return ()
    items: list[ParsedProject] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        items.append(ParsedProject(
            name=_coerce_str(item.get("name")),
            company=_coerce_str(item.get("company")),
            role=_coerce_str(item.get("role")),
            start_date=_coerce_str(item.get("start_date")),
            end_date=_coerce_str(item.get("end_date")),
            bullets=_coerce_str_list(item.get("bullets")),
            tags=_coerce_str_list(item.get("tags")),
        ))
    return tuple(items)


def _parse_skills(value: object) -> tuple[ParsedSkillCategory, ...]:
    if not isinstance(value, list):
        return ()
    items: list[ParsedSkillCategory] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        items.append(ParsedSkillCategory(
            name=_coerce_str(item.get("name")),
            items=_coerce_str_list(item.get("items")),
        ))
    return tuple(items)


def _parse_education(value: object) -> tuple[ParsedEducation, ...]:
    if not isinstance(value, list):
        return ()
    items: list[ParsedEducation] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        items.append(ParsedEducation(
            institution=_coerce_str(item.get("institution")),
            degree=_coerce_str(item.get("degree")),
            location=_coerce_str(item.get("location")),
            start_date=_coerce_str(item.get("start_date")),
            end_date=_coerce_str(item.get("end_date")),
        ))
    return tuple(items)


def _coerce_str(value: object) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        return text if text else None
    return None


def _coerce_str_list(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    items: list[str] = []
    for item in value:
        if isinstance(item, str):
            text = item.strip()
            if text:
                items.append(text)
    return tuple(items)
