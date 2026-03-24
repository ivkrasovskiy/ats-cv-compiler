import shutil
import subprocess


def gh_available() -> bool:
    return shutil.which("gh") is not None


def create_issue(title: str, body: str) -> str:
    """Create a GitHub issue and return its URL."""
    result = subprocess.run(
        ["gh", "issue", "create", "--title", title, "--body", body],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh issue create failed: {result.stderr.strip()}")
    return result.stdout.strip()
