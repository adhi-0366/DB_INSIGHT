from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture
def database_path(tmp_path: Path) -> Iterator[Path]:
    path = tmp_path / "test.db"
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE departments (
                department_id INTEGER PRIMARY KEY,
                department_name TEXT NOT NULL UNIQUE
            );
            CREATE TABLE employees (
                employee_id INTEGER PRIMARY KEY,
                first_name TEXT NOT NULL,
                department_id INTEGER NOT NULL REFERENCES departments(department_id)
            );
            INSERT INTO departments VALUES (1, 'Engineering'), (2, 'Finance');
            INSERT INTO employees VALUES (1, 'Aarav', 1), (2, 'Diya', 1), (3, 'Kabir', 2);
            """
        )
    yield path
