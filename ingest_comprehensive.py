"""
Comprehensive Ingestion - Scrape docs.livekit.io and populate Pinecone
Downloads all documentation pages and creates many detailed chunks
"""

import os
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import logging
import urllib3
from collections import deque

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME") or os.environ.get("PINECONE_INDEX", "livekit-docs")
DOCS_URL = "https://docs.livekit.io"

# Headers to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def fetch_page(url, retries=3):
    """Fetch a page and extract text content with retry logic"""
    for attempt in range(retries):
        try:
            response = requests.get(
                url, 
                headers=HEADERS, 
                timeout=15,
                verify=False,
                allow_redirects=True
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract page title for context
            title = ""
            title_elem = soup.find('title')
            if title_elem:
                title = title_elem.get_text().strip()
            
            h1_elem = soup.find('h1')
            if h1_elem:
                title = h1_elem.get_text().strip()
            
            # Try to find main content areas (common patterns for doc sites)
            content_selectors = [
                'main',
                'article',
                '[role="main"]',
                '.main-content',
                '.content',
                '.docs-content',
                '.documentation',
                '#content',
                '.page-content',
                '.markdown-body',
                '.doc-content'
            ]
            
            main_content = None
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            # If no main content found, try body
            if not main_content:
                main_content = soup.body if soup.body else soup
            
            # Remove unwanted elements
            for unwanted in main_content(["script", "style", "nav", "footer", "aside", "noscript", "header"]):
                unwanted.decompose()
            
            # Extract text
            text = main_content.get_text(separator='\n', strip=True)
            
            # Clean up whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            text = '\n'.join(lines)
            
            # Remove extra blank lines
            while '\n\n\n' in text:
                text = text.replace('\n\n\n', '\n\n')
            
            # Include title in output if we have content
            if text and title:
                text = f"Title: {title}\n\n{text}"
            
            return text
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.debug(f"Retry {attempt + 1}/{retries} after {wait_time}s: {str(e)[:50]}")
                time.sleep(wait_time)
            else:
                logger.debug(f"Failed after {retries} retries: {str(e)[:50]}")
                return None
        except Exception as e:
            logger.debug(f"Error fetching {url}: {str(e)[:50]}")
            return None

def discover_pages_from_sitemap():
    """Try to discover pages from sitemap"""
    try:
        sitemap_urls = [
            f"{DOCS_URL}/sitemap.xml",
            f"{DOCS_URL}/sitemap-docs.xml",
        ]
        
        discovered = []
        for sitemap_url in sitemap_urls:
            try:
                response = requests.get(sitemap_url, headers=HEADERS, timeout=5, verify=False)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'xml')
                    for loc in soup.find_all('loc'):
                        url = loc.text
                        if '/docs/' in url or '/home/' in url:
                            discovered.append(url)
                    if discovered:
                        return discovered
            except:
                pass
        
        return []
    except:
        return []

def crawl_all_pages():
    """Crawl all documentation pages dynamically"""
    print("🕷️ Crawling docs.livekit.io to discover all pages...")
    
    visited = set()
    queue = deque([
        f"{DOCS_URL}/",
        f"{DOCS_URL}/home/",
        f"{DOCS_URL}/docs/",
    ])
    discovered_urls = set()
    
    # Prefill with common paths
    common_paths = [
        "/home/intro",
        "/home/getting-started",
        "/docs/home",
        "/docs/server",
        "/docs/client",
        "/docs/guides",
        "/docs/api",
    ]
    for path in common_paths:
        queue.append(f"{DOCS_URL}{path}")
    
    crawl_count = 0
    max_crawl = 100  # Limit crawling to avoid infinite loops
    
    while queue and crawl_count < max_crawl:
        url = queue.popleft()
        
        # Normalize URL
        url, _ = urldefrag(url)
        
        if url in visited:
            continue
        
        visited.add(url)
        crawl_count += 1
        
        try:
            print(f"  📍 Crawling [{crawl_count}]: {urlparse(url).path[:50]}", end="...", flush=True)
            
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=10,
                verify=False
            )
            
            if "text/html" not in response.headers.get("Content-Type", ""):
                print(" ⊘ (not HTML)")
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links
            for a in soup.find_all("a", href=True):
                link = urljoin(url, a["href"])
                link, _ = urldefrag(link)
                
                parsed = urlparse(link)
                
                # Only follow docs.livekit.io links
                if parsed.netloc == "docs.livekit.io":
                    discovered_urls.add(link)
                    
                    # Queue for crawling if we haven't visited
                    if link not in visited and crawl_count < max_crawl:
                        queue.append(link)
            
            print(" ✓")
            
        except Exception as e:
            print(f" ✗ ({str(e)[:20]})")
    
    # Filter and sort discovered URLs
    discovered_urls = sorted(list(discovered_urls))
    print(f"\n✅ Discovered {len(discovered_urls)} pages via crawling")
    
    return discovered_urls

def main():
    if not PINECONE_API_KEY:
        print("❌ PINECONE_API_KEY not found in .env")
        return

    print("🌐 Fetching LiveKit documentation from docs.livekit.io...")
    print("=" * 60)
    
    # Try to discover pages from sitemap first
    print("📍 Checking for sitemap...")
    discovered = discover_pages_from_sitemap()
    
    if discovered:
        pages = discovered
        print(f"✓ Found {len(pages)} pages from sitemap")
    else:
        # Fall back to crawling all pages
        pages = crawl_all_pages()
    
    if not pages:
        print("❌ Failed to discover any pages!")
        return
    
    all_docs = []
    failed_pages = []
    
    print(f"\n📄 Fetching {len(pages)} pages...")
    print("=" * 60)
    
    for i, url in enumerate(pages, 1):
        # Extract path for display
        parsed = urlparse(url)
        path = parsed.path
        
        print(f"📄 [{i}/{len(pages)}] Fetching: {path[:50]:<50}", end=" ", flush=True)
        
        try:
            content = fetch_page(url)
            if content and len(content.strip()) > 50:
                all_docs.append({
                    "url": url,
                    "content": content
                })
                print(f"✓ ({len(content)} chars)")
            else:
                print("⊘ (empty)")
                failed_pages.append(url)
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user")
            break
        except Exception as e:
            print(f"✗ (error: {str(e)[:20]})")
            failed_pages.append(url)
        
        time.sleep(0.3)  # Rate limiting
    
    print("\n" + "=" * 60)
    print(f"✅ Successfully fetched {len(all_docs)}/{len(pages)} pages")
    if failed_pages:
        print(f"⚠️  Failed on {len(failed_pages)} pages")
    print("=" * 60)
    
    if not all_docs:
        print("\n❌ Failed to fetch any documentation!")
        print("💡 Troubleshooting:")
        print("   • Check your internet connection")
        print("   • Try: python ingest_from_file.py (local file instead)")
        return
    
    total_chars = sum(len(doc["content"]) for doc in all_docs)
    print(f"📊 Total content: {total_chars:,} characters")
    
    # Combine all docs
    combined_docs = "\n\n---PAGE BREAK---\n\n".join([doc["content"] for doc in all_docs])
    
    print("\n📝 Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,      # Smaller chunks for maximum accuracy
        chunk_overlap=150,   # More overlap for better context preservation
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    docs_chunks = text_splitter.split_text(combined_docs)
    print(f"✓ Created {len(docs_chunks)} document chunks")
    
    # Filter out very small chunks
    docs_chunks = [chunk for chunk in docs_chunks if len(chunk.strip()) > 50]
    print(f"✓ After filtering: {len(docs_chunks)} quality chunks")

    print("\n🔤 Creating embeddings with HuggingFace...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )
    print("✓ HuggingFace embeddings model loaded")

    print(f"\n📍 Connecting to Pinecone index: {PINECONE_INDEX_NAME}...")
    
    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Check if index exists, if not create it
    try:
        index = pc.Index(PINECONE_INDEX_NAME)
        print(f"✓ Connected to existing index")
    except:
        print(f"📌 Creating new index: {PINECONE_INDEX_NAME}")
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=384,  # HuggingFace all-MiniLM-L6-v2 uses 384 dimensions
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        time.sleep(2)
        index = pc.Index(PINECONE_INDEX_NAME)
        print("✓ Index created and ready")

    print(f"\n⬆️ Uploading {len(docs_chunks)} chunks to Pinecone...")
    
    # Upload in batches
    batch_size = 50
    total_uploaded = 0
    
    for i in range(0, len(docs_chunks), batch_size):
        batch = docs_chunks[i:i+batch_size]
        
        # Create embeddings for this batch
        batch_embeddings = embeddings.embed_documents(batch)
        
        # Create vectors for upsert
        vectors = []
        for j, (text, embedding) in enumerate(zip(batch, batch_embeddings)):
            vector_id = f"livekit-web-{i+j}"
            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    "text": text[:500],  # Store first 500 chars as preview
                    "source": "docs.livekit.io",
                    "chunk_index": i+j
                }
            })
        
        # Upsert to Pinecone
        index.upsert(vectors=vectors)
        total_uploaded += len(vectors)
        print(f"  ⬆️ Uploaded batch {i//batch_size + 1}/{(len(docs_chunks)-1)//batch_size + 1} ({total_uploaded} total)")
        time.sleep(0.5)  # Rate limiting
    
    print(f"\n✅ Successfully uploaded {total_uploaded} chunks to Pinecone!")
    print(f"📊 Index: {PINECONE_INDEX_NAME}")
    print(f"📈 Total chunks: {len(docs_chunks)}")
    print(f"💾 Total content: {sum(len(chunk) for chunk in docs_chunks):,} characters")
    print(f"\n🎉 LiveKit documentation is now ready for searching!")

if __name__ == "__main__":
    main()
