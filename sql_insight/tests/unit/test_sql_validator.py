from __future__ import annotations

import pytest

from insightsql.exceptions import SQLValidationError
from insightsql.security.sql_validator import validate_select_sql

TABLES = {"employees", "departments"}


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM employees",
        " select department_id, COUNT(*) FROM employees GROUP BY department_id; ",
        "WITH team AS (SELECT * FROM employees) SELECT * FROM team",
        "SELECT first_name FROM employees UNION SELECT department_name FROM departments",
    ],
)
def test_accepts_read_only_select(sql: str) -> None:
    assert validate_select_sql(sql, TABLES).upper().startswith(("SELECT", "WITH"))


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE employees",
        "DELETE FROM employees",
        "UPDATE employees SET first_name = 'x'",
        "ALTER TABLE employees ADD COLUMN x TEXT",
        "TRUNCATE TABLE employees",
        "INSERT INTO employees VALUES (4, 'x', 1)",
        "SELECT * FROM employees; DELETE FROM employees",
        "SELECT * FROM sqlite_schema",
        "SELECT * FROM missing_table",
        "SELECT load_extension('extension')",
    ],
)
def test_rejects_non_select_or_disallowed_queries(sql: str) -> None:
    with pytest.raises(SQLValidationError):
        validate_select_sql(sql, TABLES)


def test_rejects_empty_query() -> None:
    with pytest.raises(SQLValidationError, match="empty"):
        validate_select_sql("  ", TABLES)

