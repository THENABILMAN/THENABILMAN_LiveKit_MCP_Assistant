"""
Check what's actually stored in Pinecone and diagnose search issues
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import Pinecone as LangChainPinecone

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME") or os.getenv("PINECONE_INDEX", "livekit-docs")

print("🔍 Pinecone Diagnostic Check")
print("=" * 60)

# Connect to Pinecone directly
try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    
    # Get index stats
    stats = index.describe_index_stats()
    print(f"\n📊 Index: {PINECONE_INDEX_NAME}")
    print(f"   Namespaces: {stats.get('namespaces', {})}")
    
    total_vectors = 0
    for ns, ns_stats in stats.get('namespaces', {}).items():
        vector_count = ns_stats.get('vector_count', 0)
        total_vectors += vector_count
        print(f"   - Namespace '{ns}': {vector_count} vectors")
    
    print(f"\n   📈 Total vectors: {total_vectors}")
    
    if total_vectors == 0:
        print("\n❌ No vectors found in Pinecone!")
        print("   Run: python ingest_comprehensive.py")
        print("   Or:  python ingest_from_file.py")
    else:
        print(f"   ✅ Found {total_vectors} vectors!")
    
except Exception as e:
    print(f"❌ Error connecting to Pinecone: {e}")
    exit(1)

print("\n" + "=" * 60)
print("🔎 Testing Search Query")
print("=" * 60)

try:
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    vector_store = LangChainPinecone(
        index_name=PINECONE_INDEX_NAME,
        embedding=embeddings
    )
    
    # Try a simple search
    test_queries = [
        "LiveKit installation",
        "WebRTC",
        "server setup",
        "client SDK",
        "documentation",
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        try:
            results = vector_store.similarity_search(query, k=3)
            print(f"   Results: {len(results)} found")
            
            if results:
                for i, doc in enumerate(results, 1):
                    preview = doc.page_content[:80].replace('\n', ' ')
                    print(f"   [{i}] {preview}...")
                    if doc.metadata:
                        print(f"        Source: {doc.metadata.get('source', 'N/A')}")
            else:
                print("   ⚠️  No results")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}")
    
    print("\n" + "=" * 60)
    print("✅ Diagnostic check complete!")
    
except Exception as e:
    print(f"❌ Search error: {e}")
