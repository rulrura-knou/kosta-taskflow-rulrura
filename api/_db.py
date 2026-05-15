import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./taskflow.db")


def _is_sqlite() -> bool:
    return DATABASE_URL.startswith("sqlite")


def _sqlite_path() -> str:
    return DATABASE_URL.split("///", 1)[1]


def q(sql: str) -> str:
    """Convert ? placeholders to %s for psycopg2."""
    if not _is_sqlite():
        return sql.replace("?", "%s")
    return sql


def _serialize(val):
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%dT%H:%M:%S.") + f"{val.microsecond // 1000:03d}Z"
    return val


def to_dict(row) -> dict | None:
    if row is None:
        return None
    return {k: _serialize(v) for k, v in dict(row).items()}


def to_list(rows) -> list[dict]:
    return [to_dict(r) for r in rows]


@contextmanager
def get_db():
    if _is_sqlite():
        conn = sqlite3.connect(_sqlite_path())
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()


_SQLITE_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        invite_code TEXT UNIQUE NOT NULL,
        owner_id INTEGER NOT NULL,
        created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')||'Z')
    )""",
    """CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        team_id INTEGER REFERENCES teams(id),
        created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')||'Z')
    )""",
    """CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_id INTEGER NOT NULL REFERENCES teams(id),
        title TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'TODO',
        creator_id INTEGER NOT NULL REFERENCES users(id),
        assignee_id INTEGER REFERENCES users(id),
        created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')||'Z')
    )""",
    """CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_id INTEGER NOT NULL REFERENCES teams(id),
        user_id INTEGER NOT NULL REFERENCES users(id),
        content TEXT NOT NULL,
        created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')||'Z')
    )""",
    "CREATE INDEX IF NOT EXISTS idx_tasks_team_created ON tasks(team_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_messages_team_created ON messages(team_id, created_at)",
]

_PG_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS teams (
        id SERIAL PRIMARY KEY,
        name VARCHAR(30) NOT NULL,
        invite_code VARCHAR(9) UNIQUE NOT NULL,
        owner_id INTEGER NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        team_id INTEGER REFERENCES teams(id),
        created_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS tasks (
        id SERIAL PRIMARY KEY,
        team_id INTEGER NOT NULL REFERENCES teams(id),
        title VARCHAR(100) NOT NULL,
        status TEXT NOT NULL DEFAULT 'TODO',
        creator_id INTEGER NOT NULL REFERENCES users(id),
        assignee_id INTEGER REFERENCES users(id),
        created_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY,
        team_id INTEGER NOT NULL REFERENCES teams(id),
        user_id INTEGER NOT NULL REFERENCES users(id),
        content TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    "CREATE INDEX IF NOT EXISTS idx_tasks_team_created ON tasks(team_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_messages_team_created ON messages(team_id, created_at)",
]


def init_schema():
    stmts = _SQLITE_SCHEMA if _is_sqlite() else _PG_SCHEMA
    if _is_sqlite():
        conn = sqlite3.connect(_sqlite_path())
        conn.execute("PRAGMA foreign_keys = ON")
        for stmt in stmts:
            conn.execute(stmt)
        conn.commit()
        conn.close()
    else:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        for stmt in stmts:
            try:
                cur.execute(stmt)
            except Exception as e:
                print(f"[schema] {e}")
        cur.close()
        conn.close()
