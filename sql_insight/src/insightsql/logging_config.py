"""Redacted application logging configuration."""

import logging


def configure_logging() -> None:
    """Configure concise logs without prompts, SQL, query results, or secrets."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
