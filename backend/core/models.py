"""
Database models — SQLite table definitions and DDL.
"""

TABLES_DDL = [
    """
    CREATE TABLE IF NOT EXISTS content_items (
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
    """,
    """
    CREATE TABLE IF NOT EXISTS family_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS family_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        name TEXT DEFAULT '',
        age_band TEXT NOT NULL CHECK(age_band IN ('kid', 'teen', 'adult', 'senior')),
        preferences_json TEXT DEFAULT '{}',
        topics_json TEXT DEFAULT '[]',
        FOREIGN KEY (group_id) REFERENCES family_groups(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS saved_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        content_id INTEGER NOT NULL,
        saved_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (group_id) REFERENCES family_groups(id) ON DELETE CASCADE,
        FOREIGN KEY (content_id) REFERENCES content_items(id) ON DELETE CASCADE,
        UNIQUE(group_id, content_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_content_items_url ON content_items(url)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_content_items_source ON content_items(source_name)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_family_members_group ON family_members(group_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_saved_items_group ON saved_items(group_id)
    """,
]


def init_tables(conn):
    """Create all tables if they don't exist."""
    for ddl in TABLES_DDL:
        conn.execute(ddl)
    conn.commit()
