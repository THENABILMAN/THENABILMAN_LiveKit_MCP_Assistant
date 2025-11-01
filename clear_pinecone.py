"""
Clear all vectors from Pinecone index
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME") or os.environ.get("PINECONE_INDEX", "livekit-docs")

if not PINECONE_API_KEY:
    print("❌ PINECONE_API_KEY not found in .env")
    exit(1)

print(f"🗑️ Connecting to Pinecone index: {PINECONE_INDEX_NAME}...")

try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    
    # Get index stats before deletion
    stats = index.describe_index_stats()
    vector_count = stats.get("total_vector_count", 0)
    
    print(f"📊 Current vectors in index: {vector_count}")
    
    if vector_count == 0:
        print("✅ Index is already empty!")
        exit(0)
    
    # Delete all vectors by deleting all namespaces
    print("🔄 Deleting all vectors...")
    
    # Delete from default namespace
    index.delete(delete_all=True)
    
    print("✅ Successfully deleted all vectors from Pinecone!")
    
    # Verify deletion
    stats = index.describe_index_stats()
    vector_count = stats.get("total_vector_count", 0)
    print(f"✓ Remaining vectors: {vector_count}")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    exit(1)
