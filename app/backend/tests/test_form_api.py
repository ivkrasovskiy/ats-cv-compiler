"""Tests for the form API endpoints."""

from __future__ import annotations

# ── GET form tests ─────────────────────────────────────────────────────────────


def test_get_profile_form(client):
    r = client.get("/api/files/data/profile.md/form")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "profile"
    fields = data["fields"]
    assert "name" in fields
    assert "headline" in fields
    assert "email" in fields
    assert "location" in fields
    assert "about_me" in fields
    assert "links" in fields
    assert isinstance(fields["links"], list)


def test_get_skills_form(client):
    r = client.get("/api/files/data/skills.md/form")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "skills"
    assert "categories" in data["fields"]
    assert isinstance(data["fields"]["categories"], list)


def test_get_education_form(client):
    r = client.get("/api/files/data/education.md/form")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "education"
    assert "entries" in data["fields"]
    assert "languages" in data["fields"]


def test_get_experience_form(client):
    r = client.get("/api/files/data/experience/2023-example-corp.md/form")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "experience"
    fields = data["fields"]
    for key in ("company", "title", "start_date", "tags", "bullets"):
        assert key in fields


def test_get_project_form(client):
    r = client.get("/api/files/data/projects/cli-cv-compiler.md/form")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "project"
    fields = data["fields"]
    for key in ("name", "tags", "bullets"):
        assert key in fields


def test_get_unknown_type_returns_400(client):
    r = client.get("/api/files/data/some_random_file.md/form")
    assert r.status_code == 400


# ── PUT form round-trip tests ──────────────────────────────────────────────────


def test_put_profile_form_round_trips(client):
    """GET → PUT → GET should preserve key fields."""
    get1 = client.get("/api/files/data/profile.md/form").json()
    fields = get1["fields"]
    fields["name"] = "Test User"

    put_r = client.put("/api/files/data/profile.md/form", json={"fields": fields})
    assert put_r.status_code == 200
    assert put_r.json()["saved"] is True

    get2 = client.get("/api/files/data/profile.md/form").json()
    assert get2["fields"]["name"] == "Test User"


def test_put_skills_form_round_trips(client):
    get1 = client.get("/api/files/data/skills.md/form").json()
    fields = get1["fields"]
    # Modify a category name
    if fields["categories"]:
        fields["categories"][0]["name"] = "Updated Category"

    put_r = client.put("/api/files/data/skills.md/form", json={"fields": fields})
    assert put_r.status_code == 200

    get2 = client.get("/api/files/data/skills.md/form").json()
    if get2["fields"]["categories"]:
        assert get2["fields"]["categories"][0]["name"] == "Updated Category"


def test_put_experience_form_round_trips(client):
    path = "experience/2023-example-corp.md"
    get1 = client.get(f"/api/files/data/{path}/form").json()
    fields = get1["fields"]
    original_company = fields["company"]
    fields["company"] = "New Company"

    put_r = client.put(f"/api/files/data/{path}/form", json={"fields": fields})
    assert put_r.status_code == 200

    get2 = client.get(f"/api/files/data/{path}/form").json()
    assert get2["fields"]["company"] == "New Company"
    _ = original_company  # silence unused var


def test_put_profile_missing_required_returns_422(client):
    r = client.put(
        "/api/files/data/profile.md/form",
        json={
            "fields": {
                "name": "",
                "headline": "",
                "location": "",
                "about_me": "",
                "links": [],
            }
        },
    )
    assert r.status_code == 422


def test_put_experience_missing_required_returns_422(client):
    r = client.put(
        "/api/files/data/experience/2023-example-corp.md/form",
        json={
            "fields": {
                "company": "",
                "title": "",
                "start_date": "",
                "tags": [],
                "bullets": [],
            }
        },
    )
    assert r.status_code == 422


def test_put_unknown_type_returns_400(client):
    r = client.put("/api/files/data/some_random_file.md/form", json={"fields": {}})
    assert r.status_code == 400
