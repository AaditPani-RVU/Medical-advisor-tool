import sqlite3

db_path = r"d:\verified-healthcare-content-reccomender\data\app.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Remove specific irrelevant creators
cursor.execute("DELETE FROM content_items WHERE source_name IN ('Ninja Nerd', 'Doctor Mike')")
print(f"Deleted {cursor.rowcount} rows from irrelevant creators.")

conn.commit()
conn.close()
