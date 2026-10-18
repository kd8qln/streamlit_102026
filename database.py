import os
import sqlite3
from pathlib import Path
from typing import Any


DATABASE_PATH = Path(os.environ.get("CALCULATOR_DB_PATH", "calculator_history.db"))


def _connect(db_path: str | Path = DATABASE_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            left_operand REAL NOT NULL,
            operator TEXT NOT NULL,
            right_operand REAL NOT NULL,
            result REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return connection


def save_calculation(
    left: float,
    operator: str,
    right: float,
    result: float,
    db_path: str | Path = DATABASE_PATH,
) -> int:
    with _connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO calculations (left_operand, operator, right_operand, result)
            VALUES (?, ?, ?, ?)
            """,
            (left, operator, right, result),
        )
        return int(cursor.lastrowid)


def get_history(
    limit: int = 50, db_path: str | Path = DATABASE_PATH
) -> list[dict[str, Any]]:
    if limit < 1:
        raise ValueError("History limit must be greater than zero.")
    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT left_operand AS Left, operator AS Operation,
                   right_operand AS Right, result AS Result, created_at AS Time
            FROM calculations
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def clear_history(db_path: str | Path = DATABASE_PATH) -> None:
    with _connect(db_path) as connection:
        connection.execute("DELETE FROM calculations")