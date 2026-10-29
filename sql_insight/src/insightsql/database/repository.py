"""Read-only SQLite repository with execution and result limits."""

from __future__ import annotations

import logging
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from typing import Any

from insightsql.config import MAX_RESULT_ROWS, QUERY_TIMEOUT_SECONDS
from insightsql.exceptions import DatabaseQueryError

logger = logging.getLogger(__name__)

_ALLOWED_ACTIONS = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
    getattr(sqlite3, "SQLITE_RECURSIVE", -1),
}
_ALLOWED_FUNCTIONS = {
    "abs",
    "avg",
    "coalesce",
    "count",
    "date",
    "datetime",
    "group_concat",
    "ifnull",
    "instr",
    "length",
    "lower",
    "max",
    "min",
    "nullif",
    "printf",
    "replace",
    "round",
    "strftime",
    "substr",
    "sum",
    "time",
    "total",
    "trim",
    "upper",
}


class SQLiteRepository:
    """Execute read-only queries against one configured SQLite database."""

    def __init__(
        self,
        database_path: Path,
        *,
        timeout_seconds: int = QUERY_TIMEOUT_SECONDS,
        max_rows: int = MAX_RESULT_ROWS,
    ) -> None:
        self.database_path = database_path.resolve()
        self.timeout_seconds = timeout_seconds
        self.max_rows = max_rows

    def list_tables(self) -> set[str]:
        """Return non-internal table names present in the database."""
        if not self.database_path.is_file():
            raise DatabaseQueryError("The configured SQLite database file was not found.")

        try:
            with closing(self._connect()) as connection:
                rows = connection.execute(
                    "SELECT name FROM sqlite_schema "
                    "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
                    "ORDER BY name"
                ).fetchall()
            return {str(row[0]) for row in rows}
        except sqlite3.Error as error:
            logger.warning("database_schema_read_failed error_type=%s", type(error).__name__)
            raise DatabaseQueryError("Could not read the database schema.") from error

    def get_schema_context(self) -> str:
        """Return table/column metadata for SQL generation, without row data."""
        if not self.database_path.is_file():
            raise DatabaseQueryError("The configured SQLite database file was not found.")
        try:
            with closing(self._connect()) as connection:
                table_names = connection.execute(
                    "SELECT name FROM sqlite_schema "
                    "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                ).fetchall()
                lines: list[str] = []
                for (table_name,) in table_names:
                    columns = connection.execute(
                        f"PRAGMA table_info({self._quote_identifier(str(table_name))})"
                    ).fetchall()
                    column_names = ", ".join(str(column[1]) for column in columns)
                    lines.append(f"{table_name}({column_names})")
            return "\n".join(lines)
        except sqlite3.Error as error:
            logger.warning("database_schema_read_failed error_type=%s", type(error).__name__)
            raise DatabaseQueryError("Could not read the database schema.") from error

    def execute_select(self, sql: str) -> tuple[list[str], list[tuple[Any, ...]], bool]:
        """Execute one SELECT under SQLite authorizer, timeout, and row limits."""
        if not self.database_path.is_file():
            raise DatabaseQueryError("The configured SQLite database file was not found.")

        try:
            with closing(self._connect()) as connection:
                table_names = {
                    str(row[0])
                    for row in connection.execute(
                        "SELECT name FROM sqlite_schema "
                        "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
                    ).fetchall()
                }
                connection.set_authorizer(self._authorizer(table_names))
                deadline = time.monotonic() + self.timeout_seconds
                connection.set_progress_handler(
                    lambda: int(time.monotonic() >= deadline), 1_000
                )
                cursor = connection.execute(sql)
                columns = [str(description[0]) for description in cursor.description or ()]
                rows = cursor.fetchmany(self.max_rows + 1)
                truncated = len(rows) > self.max_rows
                return columns, rows[: self.max_rows], truncated
        except sqlite3.Error as error:
            logger.warning("database_query_failed error_type=%s", type(error).__name__)
            if "interrupted" in str(error).casefold():
                raise DatabaseQueryError("The query exceeded the execution time limit.") from error
            raise DatabaseQueryError(
                "The database could not execute this query. Try rephrasing your question."
            ) from error

    def _connect(self) -> sqlite3.Connection:
        """Open a read-only SQLite connection."""
        uri = f"{self.database_path.as_uri()}?mode=ro"
        connection = sqlite3.connect(uri, uri=True, timeout=self.timeout_seconds)
        connection.execute("PRAGMA query_only = ON")
        connection.enable_load_extension(False)
        return connection

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        return '"' + identifier.replace('"', '""') + '"'

    @staticmethod
    def _authorizer(table_names: set[str]):
        """Reject every SQLite operation except SELECT over known tables."""
        known_tables = {table.casefold() for table in table_names}

        def authorize(
            action: int,
            argument1: str | None,
            argument2: str | None,
            database_name: str | None,
            trigger_name: str | None,
        ) -> int:
            del database_name, trigger_name
            if action not in _ALLOWED_ACTIONS:
                return sqlite3.SQLITE_DENY
            if action == sqlite3.SQLITE_READ:
                if not argument1 or argument1.casefold() not in known_tables:
                    return sqlite3.SQLITE_DENY
            if action == sqlite3.SQLITE_FUNCTION:
                function_name = (argument2 or argument1 or "").casefold()
                if function_name not in _ALLOWED_FUNCTIONS:
                    return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        return authorize
