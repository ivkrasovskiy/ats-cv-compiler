from pathlib import Path

from app.backend.services.file_service import get_project_root

CONFIG_GROUPS = {
    "basic": [
        "CV_AI_PROVIDER",
        "CV_GEMINI_MODEL",
        "CV_AGENT_CHAIN_ENABLED",
        "CV_AGENT_MAX_BULLET_CHARS",
        "CV_AGENT_MAX_SUMMARY_CHARS",
        "CV_AGENT_KEYWORD_COVERAGE_MIN",
        "CV_REPAIR_MODE",
    ],
    "advanced_llm": [
        "CV_LLM_BASE_URL",
        "CV_LLM_API_KEY",
        "CV_LLM_MODEL",
        "CV_LLM_MODE",
        "CV_LLM_TIMEOUT_SECONDS",
    ],
    "advanced_timeouts": [
        "CV_AGENT_TIMEOUT_JOB_ANALYSIS",
        "CV_AGENT_TIMEOUT_EXPERIENCE",
        "CV_AGENT_TIMEOUT_SKILLS",
        "CV_AGENT_TIMEOUT_BULLET_POLISH",
        "CV_AGENT_TIMEOUT_SUMMARY",
    ],
}


def _env_path() -> Path:
    return get_project_root() / "config" / "llm.env"


def read_config() -> dict:
    from cv_compiler.llm.config import read_env_file

    values = read_env_file(_env_path())
    result = {}
    for group, keys in CONFIG_GROUPS.items():
        result[group] = {k: values.get(k, "") for k in keys}
    return result


def write_config(data: dict) -> None:
    from cv_compiler.llm.config import upsert_env_value

    env_path = _env_path()
    for _group, kvs in data.items():
        for key, value in kvs.items():
            upsert_env_value(env_path, key, str(value))
