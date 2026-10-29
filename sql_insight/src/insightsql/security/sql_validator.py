"""Validate model-generated SQL before passing it to SQLite."""

from __future__ import annotations

from sqlglot import exp, parse
from sqlglot.errors import ParseError

from insightsql.config import MAX_SQL_LENGTH
from insightsql.exceptions import SQLValidationError

_ALLOWED_QUERY_TYPES = (exp.Select, exp.Union, exp.Intersect, exp.Except)
_FORBIDDEN_FUNCTIONS = {"LOAD_EXTENSION", "READFILE", "WRITEFILE"}


def validate_select_sql(sql: str, allowed_tables: set[str]) -> str:
    """Accept exactly one SELECT query using only known application tables."""
    if not isinstance(sql, str) or not sql.strip():
        raise SQLValidationError("The generated SQL query was empty.")
    if len(sql) > MAX_SQL_LENGTH:
        raise SQLValidationError("The generated SQL query is too long.")

    try:
        statements = [statement for statement in parse(sql, read="sqlite") if statement]
    except ParseError as error:
        raise SQLValidationError("The generated SQL could not be parsed safely.") from error

    if len(statements) != 1 or not isinstance(statements[0], _ALLOWED_QUERY_TYPES):
        raise SQLValidationError("Only one read-only SELECT query is allowed.")

    query = statements[0]
    if any(
        isinstance(node, (exp.DML, exp.DDL, exp.Command))
        for node in query.walk()
    ):
        raise SQLValidationError("Only read-only SELECT operations are allowed.")

    forbidden_function = next(
        (
            function
            for function in query.find_all(exp.Func)
            if (
                function.name
                if isinstance(function, exp.Anonymous)
                else function.sql_name()
            ).upper()
            in _FORBIDDEN_FUNCTIONS
        ),
        None,
    )
    if forbidden_function is not None:
        raise SQLValidationError("The query uses a function that is not allowed.")

    known_tables = {table.casefold() for table in allowed_tables}
    known_ctes = {
        cte.alias_or_name.casefold()
        for cte in query.find_all(exp.CTE)
        if cte.alias_or_name
    }
    for table in query.find_all(exp.Table):
        if not table.name or table.name.casefold() not in known_tables | known_ctes:
            raise SQLValidationError(
                f"The query references an unknown table: {table.name or '(unnamed)'}."
            )
        if table.db or table.catalog:
            raise SQLValidationError("Database-qualified table names are not allowed.")

    return sql.strip().rstrip(";").strip()
