"""Application configuration and safe defaults."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from insightsql.exceptions import ConfigurationError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT.parent / "DB_INSIGHT" / "employee_management.db"
DEFAULT_MODEL = "gpt-4o-mini"
MAX_QUESTION_LENGTH = 2_000
MAX_SQL_LENGTH = 20_000
MAX_RESULT_ROWS = 1_000
QUERY_TIMEOUT_SECONDS = 5


def get_database_path() -> Path:
    """Resolve the configured database path, defaulting to the sibling sample DB."""
    raw_path = os.environ.get("INSIGHTSQL_DB_PATH")
    path = Path(raw_path).expanduser() if raw_path else DEFAULT_DATABASE_PATH
    return path.resolve()


def get_openai_api_key() -> str | None:
    """Read the OpenAI key from the environment or local Streamlit secrets."""
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if key:
        return key

    secrets_path = PROJECT_ROOT / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        return None

    try:
        secrets = tomllib.loads(secrets_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ConfigurationError("Could not read .streamlit/secrets.toml.") from error

    secret_key = secrets.get("OPENAI_API_KEY")
    if not isinstance(secret_key, str) or not secret_key.strip():
        return None
    return secret_key.strip()


def get_model_name() -> str:
    """Return the configured OpenAI model name."""
    return os.environ.get("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
