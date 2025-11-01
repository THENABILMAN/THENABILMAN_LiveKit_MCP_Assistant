import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag, urlparse
from collections import deque

START_URL = "https://docs.livekit.io/home/"
DOMAIN = "docs.livekit.io"
visited = set()
queue = deque([START_URL])

all_urls = []

def normalize(url):
    url, _ = urldefrag(url)
    return url

while queue:
    url = queue.popleft()
    if url in visited:
        continue
    visited.add(url)

    try:
        print(f"Crawling: {url}")
        r = requests.get(url, timeout=10)
        if "text/html" not in r.headers.get("Content-Type", ""):
            continue
    except:
        continue

    soup = BeautifulSoup(r.text, "html.parser")

    for a in soup.find_all("a", href=True):
        link = normalize(urljoin(url, a["href"]))
        parsed = urlparse(link)

        # only URLs under docs.livekit.io/home/
        if parsed.netloc == DOMAIN and parsed.path.startswith("/home/"):
            if link not in visited:
                queue.append(link)
            all_urls.append(link)

# remove duplicates
all_urls = sorted(set(all_urls))

# save to file
with open("livekit_home_urls.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(all_urls))

print(f"\n✅ Done! Found {len(all_urls)} URLs inside /home/")
print("📄 Saved to livekit_home_urls.txt")
