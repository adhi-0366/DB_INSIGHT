"""Build and validate the employee management SQLite database."""

import argparse
import os
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE = PROJECT_DIR / "employee_management.db"
TABLE_COUNTS = {
    "DEPARTMENTS": 5,
    "EMPLOYEES": 20,
    "PROJECTS": 10,
    "EMPLOYEE_PROJECTS": 30,
}


def validate_database(database_path: Path) -> None:
    """Raise an error if the database is invalid or missing expected sample data."""
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"SQLite integrity check failed: {integrity}")

        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Database has foreign-key violations: {violations}")

        for table_name, expected_count in TABLE_COUNTS.items():
            try:
                actual_count = connection.execute(
                    f'SELECT COUNT(*) FROM "{table_name}"'
                ).fetchone()[0]
            except sqlite3.OperationalError as error:
                raise RuntimeError(
                    f"Expected table {table_name} is missing; rebuild with --force."
                ) from error
            if actual_count != expected_count:
                raise RuntimeError(
                    f"{table_name} has {actual_count} rows; expected "
                    f"{expected_count}. Rebuild with --force."
                )


def build_database(database_path: Path) -> None:
    """Build into a temporary file, validate it, then replace the target."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{database_path.stem}_",
        suffix=".tmp",
        dir=database_path.parent,
        delete=False,
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)

    try:
        with closing(sqlite3.connect(temporary_path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            for script_name in ("01_create_tables.sql", "02_insert_sample_data.sql"):
                script_path = PROJECT_DIR / script_name
                connection.executescript(script_path.read_text(encoding="utf-8"))
            connection.commit()

        validate_database(temporary_path)
        os.replace(temporary_path, database_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build and validate the employee management SQLite database."
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"database file path (default: {DEFAULT_DATABASE})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="rebuild the database if the file already exists",
    )
    args = parser.parse_args()
    database_path = args.database.resolve()

    try:
        if database_path.exists() and not args.force:
            validate_database(database_path)
            print(f"Database is accessible and valid: {database_path}")
        else:
            build_database(database_path)
            print(f"Database built and validated: {database_path}")

        for table_name, expected_count in TABLE_COUNTS.items():
            print(f"  {table_name}: {expected_count} rows")
    except (OSError, sqlite3.Error, RuntimeError) as error:
        print(f"Database build/validation failed: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
