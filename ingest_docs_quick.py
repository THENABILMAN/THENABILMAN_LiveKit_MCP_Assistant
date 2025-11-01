"""
Quick Ingestion - Populate Pinecone with sample LiveKit documentation
"""

import os
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec
import time

load_dotenv()

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME") or os.environ.get("PINECONE_INDEX", "livekit-docs")

# Sample LiveKit documentation
SAMPLE_DOCS = """
LiveKit is an open source project that provides SDKs in Web, iOS, Android, Flutter, React Native, Go, Python, Ruby, Rust, and C++.

LiveKit Server is a WebRTC SFU (Selective Forwarding Unit). It handles WebRTC connections and routes media between participants.

Installation: To get started with LiveKit, you can use the official Docker image or compile from source. The easiest way is using Docker.

Authentication: LiveKit uses token-based authentication. You generate access tokens with specific permissions for each participant.

Room Management: LiveKit server manages rooms which contain participants. Rooms are created dynamically when the first participant joins.

Recording: LiveKit can record audio and video of rooms. Recordings are saved as MP4 files.

Virtual Backgrounds: Participants can use virtual backgrounds during video calls.

Screen Sharing: Users can share their screen with other participants in the room.

Chat: LiveKit supports sending messages between participants in real-time.

Permissions: You can control which participants can publish audio, video, or share their screen.

Analytics: LiveKit provides detailed analytics about room usage and bandwidth.

Webhooks: LiveKit sends webhooks for room and participant events like joins, leaves, and updates.

Codecs: LiveKit supports H264 and VP8 for video, and Opus for audio.

Bandwidth Management: The server automatically adjusts video quality based on available bandwidth.

Network Adaptation: Clients automatically adapt to network conditions.

Load Balancing: Multiple LiveKit servers can be deployed for load balancing.

Security: All connections are encrypted with TLS/DTLS.

Egress: Export room recordings and stream to external services.

Ingress: Stream from external sources into LiveKit rooms.

Turnserver: LiveKit can use TURN servers for NAT traversal.

Configuration: LiveKit server is configured via environment variables or config file.

Monitoring: Prometheus metrics are available for monitoring LiveKit server performance.

Scaling: LiveKit can scale horizontally with multiple server instances.

Database: LiveKit uses Redis for distributed state management.

Pricing: LiveKit Cloud pricing is based on usage minutes and bandwidth.

API: Complete REST API available for managing rooms and participants.

SDKs: Official SDKs available for all major platforms.

Plugins: Extensibility through plugin system for custom features.

Testing: LiveKit provides testing tools and sample applications.
"""

def main():
    if not PINECONE_API_KEY:
        print("❌ PINECONE_API_KEY not found in .env")
        return

    print("📝 Splitting documents...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
    )
    docs_chunks = text_splitter.split_text(SAMPLE_DOCS)
    print(f"✓ Created {len(docs_chunks)} document chunks")

    print("\n🔤 Creating embeddings with HuggingFace...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )
    print("✓ HuggingFace embeddings initialized")

    print(f"\n📍 Connecting to Pinecone index: {PINECONE_INDEX_NAME}...")
    
    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Create index if it doesn't exist
    if PINECONE_INDEX_NAME not in pc.list_indexes().names():
        print(f"Creating new index: {PINECONE_INDEX_NAME}...")
        pc.create_index(
            PINECONE_INDEX_NAME,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print(f"✓ Index created")
        time.sleep(30)  # Wait for index to be ready
    else:
        print(f"✓ Index already exists")
    
    index = pc.Index(PINECONE_INDEX_NAME)
    
    # Upload in batches
    print(f"\n⬆️ Uploading {len(docs_chunks)} chunks to Pinecone...")
    total_docs = len(docs_chunks)
    
    for batch_start in range(0, total_docs, 50):
        batch_end = min(batch_start + 50, total_docs)
        batch_docs = docs_chunks[batch_start:batch_end]
        
        # Embed this batch
        vectors_batch = []
        for i, doc_text in enumerate(batch_docs):
            doc_id = batch_start + i
            embedding = embeddings.embed_query(doc_text)
            vectors_batch.append({
                "id": f"doc_{doc_id}",
                "values": embedding,
                "metadata": {"text": doc_text}
            })
        
        # Upload this batch (to default namespace)
        index.upsert(vectors=vectors_batch)
        progress = min(batch_end, total_docs)
        print(f"  ✓ Uploaded {progress}/{total_docs} chunks")
    
    print(f"\n✅ Successfully uploaded {len(docs_chunks)} chunks to Pinecone!")
    print(f"📊 Index: {PINECONE_INDEX_NAME}")
    print(f"📈 Total chunks: {len(docs_chunks)}")
    print("\n🎉 Documentation is now ready for searching!")

if __name__ == "__main__":
    main()
