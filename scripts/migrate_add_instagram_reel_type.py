"""
Migration script — adds 'instagram_reel' to the content_items type CHECK constraint.

SQLite does not support ALTER TABLE ... ALTER COLUMN, so we recreate the table
inside a transaction while preserving all existing data.

Usage:
    python scripts/migrate_add_instagram_reel_type.py
"""

import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.settings import settings

DB_PATH = settings.db_path


def migrate():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")

    try:
        conn.execute("BEGIN TRANSACTION")

        # 1. Rename existing table
        conn.execute("ALTER TABLE content_items RENAME TO _content_items_old")

        # 2. Create new table with updated CHECK constraint
        conn.execute("""
            CREATE TABLE content_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK(type IN ('article', 'video', 'post', 'short_video', 'instagram_reel')),
                title TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                source_name TEXT NOT NULL,
                source_tier TEXT NOT NULL CHECK(source_tier IN ('verified_org', 'verified_creator')),
                published_at TEXT,
                text TEXT,
                transcript TEXT,
                tags_json TEXT DEFAULT '[]',
                summary_json TEXT DEFAULT '{}',
                ingested_at TEXT DEFAULT (datetime('now')),
                content_length INTEGER DEFAULT 0
            )
        """)

        # 3. Copy data from old table
        conn.execute("""
            INSERT INTO content_items
                (id, type, title, url, source_name, source_tier,
                 published_at, text, transcript, tags_json, summary_json,
                 ingested_at, content_length)
            SELECT
                id, type, title, url, source_name, source_tier,
                published_at, text, transcript, tags_json, summary_json,
                ingested_at, content_length
            FROM _content_items_old
        """)

        # 4. Recreate indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_content_items_url ON content_items(url)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_content_items_source ON content_items(source_name)")

        # 5. Drop old table
        conn.execute("DROP TABLE _content_items_old")

        conn.execute("COMMIT")
        print("✅ Migration complete — 'instagram_reel' type added to content_items.")

    except Exception as e:
        conn.execute("ROLLBACK")
        print(f"❌ Migration failed, rolled back: {e}")
        raise
    finally:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.close()


if __name__ == "__main__":
    migrate()
