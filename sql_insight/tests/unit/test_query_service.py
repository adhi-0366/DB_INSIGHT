from __future__ import annotations

from typing import Any

import pytest

from insightsql.exceptions import SQLValidationError
from insightsql.services.query_service import QueryService


class FakeGenerator:
    def __init__(self, sql: str) -> None:
        self.sql = sql

    def generate_sql(self, question: str, schema_context: str) -> str:
        assert question == "How many employees?"
        assert "employees" in schema_context
        return self.sql


class FakeRepository:
    def __init__(self) -> None:
        self.executed_sql: str | None = None

    def get_schema_context(self) -> str:
        return "employees(employee_id, first_name)"

    def list_tables(self) -> set[str]:
        return {"employees"}

    def execute_select(self, sql: str) -> tuple[list[str], list[tuple[Any, ...]], bool]:
        self.executed_sql = sql
        return ["count"], [(3,)], False


def test_service_validates_before_execution() -> None:
    repository = FakeRepository()
    result = QueryService(FakeGenerator("SELECT COUNT(*) FROM employees"), repository).answer(
        "How many employees?"
    )

    assert result.columns == ["count"]
    assert result.rows == [(3,)]
    assert repository.executed_sql == "SELECT COUNT(*) FROM employees"


def test_service_never_executes_generated_write() -> None:
    repository = FakeRepository()
    service = QueryService(FakeGenerator("DELETE FROM employees"), repository)

    with pytest.raises(SQLValidationError):
        service.answer("How many employees?")
    assert repository.executed_sql is None


def test_service_requires_a_question() -> None:
    repository = FakeRepository()
    service = QueryService(FakeGenerator("SELECT 1"), repository)

    with pytest.raises(SQLValidationError, match="Enter a question"):
        service.answer("  ")


def test_direct_select_runs_without_model() -> None:
    repository = FakeRepository()
    result = QueryService(None, repository).answer(
        "SELECT first_name FROM employees"
    )

    assert result.sql == "SELECT first_name FROM employees"
    assert repository.executed_sql == result.sql


def test_direct_write_is_rejected_without_model() -> None:
    repository = FakeRepository()

    with pytest.raises(SQLValidationError):
        QueryService(None, repository).answer("DELETE FROM employees")
    assert repository.executed_sql is None


def test_natural_language_without_model_has_setup_guidance() -> None:
    from insightsql.exceptions import ModelConfigurationError

    with pytest.raises(ModelConfigurationError, match="OPENAI_API_KEY"):
        QueryService(None, FakeRepository()).answer("How many employees are there?")
