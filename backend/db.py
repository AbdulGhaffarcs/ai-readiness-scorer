"""Tiny SQLite cache so we don't burn LLM calls on every page render."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "cache.db"


def init_db() -> None:
    with _conn() as cx:
        cx.execute(
            """
            CREATE TABLE IF NOT EXISTS outreach_cache (
                domain TEXT PRIMARY KEY,
                angle TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


@contextmanager
def _conn():
    cx = sqlite3.connect(DB_PATH)
    try:
        yield cx
        cx.commit()
    finally:
        cx.close()


def get_outreach(domain: str) -> str | None:
    with _conn() as cx:
        row = cx.execute(
            "SELECT angle FROM outreach_cache WHERE domain = ?", (domain,)
        ).fetchone()
    return row[0] if row else None


def put_outreach(domain: str, angle: str) -> None:
    with _conn() as cx:
        cx.execute(
            "INSERT OR REPLACE INTO outreach_cache (domain, angle) VALUES (?, ?)",
            (domain, angle),
        )
