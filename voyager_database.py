import os
import sqlite3
from pathlib import Path
from typing import Any


DATABASE_PATH = Path(
    os.environ.get(
        "VOYAGER_DB_PATH",
        Path(__file__).resolve().parent / "db" / "Voyager_101726_2.db",
    )
)


def _connect(db_path: str | Path = DATABASE_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    if not path.is_file():
        raise FileNotFoundError(f"SQLite database not found: {path}")
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _get_columns(
    connection: sqlite3.Connection, table_name: str
) -> list[dict[str, Any]]:
    table = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    if table is None:
        raise ValueError(f"Unknown table: {table_name}")
    return [
        dict(row)
        for row in connection.execute(
            f"PRAGMA table_info({_quote_identifier(table_name)})"
        ).fetchall()
    ]


def get_tables(db_path: str | Path = DATABASE_PATH) -> list[str]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    return [str(row["name"]) for row in rows]


def get_columns(
    table_name: str, db_path: str | Path = DATABASE_PATH
) -> list[dict[str, Any]]:
    with _connect(db_path) as connection:
        return _get_columns(connection, table_name)


def get_records(
    table_name: str, db_path: str | Path = DATABASE_PATH
) -> list[dict[str, Any]]:
    with _connect(db_path) as connection:
        columns = _get_columns(connection, table_name)
        primary_keys = sorted(
            (column for column in columns if column["pk"]),
            key=lambda column: column["pk"],
        )
        order_by = ""
        if primary_keys:
            order_by = " ORDER BY " + ", ".join(
                _quote_identifier(column["name"]) for column in primary_keys
            )
        rows = connection.execute(
            f"SELECT * FROM {_quote_identifier(table_name)}{order_by}"
        ).fetchall()
    return [dict(row) for row in rows]


def insert_record(
    table_name: str,
    values: dict[str, Any],
    db_path: str | Path = DATABASE_PATH,
) -> int:
    with _connect(db_path) as connection:
        columns = _get_columns(connection, table_name)
        allowed_columns = {column["name"] for column in columns}
        unknown_columns = set(values) - allowed_columns
        if unknown_columns:
            raise ValueError(f"Unknown columns: {', '.join(sorted(unknown_columns))}")

        if values:
            names = list(values)
            column_sql = ", ".join(_quote_identifier(name) for name in names)
            placeholders = ", ".join("?" for _ in names)
            cursor = connection.execute(
                f"INSERT INTO {_quote_identifier(table_name)} "
                f"({column_sql}) VALUES ({placeholders})",
                [values[name] for name in names],
            )
        else:
            cursor = connection.execute(
                f"INSERT INTO {_quote_identifier(table_name)} DEFAULT VALUES"
            )
        return int(cursor.lastrowid)


def update_record(
    table_name: str,
    primary_key: dict[str, Any],
    values: dict[str, Any],
    db_path: str | Path = DATABASE_PATH,
) -> int:
    with _connect(db_path) as connection:
        columns = _get_columns(connection, table_name)
        column_names = {column["name"] for column in columns}
        primary_columns = {
            column["name"] for column in columns if column["pk"]
        }
        if not primary_columns:
            raise ValueError(f"Table {table_name} has no primary key")
        if set(primary_key) != primary_columns:
            raise ValueError("The record key must include every primary-key column")
        if not values:
            raise ValueError("At least one value is required to update a record")
        unknown_columns = set(values) - column_names
        if unknown_columns:
            raise ValueError(f"Unknown columns: {', '.join(sorted(unknown_columns))}")
        if set(values) & primary_columns:
            raise ValueError("Primary-key columns cannot be updated")

        assignments = ", ".join(
            f"{_quote_identifier(name)} = ?" for name in values
        )
        where_clause = " AND ".join(
            f"{_quote_identifier(name)} = ?" for name in primary_key
        )
        cursor = connection.execute(
            f"UPDATE {_quote_identifier(table_name)} SET {assignments} "
            f"WHERE {where_clause}",
            [*values.values(), *primary_key.values()],
        )
        return cursor.rowcount


def delete_record(
    table_name: str,
    primary_key: dict[str, Any],
    db_path: str | Path = DATABASE_PATH,
) -> int:
    with _connect(db_path) as connection:
        columns = _get_columns(connection, table_name)
        primary_columns = {
            column["name"] for column in columns if column["pk"]
        }
        if not primary_columns:
            raise ValueError(f"Table {table_name} has no primary key")
        if set(primary_key) != primary_columns:
            raise ValueError("The record key must include every primary-key column")

        where_clause = " AND ".join(
            f"{_quote_identifier(name)} = ?" for name in primary_key
        )
        cursor = connection.execute(
            f"DELETE FROM {_quote_identifier(table_name)} WHERE {where_clause}",
            list(primary_key.values()),
        )
        return cursor.rowcount