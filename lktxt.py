

import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
from collections import deque

START_URL = "https://docs.livekit.io/"
ALLOWED_NETLOC = urlparse(START_URL).netloc
OUTPUT_FILE = "livekit_docs.txt"
HEADERS = {"User-Agent": "livekit-docs-dumper/1.0 (+https://github.com/yourname)"}

# Crawl settings
MAX_PAGES = 300          # limit for safety; change if you need more
DELAY_BETWEEN_REQUESTS = 0.8  # seconds
ONLY_PATH_PREFIX = "/"   # restrict to paths under root; adjust if needed

def is_same_site(url):
    p = urlparse(url)
    return (p.scheme in ("http", "https")) and (p.netloc == ALLOWED_NETLOC)

def normalize_url(base, link):
    if not link:
        return None
    # remove fragment, join relative to base
    joined = urljoin(base, link)
    nofrag, _ = urldefrag(joined)
    return nofrag

def extract_text_from_html(html, page_url):
    soup = BeautifulSoup(html, "html.parser")
    # remove scripts, styles, nav, footer (common noisy elements)
    for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
        tag.decompose()
    # Optionally keep h1-h3 as headings
    texts = []
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    if title:
        texts.append(f"PAGE TITLE: {title}")
    texts.append(f"URL: {page_url}")
    # Add headings
    for h in soup.find_all(["h1","h2","h3"]):
        t = h.get_text(separator=" ", strip=True)
        if t:
            texts.append("\n== " + t + " ==")
    # Main textual content
    body = soup.get_text(separator="\n", strip=True)
    # Keep body but trim redundant whitespace and short repeated lines
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    # Avoid duplicating the title line inside body
    filtered = [ln for ln in lines if ln not in (title,)]
    texts.append("\n".join(filtered))
    texts.append("\n" + "="*80 + "\n")
    return "\n".join(texts)

def crawl_and_dump(start_url, output_file, max_pages=MAX_PAGES):
    visited = set()
    queue = deque([start_url])
    pages_processed = 0

    with open(output_file, "w", encoding="utf-8") as out:
        while queue and pages_processed < max_pages:
            url = queue.popleft()
            if url in visited:
                continue
            if not is_same_site(url):
                continue
            visited.add(url)
            try:
                resp = requests.get(url, headers=HEADERS, timeout=20)
                if resp.status_code != 200 or "text/html" not in resp.headers.get("Content-Type", ""):
                    # skip non-html pages
                    continue
                html = resp.text
            except Exception as e:
                print(f"[WARN] Failed to fetch {url}: {e}")
                continue

            text_blob = extract_text_from_html(html, url)
            out.write(text_blob + "\n")
            pages_processed += 1
            print(f"[INFO] Saved ({pages_processed}): {url}")

            # Discover links to follow
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                normalized = normalize_url(url, a["href"])
                if not normalized:
                    continue
                # restrict to same host and optional path prefix
                parsed = urlparse(normalized)
                # ensure it's same origin and under the chosen path (e.g., keep docs pages only)
                if parsed.netloc == ALLOWED_NETLOC and parsed.path.startswith(ONLY_PATH_PREFIX):
                    if normalized not in visited:
                        queue.append(normalized)

            time.sleep(DELAY_BETWEEN_REQUESTS)

    print(f"[DONE] Wrote {pages_processed} pages to {output_file}")

if __name__ == "__main__":
    crawl_and_dump(START_URL, OUTPUT_FILE)
