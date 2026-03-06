import sqlite3

db_path = r"d:\verified-healthcare-content-reccomender\data\app.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT title, url FROM content_items WHERE source_name = 'Ninja Nerd'")
for row in cursor.fetchall():
    print(row[0])
conn.close()
