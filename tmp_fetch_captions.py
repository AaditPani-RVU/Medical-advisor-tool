import instaloader
import time

L = instaloader.Instaloader()

shortcodes = [
    "DVekiK1DyiC",
    "DVMHdz1DVff",
    "DVf50xNkoU_",
    "DVUWjjNDgcH",
    "DRDe4WKEZmS",
    "DVRr5SFlMAh",
    "DRjy-APj3JE",
    "DVeILCvEa4u",
    "DU6dJ7Dkq6c",
    "DVQnSGHAXe-"
]

print("Fetching metadata for reels...")
for code in shortcodes:
    try:
        post = instaloader.Post.from_shortcode(L.context, code)
        print(f"\n--- {code} ---")
        caption = post.caption if post.caption else "No caption"
        print(caption[:200].replace('\n', ' ') + "...")
        time.sleep(2)  # Avoid rate limit
    except Exception as e:
        print(f"Error fetching {code}: {e}")
