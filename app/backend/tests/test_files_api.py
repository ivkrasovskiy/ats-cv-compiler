def test_list_data_files_returns_list(client):
    r = client.get("/api/files/data")
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    paths = [f["path"] for f in items]
    assert any("profile.md" in p for p in paths)


def test_get_data_file_returns_content(client):
    r = client.get("/api/files/data/profile.md")
    assert r.status_code == 200
    data = r.json()
    assert "content" in data
    assert len(data["content"]) > 0


def test_put_data_file_saves_content(client):
    payload = "---\nid: test\n---\n"
    r = client.put("/api/files/data/profile.md", json={"content": payload})
    assert r.status_code == 200
    assert r.json()["saved"] is True

    r2 = client.get("/api/files/data/profile.md")
    assert r2.json()["content"] == payload


def test_file_path_traversal_rejected(client):
    r = client.get("/api/files/data/../pyproject.toml")
    assert r.status_code in (400, 404)


def test_list_jobs_starts_empty(client):
    r = client.get("/api/files/jobs")
    assert r.status_code == 200
    assert r.json() == []


def test_job_file_full_crud(client):
    content = "# Software Engineer\nBuild cool things."

    # Create
    r = client.put("/api/files/jobs/acme.md", json={"content": content})
    assert r.status_code == 200

    # Read
    r = client.get("/api/files/jobs/acme.md")
    assert r.status_code == 200
    assert r.json()["content"] == content

    # List
    r = client.get("/api/files/jobs")
    assert any(f["name"] == "acme.md" for f in r.json())

    # Delete
    r = client.delete("/api/files/jobs/acme.md")
    assert r.status_code == 200

    # Confirm gone
    r = client.get("/api/files/jobs/acme.md")
    assert r.status_code == 404


def test_delete_missing_job_returns_404(client):
    r = client.delete("/api/files/jobs/nonexistent.md")
    assert r.status_code == 404


def test_list_out_files(client):
    r = client.get("/api/out")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_out_file_not_found(client):
    r = client.get("/api/out/missing.pdf")
    assert r.status_code == 404
