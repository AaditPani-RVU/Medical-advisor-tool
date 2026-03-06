"""Check current content counts."""
import sqlite3

db_path = r"d:\verified-healthcare-content-reccomender\data\app.db"
conn = sqlite3.connect(db_path)

articles = conn.execute("SELECT COUNT(*) FROM content_items WHERE type = 'article'").fetchone()[0]
videos = conn.execute("SELECT COUNT(*) FROM content_items WHERE type = 'video'").fetchone()[0]
total = articles + videos

print(f"Articles: {articles}")
print(f"Videos:   {videos}")
print(f"Total:    {total}")
print(f"Current split: {videos/(total)*100:.0f}% videos / {articles/(total)*100:.0f}% articles")

# Target: 40% videos, 60% articles
# If we keep articles at {articles}, we need: articles / 0.6 * 0.4 = target_videos
target_videos = int(articles / 0.6 * 0.4)
print(f"\nTo reach 40/60 split with {articles} articles, need ~{target_videos} videos")
print(f"Need {target_videos - videos} more videos")

conn.close()
