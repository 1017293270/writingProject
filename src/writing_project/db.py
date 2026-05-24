from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import mysql.connector
from mysql.connector import MySQLConnection

from writing_project.config import Settings


@contextmanager
def connect(settings: Settings | None = None) -> Iterator[MySQLConnection]:
    active_settings = settings or Settings.from_env()
    connection = mysql.connector.connect(**active_settings.connection_config())
    try:
        yield connection
    finally:
        connection.close()


def fetch_all(connection: MySQLConnection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return list(cursor.fetchall())
    finally:
        cursor.close()


def execute(connection: MySQLConnection, sql: str, params: tuple[Any, ...] = ()) -> int:
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
        connection.commit()
        return cursor.rowcount
    finally:
        cursor.close()
