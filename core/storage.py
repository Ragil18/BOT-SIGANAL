import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "app_state.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS session_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    return conn


def load_state(key: str, default):
    """Load a JSON-serializable value previously saved under `key`, or `default` if
    nothing has been saved yet (or the store is unavailable)."""
    try:
        conn = _get_connection()
        row = conn.execute("SELECT value FROM session_state WHERE key = ?", (key,)).fetchone()
        conn.close()
        return json.loads(row[0]) if row is not None else default
    except Exception:
        return default


def save_state(key: str, value) -> None:
    """Persist a JSON-serializable value under `key` so it survives a process restart.
    Persistence is a convenience, not a correctness requirement — a write failure here
    must never crash the app, it just means this change won't survive a restart."""
    try:
        conn = _get_connection()
        conn.execute(
            "INSERT INTO session_state (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
            (key, json.dumps(value, default=str), datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
