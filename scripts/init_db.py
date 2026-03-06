"""
Database initialization script.
Creates the SQLite database and all tables.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.settings import settings, DATA_DIR
from backend.core.models import init_tables
from backend.core.db import get_connection


def main():
    """Initialize the database."""
    # Ensure data directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "cache").mkdir(exist_ok=True)
    (DATA_DIR / "raw_ingest").mkdir(exist_ok=True)

    db_path = Path(settings.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Initializing database at: {db_path}")
    print(f"Database exists: {db_path.exists()}")

    conn = get_connection()
    init_tables(conn)
    conn.close()

    print("✅ Database initialized successfully!")
    print("   Tables created: content_items, family_groups, family_members, saved_items")
    print(f"   Database file: {db_path}")
    print()
    print("Next steps:")
    print("  1. Run ingestion: python -m backend.ingest.ingest_runner")
    print("  2. Start API:     uvicorn backend.main:app --reload")
    print("  3. Start UI:      streamlit run ui/streamlit_app.py")


if __name__ == "__main__":
    main()
