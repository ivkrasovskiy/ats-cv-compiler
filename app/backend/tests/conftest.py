import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("CV_PROJECT_ROOT", str(tmp_path))

    # Seed with example data so file-tree tests have real files
    src = Path("examples/basic/data")
    if src.exists():
        shutil.copytree(src, tmp_path / "data")
    else:
        (tmp_path / "data").mkdir()

    (tmp_path / "jobs").mkdir(exist_ok=True)
    (tmp_path / "out").mkdir(exist_ok=True)

    # Import after env is patched so get_project_root() picks it up
    from app.backend.main import create_app

    return TestClient(create_app())
