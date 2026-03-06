"""Delete existing video entries to prepare for re-ingestion."""
import sqlite3
db_path = r"d:\verified-healthcare-content-reccomender\data\app.db"
conn = sqlite3.connect(db_path)
count = conn.execute("SELECT COUNT(*) FROM content_items WHERE type = 'video'").fetchone()[0]
print(f"Deleting {count} old video entries...")
conn.execute("DELETE FROM content_items WHERE type = 'video'")
conn.commit()
print("Done!")
conn.close()
