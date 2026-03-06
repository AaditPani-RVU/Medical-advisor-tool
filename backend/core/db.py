"""
SQLite database connection manager.
"""

import sqlite3
from contextlib import contextmanager
from backend.core.settings import settings


def get_connection() -> sqlite3.Connection:
    """Create a new SQLite connection with row factory."""
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_query(query: str, params: tuple = ()) -> list[dict]:
    """Execute a SELECT query and return results as list of dicts."""
    with get_db() as conn:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def execute_insert(query: str, params: tuple = ()) -> int:
    """Execute an INSERT query and return the last row id."""
    with get_db() as conn:
        cursor = conn.execute(query, params)
        return cursor.lastrowid


def execute_update(query: str, params: tuple = ()) -> int:
    """Execute an UPDATE/DELETE query and return rows affected."""
    with get_db() as conn:
        cursor = conn.execute(query, params)
        return cursor.rowcount
