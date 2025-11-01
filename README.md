# 💬 LiveKit RAG Assistant

**AI-powered semantic search and question-answering system for LiveKit documentation**

## 🎯 Features

- **Dual Search Modes**: Documentation (Pinecone) + Real-time Web Search (Tavily)
- **Standard MCP Server**: Async LangChain integration with Model Context Protocol
- **Fast Responses**: Groq LLM (llama-3.3-70b) with ultra-fast inference
- **Semantic Search**: HuggingFace embeddings (384-dim) with vector indexing
- **Source Attribution**: View exact sources for every answer
- **Chat History**: Persistent conversation tracking with recent query access
- **Query Validation**: Prevents invalid inputs with helpful error messages
- **Copy-to-Clipboard**: One-click message sharing

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ with conda
- API Keys: GROQ, TAVILY, PINECONE, HuggingFace

### Installation

```bash
# 1. Clone and setup environment
cd c:\lg mcp ai
conda create -n langmcp python=3.12
conda activate langmcp

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure .env file
echo "GROQ_API_KEY=your_key" >> .env
echo "TAVILY_API_KEY=your_key" >> .env
echo "PINECONE_API_KEY=your_key" >> .env
echo "PINECONE_INDEX_NAME=livekit-docs" >> .env
```

### Running the Application

**Terminal 1** - Start MCP Server:
```bash
python mcp_server_standard.py
```

**Terminal 2** - Start Streamlit UI:
```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`

## 📊 Architecture

```
Streamlit UI (app.py)
    ↓
Query Validation → Error Handling
    ↓
MCP Server (subprocess) → mcp_server_standard.py
    ↓
Dual Search Layer:
├─ Pinecone (3,007 vectors) - Semantic search
└─ Tavily API - Real-time web results
    ↓
LLM Layer (Groq):
├─ Temperature: 0.3 (detailed, focused)
├─ Max Tokens: 2048 (comprehensive answers)
└─ Model: llama-3.3-70b-versatile
    ↓
Response Display + Source Attribution
```

## 🔧 Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Streamlit 1.28+ | Premium glassmorphism UI |
| **Backend** | MCP Standard | Async subprocess server |
| **LLM** | Groq API | Ultra-fast inference (free tier) |
| **Embeddings** | HuggingFace | sentence-transformers/all-MiniLM-L6-v2 |
| **Vector DB** | Pinecone Serverless | Ultra-fast similarity search (AWS us-east-1) |
| **Web Search** | Tavily API | Real-time internet search |
| **Framework** | LangChain | LLM orchestration & tools |
| **Language** | Python 3.12 | Modern syntax & features |

## 📚 Project Structure

```
c:\lg mcp ai\
├── app.py                    # Main Streamlit application (enhanced)
├── mcp_server_standard.py    # MCP server with LangChain tools
├── ingest_docs_quick.py      # Document ingestion to Pinecone
├── requirements.txt          # Python dependencies
├── .env                       # API keys & configuration
├── README.md                  # This file
└── ingest_docs.py           # Legacy ingestion script
```

## 🎮 Usage

### Ask Questions

1. **Choose Search Mode**: Documentation (📚) or Web Search (🌐)
2. **Type Question**: Natural language queries work best
3. **Get Answer**: AI responds with detailed 3-5 sentence answers
4. **View Sources**: Click "View Sources" to see cited documents

### Features

- **Copy Messages**: 📋 Click button on any message to copy
- **Recent Queries**: ↻ Quick re-ask from history
- **Quick Help**: 💡 Expandable tips and usage guide
- **Performance Metrics**: 📊 Real-time statistics in System Status
- **Error Prevention**: ✅ Query validation with helpful feedback

## ⚡ Performance

- **First Query**: ~15-20s (model initialization)
- **Subsequent Queries**: 3-8s (cached LLM)
- **Copy/History**: Instant (client-side)
- **Metrics Update**: Real-time (no overhead)

## 📖 Example Queries

- "How do I set up LiveKit?"
- "What are the best practices for video conferencing?"
- "How do I implement real-time communication?"
- "What authentication methods are available?"
- "How do I handle bandwidth optimization?"
- "Deploy to Kubernetes - how does LiveKit handle it?"

## 🛠️ Configuration

Edit `.env` file:

```env
GROQ_API_KEY=gsk_your_groq_key
TAVILY_API_KEY=tvly_your_tavily_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=livekit-docs
HF_TOKEN=optional_huggingface_token
```

## 🔄 Ingestion

Populate Pinecone with LiveKit documentation:

```bash
python ingest_docs_quick.py
```

This creates 3,007 searchable vector chunks from LiveKit docs.

## 📊 Status Checks

View system status in Streamlit sidebar:

```
✅ MCP Server Ready - Status indicator
✅ Groq LLM - API connection
✅ Pinecone VectorDB - Index status
💬 Messages - Total message count
👤 Questions - User query count
🤖 Responses - AI response count
```

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No relevant documentation found" | Try web search mode or different keywords |
| "MCP Server not found" | Ensure `mcp_server_standard.py` is running in Terminal 1 |
| Slow first response | Normal - model loads on first query (~15-20s) |
| API key errors | Check `.env` file and verify all keys are set |
| Empty Pinecone index | Run `python ingest_docs_quick.py` to populate |

## 📝 Notes

- All chat history saved in session state
- Supports semantic search with keyword fallback
- Responses stored with source attribution
- Query validation prevents invalid inputs
- Performance optimized for fast inference

## 👨‍💻 Created By

**@THENABILMAN** - [GitHub](https://github.com/THENABILMAN)

## 📄 License

Built with ❤️ for developers. Feel free to modify and extend!

---

**Version**: Enhanced v1.0 | **Status**: ✅ Production Ready | **Date**: November 1, 2025
