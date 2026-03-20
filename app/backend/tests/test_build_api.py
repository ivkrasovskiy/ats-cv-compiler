import time


def test_build_returns_202_with_job_id(client):
    r = client.post("/api/build", json={"job": None, "llm": "none"})
    assert r.status_code == 202
    data = r.json()
    assert "job_id" in data
    assert len(data["job_id"]) == 36  # UUID4


def test_build_status_is_valid(client):
    r = client.post("/api/build", json={"job": None, "llm": "none"})
    job_id = r.json()["job_id"]

    r2 = client.get(f"/api/build/{job_id}")
    assert r2.status_code == 200
    assert r2.json()["status"] in ("running", "done", "error")
    assert r2.json()["job_id"] == job_id


def test_build_status_not_found(client):
    r = client.get("/api/build/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_build_stream_not_found(client):
    r = client.get("/api/build/00000000-0000-0000-0000-000000000000/stream")
    assert r.status_code == 404


def test_build_completes_and_has_exit_code(client):
    """Build should eventually settle to done/error with an exit_code."""
    r = client.post("/api/build", json={"job": None, "llm": "none"})
    job_id = r.json()["job_id"]

    # Poll up to 60 s for completion
    for _ in range(120):
        status = client.get(f"/api/build/{job_id}").json()
        if status["status"] != "running":
            break
        time.sleep(0.5)

    assert status["status"] in ("done", "error")
    assert status["exit_code"] is not None


def test_build_with_cover_letter_flag_returns_202(client):
    """POST /api/build with cover_letter: true should be accepted."""
    r = client.post("/api/build", json={"job": None, "llm": "none", "cover_letter": True})
    assert r.status_code == 202
    data = r.json()
    assert "job_id" in data
    assert len(data["job_id"]) == 36
