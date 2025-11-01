# 💬 LiveKit RAG Assistant v2.0

**Enterprise-grade AI semantic search + real-time web integration for LiveKit documentation**

## 🎯 Features

- **Dual Search**: Pinecone docs (3,000+ vectors) + Tavily real-time web
- **Standard MCP**: Async LangChain with Model Context Protocol
- **Ultra-Fast**: Groq LLM (llama-3.3-70b) sub-5s responses
- **Premium UI**: Glassmorphism design with 60+ animations
- **Source Attribution**: Full transparency on every answer

## 🚀 Quick Start

```bash
# Setup
conda create -n langmcp python=3.12
conda activate langmcp
pip install -r requirements.txt

# Configure .env
GROQ_API_KEY=your_key
TAVILY_API_KEY=your_key
PINECONE_API_KEY=your_key
PINECONE_INDEX_NAME=livekit-docs

# Terminal 1: Start MCP Server
python mcp_server_standard.py

# Terminal 2: Start UI
streamlit run app.py
```

App opens at `http://localhost:8501`

## 🏗️ Architecture

```
Streamlit (app.py) → MCP Server → Dual Search:
├─ Pinecone: Semantic search on embeddings (384-dim)
└─ Tavily: Real-time web results
    ↓
Groq LLM (2048 tokens, temp 0.3) → Response + Sources
```

## 🔧 Tech Stack

| Layer | Tech | Purpose |
|-------|------|---------|
| Frontend | Streamlit | Premium glassmorphism UI |
| Backend | MCP Standard | Async subprocess |
| LLM | Groq API | Ultra-fast inference |
| Embeddings | HuggingFace | all-MiniLM-L6-v2 (384-dim) |
| Vector DB | Pinecone | Serverless similarity search |
| Web Search | Tavily | Real-time internet results |

## 📚 Usage

1. Choose mode: **📚 Docs** or **� Web**
2. Ask naturally: "How do I set up LiveKit?"
3. Get instant answer with 📄 sources
4. Copy messages or re-ask from history

## ⚡ Performance

- First query: ~15-20s (model load)
- Cached queries: 2-5s
- Search latency: <500ms

## 🛠️ Configuration

```env
GROQ_API_KEY=gsk_***
TAVILY_API_KEY=tvly_***
PINECONE_API_KEY=***
PINECONE_INDEX_NAME=livekit-docs
```

## 🔄 Populate Docs

```bash
python ingest_docs_quick.py  # Creates 3,000+ vector chunks
```

## 📊 Files

- `app.py` - Streamlit UI with premium design
- `mcp_server_standard.py` - MCP server with tools
- `ingest_docs_quick.py` - Document ingestion
- `requirements.txt` - Dependencies
- `.env` - API keys

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| No results | Try web mode or different keywords |
| MCP not found | Start mcp_server_standard.py in Terminal 1 |
| Slow first response | Normal (15-20s) - model initializes once |
| API errors | Verify all keys in .env file |

## � Features

✅ Real-time chat with 60+ animations
✅ Semantic + keyword hybrid search
✅ Copy-to-clipboard for messages
✅ Recent query suggestions
✅ System status dashboard
✅ Chat history persistence
✅ Query validation + error handling

---

**Version**: 2.0 | **Status**: ✅ Production Ready | **Created**: November 2025

👨‍💻 **By [@THENABILMAN](https://github.com/THENABILMAN)** | � **Open Source** | ❤️ **For Developers**
