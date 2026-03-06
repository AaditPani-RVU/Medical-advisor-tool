import requests
from bs4 import BeautifulSoup
import time

urls = [
    "https://www.instagram.com/reel/DVMHdz1DVff/",
    "https://www.instagram.com/reel/DVUWjjNDgcH/",
    "https://www.instagram.com/reel/DVRr5SFlMAh/",
    "https://www.instagram.com/reel/DVekiK1DyiC/",
    "https://www.instagram.com/reel/DVf50xNkoU_/",
    "https://www.instagram.com/reel/DRDe4WKEZmS/"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

for url in urls:
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title').text if soup.find('title') else 'No title found'
        print(f"\n{url}\nTitle: {title}")
        time.sleep(1)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
