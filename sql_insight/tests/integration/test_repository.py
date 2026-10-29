from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from insightsql.database.repository import SQLiteRepository
from insightsql.exceptions import DatabaseQueryError
from insightsql.services.query_service import QueryService


def test_executes_select_and_returns_bounded_results(database_path: Path) -> None:
    repository = SQLiteRepository(database_path, max_rows=2)

    columns, rows, truncated = repository.execute_select(
        "SELECT first_name FROM employees ORDER BY employee_id"
    )

    assert columns == ["first_name"]
    assert rows == [("Aarav",), ("Diya",)]
    assert truncated is True


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM employees",
        "UPDATE employees SET first_name = 'x'",
        "DROP TABLE employees",
        "PRAGMA table_info(employees)",
        "ATTACH DATABASE ':memory:' AS other",
        "SELECT load_extension('extension')",
        "SELECT randomblob(1000000)",
    ],
)
def test_sqlite_authorizer_rejects_write_and_pragma_operations(
    database_path: Path, sql: str
) -> None:
    repository = SQLiteRepository(database_path)

    with pytest.raises(DatabaseQueryError):
        repository.execute_select(sql)

    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM employees").fetchone()[0] == 3


def test_schema_context_contains_names_not_rows(database_path: Path) -> None:
    context = SQLiteRepository(database_path).get_schema_context()

    assert "employees(employee_id, first_name, department_id)" in context
    assert "Aarav" not in context


def test_missing_database_has_a_safe_error(tmp_path: Path) -> None:
    with pytest.raises(DatabaseQueryError, match="not found"):
        SQLiteRepository(tmp_path / "missing.db").list_tables()


def test_direct_select_runs_without_openai(database_path: Path) -> None:
    result = QueryService(None, SQLiteRepository(database_path)).answer(
        "SELECT department_id, COUNT(*) AS employee_count "
        "FROM employees GROUP BY department_id"
    )

    assert result.columns == ["department_id", "employee_count"]
    assert result.rows == [(1, 2), (2, 1)]
