"""
Ingest LiveKit documentation from livekit_docs.txt file
Chunks the text and stores in Pinecone vector database
"""

import os
import time
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME") or os.environ.get("PINECONE_INDEX", "livekit-docs")

def read_docs_from_file(filepath: str) -> str:
    """Read documentation from local text file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✓ Read {len(content):,} characters from {filepath}")
        return content
    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")
        return None

def main():
    if not PINECONE_API_KEY:
        print("❌ PINECONE_API_KEY not found in .env")
        return

    print("📖 Ingesting LiveKit documentation from file...")
    print("=" * 60)
    
    # Read documentation from file
    doc_content = read_docs_from_file("livekit_docs.txt")
    if not doc_content:
        return
    
    print("\n📝 Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,      # Smaller chunks for maximum accuracy
        chunk_overlap=150,   # More overlap for better context preservation
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    docs_chunks = text_splitter.split_text(doc_content)
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
            dimension=384,  # HuggingFace embeddings dimension
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
            vector_id = f"livekit-doc-{i+j}"
            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    "text": text[:500],  # Store first 500 chars as preview
                    "source": "livekit_docs.txt",
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
