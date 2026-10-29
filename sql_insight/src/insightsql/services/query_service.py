"""Orchestrate question-to-SQL generation, validation, and execution."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol

from insightsql.config import MAX_QUESTION_LENGTH
from insightsql.exceptions import ModelConfigurationError, SQLValidationError
from insightsql.security.sql_validator import validate_select_sql

_SQL_INPUT_PATTERN = re.compile(
    r"\A\s*(?:(?:--[^\r\n]*(?:\r?\n|$))|(?:/\*.*?\*/\s*))*\s*"
    r"(SELECT|WITH|INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|PRAGMA|ATTACH|REPLACE)\b",
    re.IGNORECASE | re.DOTALL,
)


class SQLGenerator(Protocol):
    """Interface implemented by the OpenAI adapter and test fakes."""

    def generate_sql(self, question: str, schema_context: str) -> str: ...


class QueryRepository(Protocol):
    """Interface required from a read-only SQL repository."""

    def get_schema_context(self) -> str: ...

    def list_tables(self) -> set[str]: ...

    def execute_select(self, sql: str) -> tuple[list[str], list[tuple[Any, ...]], bool]: ...


@dataclass(frozen=True)
class QueryResult:
    """Validated SQL and bounded query output for the UI."""

    sql: str
    columns: list[str]
    rows: list[tuple[Any, ...]]
    truncated: bool


class QueryService:
    """Handle a complete natural-language question safely."""

    def __init__(
        self, generator: SQLGenerator | None, repository: QueryRepository
    ) -> None:
        self._generator = generator
        self._repository = repository

    def answer(self, question: str) -> QueryResult:
        """Generate, validate, then execute a single read-only SELECT query."""
        normalized_question = question.strip()
        if not normalized_question:
            raise SQLValidationError("Enter a question before running a query.")
        if len(normalized_question) > MAX_QUESTION_LENGTH:
            raise SQLValidationError(
                f"Keep the question under {MAX_QUESTION_LENGTH} characters."
            )

        schema_context = self._repository.get_schema_context()
        if _SQL_INPUT_PATTERN.match(normalized_question):
            candidate_sql = normalized_question
        else:
            if self._generator is None:
                raise ModelConfigurationError(
                    "Natural-language SQL needs an OpenAI API key. Configure "
                    "OPENAI_API_KEY, or enter a read-only SELECT query directly."
                )
            candidate_sql = self._generator.generate_sql(
                normalized_question, schema_context
            )
        approved_sql = validate_select_sql(
            candidate_sql,
            allowed_tables=self._repository.list_tables(),
        )
        columns, rows, truncated = self._repository.execute_select(approved_sql)
        return QueryResult(approved_sql, columns, rows, truncated)
