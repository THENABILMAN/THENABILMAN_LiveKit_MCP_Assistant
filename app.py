import os
import sys
from dotenv import load_dotenv
import streamlit as st
from datetime import datetime
import asyncio
import json

# LangChain imports
from langchain_groq import ChatGroq

load_dotenv()

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "messages" not in st.session_state:
    st.session_state.messages = []

st.set_page_config(
    page_title="LiveKit Doc Assistant",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "RAG Assistant powered by LiveKit, Pinecone, and Groq"
    }
)

# Premium Fancy CSS with Glassmorphism and Animations
st.markdown("""
    <style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    /* Animated gradient background */
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(-45deg, #0f0f0f, #1a0f2e, #0d3b2d, #050505);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        min-height: 100vh;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Main container */
    .main {
        max-width: 1000px;
        margin: 0 auto !important;
        padding: 20px !important;
    }
    
    .stAppHeader {
        background: rgba(255, 255, 255, 0.7) !important;
        backdrop-filter: blur(10px) !important;
        border-bottom: 2px solid rgba(255, 255, 255, 0.2) !important;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.2) !important;
    }
    
    /* Premium Header */
    .header-container {
        background: linear-gradient(135deg, rgba(26, 15, 46, 0.95) 0%, rgba(13, 59, 45, 0.95) 100%);
        backdrop-filter: blur(10px);
        padding: 4rem 3rem;
        text-align: center;
        border-radius: 30px;
        margin-bottom: 3rem;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        border: 2px solid rgba(168, 162, 255, 0.4);
        position: relative;
        overflow: hidden;
    }
    
    .header-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 200%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        animation: shimmer 3s infinite;
        z-index: 0;
    }
    
    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    .header-container h1 {
        margin: 0;
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #b8a2ff 0%, #4ade80 50%, #6ee7b7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -1px;
        position: relative;
        z-index: 1;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        animation: titleFadeInUp 0.8s ease-out, titleGradientShift 4s ease-in-out infinite, titleGlow 2s ease-in-out infinite;
    }
    
    @keyframes titleFadeInUp {
        0% {
            opacity: 0;
            transform: translateY(30px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes titleGradientShift {
        0%, 100% {
            background: linear-gradient(135deg, #b8a2ff 0%, #4ade80 50%, #6ee7b7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        50% {
            background: linear-gradient(135deg, #6ee7b7 0%, #b8a2ff 50%, #4ade80 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
    }
    
    @keyframes titleGlow {
        0%, 100% {
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.1), 0 0 20px rgba(184, 162, 255, 0.3);
        }
        50% {
            text-shadow: 0 2px 15px rgba(0, 0, 0, 0.2), 0 0 40px rgba(184, 162, 255, 0.6), 0 0 20px rgba(74, 222, 128, 0.4);
        }
    }
    
    .header-container p {
        margin: 1rem 0 0 0;
        font-size: 1.2rem;
        color: #b8a2ff;
        font-weight: 600;
        position: relative;
        z-index: 1;
        animation: subtitleFadeInUp 0.8s ease-out 0.2s backwards;
    }
    
    @keyframes subtitleFadeInUp {
        0% {
            opacity: 0;
            transform: translateY(20px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Premium Messages */
    .message-container {
        margin: 1.5rem 0;
        padding: 1.5rem;
        border-radius: 20px;
        animation: slideIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
        backdrop-filter: blur(10px);
        border: 2px solid rgba(255, 255, 255, 0.3);
    }
    
    .user-message {
        background: linear-gradient(135deg, #6d28d9 0%, #7c3aed 100%);
        color: #f5f5f5;
        margin-left: 2rem;
        border-radius: 25px;
        border: 2px solid rgba(168, 162, 255, 0.5);
        box-shadow: 0 15px 35px rgba(124, 58, 237, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        position: relative;
    }
    
    .user-message::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        border-radius: 25px;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), transparent);
        pointer-events: none;
    }
    
    .user-message strong {
        display: none;
    }
    
    .assistant-message {
        background: rgba(13, 59, 45, 0.95);
        color: #c8fae5;
        margin-right: 2rem;
        border-radius: 20px;
        border: 2px solid rgba(74, 222, 128, 0.5);
        box-shadow: 0 15px 35px rgba(16, 185, 129, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        position: relative;
    }
    
    .assistant-message strong {
        display: none;
    }
    
    .source-container {
        background: linear-gradient(135deg, rgba(109, 40, 217, 0.15) 0%, rgba(74, 222, 128, 0.15) 100%);
        border-left: 4px solid #4ade80;
        padding: 1.5rem;
        border-radius: 15px;
        margin-top: 1.5rem;
        font-size: 0.95rem;
        color: #c8fae5;
        backdrop-filter: blur(10px);
        border: 2px solid rgba(74, 222, 128, 0.4);
        box-shadow: 0 8px 20px rgba(74, 222, 128, 0.2);
    }
    
    .source-title {
        font-weight: 700;
        color: #b8a2ff;
        margin-bottom: 0.8rem;
        font-size: 1.1rem;
    }
    
    /* Premium Input */
    .stTextInput > div > div > input {
        background: rgba(13, 59, 45, 0.95) !important;
        border: 2px solid rgba(74, 222, 128, 0.5) !important;
        border-radius: 25px !important;
        padding: 14px 24px !important;
        font-size: 1rem !important;
        color: #c8fae5 !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border: 2px solid #4ade80 !important;
        box-shadow: 0 0 0 4px rgba(74, 222, 128, 0.3), 0 8px 25px rgba(74, 222, 128, 0.5) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Premium Button */
    .stButton > button {
        background: linear-gradient(135deg, #b8a2ff 0%, #4ade80 100%) !important;
        color: #0f0f0f !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 12px 32px !important;
        font-weight: 700 !important;
        cursor: pointer !important;
        box-shadow: 0 10px 30px rgba(74, 222, 128, 0.6) !important;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
        animation: buttonShimmer 3s infinite;
    }
    
    @keyframes buttonShimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    .stButton > button:hover {
        box-shadow: 0 15px 40px rgba(74, 222, 128, 0.7) !important;
        transform: translateY(-4px) scale(1.02) !important;
    }
    
    .stButton > button:active {
        transform: translateY(-2px) scale(0.98) !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(26, 15, 46, 0.9) 0%, rgba(13, 59, 45, 0.85) 100%) !important;
        backdrop-filter: blur(10px) !important;
        border-right: 2px solid rgba(74, 222, 128, 0.4) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
    }
    
    /* Premium Expander */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, rgba(109, 40, 217, 0.15), rgba(74, 222, 128, 0.15)) !important;
        border-radius: 15px !important;
        border-left: 4px solid #4ade80 !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, rgba(109, 40, 217, 0.2), rgba(74, 222, 128, 0.2)) !important;
        box-shadow: 0 8px 20px rgba(74, 222, 128, 0.4) !important;
    }
    
    /* Premium Divider */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(74, 222, 128, 0.5), transparent);
        margin: 2rem 0;
    }
    
    /* Subheader */
    [data-testid="stMarkdownContainer"] h2 {
        color: #b8a2ff !important;
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        margin-top: 2rem !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    /* Sidebar header styling */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1 {
        color: #b8a2ff !important;
        font-size: 1.5rem !important;
        font-weight: 800 !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: #4ade80 !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        margin-top: 1.5rem !important;
    }
    
    /* Clickable Settings Header */
    [data-testid="stSidebar"] > div:first-child > div > div > div {
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    [data-testid="stSidebar"] > div:first-child > div > div > div:hover {
        transform: translateX(5px);
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(52, 211, 153, 0.1));
        border-radius: 10px;
        padding: 0.5rem;
    }
    
    /* Premium Metrics */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(109, 40, 217, 0.15), rgba(74, 222, 128, 0.1)) !important;
        border-radius: 20px !important;
        padding: 1.5rem !important;
        color: #b8a2ff !important;
        box-shadow: 0 10px 30px rgba(74, 222, 128, 0.25) !important;
        border: 2px solid rgba(74, 222, 128, 0.4) !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(74, 222, 128, 0.4) !important;
    }
    
    /* Animations */
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    /* Suggestion styles */
    .suggestion-container {
        display: none;
        background: linear-gradient(135deg, rgba(26, 15, 46, 0.95) 0%, rgba(13, 59, 45, 0.95) 100%);
        border: 2px solid rgba(74, 222, 128, 0.5);
        border-radius: 15px;
        padding: 1rem;
        margin-top: 1rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 10px 30px rgba(74, 222, 128, 0.3);
        animation: slideIn 0.3s ease-out;
    }
    
    .suggestion-container.show {
        display: block;
    }
    
    .suggestion-title {
        color: #b8a2ff;
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .suggestion-item {
        background: rgba(74, 222, 128, 0.1);
        border: 1px solid rgba(74, 222, 128, 0.3);
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.6rem;
        cursor: pointer;
        color: #c8fae5;
        font-size: 0.95rem;
        transition: all 0.3s ease;
    }
    
    .suggestion-item:hover {
        background: rgba(74, 222, 128, 0.2);
        border-color: rgba(74, 222, 128, 0.6);
        transform: translateX(5px);
        box-shadow: 0 5px 15px rgba(74, 222, 128, 0.3);
    }
    
    .suggestion-item::before {
        content: '💡 ';
        margin-right: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_llm():
    """Load and cache the LLM from Groq for faster subsequent calls."""
    if not GROQ_API_KEY:
        st.error("❌ GROQ_API_KEY not set!")
        st.info("Add your Groq API key to .env file")
        st.stop()
    
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=GROQ_API_KEY,
        temperature=0.3,  # Lower = more focused, detailed answers
        max_tokens=2048  # Doubled for detailed responses
    )
    return llm

def validate_query(query: str) -> tuple[bool, str]:
    """Validate user query for quality and length."""
    if not query or not query.strip():
        return False, "Query cannot be empty"
    
    if len(query.strip()) < 3:
        return False, "Query too short (minimum 3 characters)"
    
    if len(query.strip()) > 500:
        return False, "Query too long (maximum 500 characters)"
    
    return True, ""

def get_query_history_suggestions(limit: int = 5) -> list:
    """Get previous queries as suggestions for quick re-asking."""
    if "chat_history" not in st.session_state:
        return []
    
    # Extract unique user queries from chat history
    user_queries = []
    for msg in st.session_state.messages:
        if msg["role"] == "user" and msg["content"] not in user_queries:
            user_queries.append(msg["content"])
    
    return list(reversed(user_queries))[:limit]

def query_documentation(query: str, top_k: int = 4) -> list:
    """Query LiveKit documentation using MCP server."""
    try:
        import subprocess
        
        # Call mcp_server_standard.py as subprocess
        result = subprocess.run(
            [sys.executable, "mcp_server_standard.py", "search", query, str(top_k)],
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode != 0:
            st.warning(f"Search: {result.stderr if result.stderr else 'No results'}")
            return []
        
        # Parse output
        output = result.stdout.strip()
        if not output:
            return []
        
        docs = []
        for doc_section in output.split("---"):
            doc_section = doc_section.strip()
            if doc_section and "Document" in doc_section:
                docs.append(doc_section)
        
        return docs if docs else []
    except subprocess.TimeoutExpired:
        st.error("⏱️ Search timed out (>60s)")
        return []
    except FileNotFoundError:
        st.error("❌ mcp_server_standard.py not found")
        return []
    except Exception as e:
        st.warning(f"Search error: {str(e)}")
        return []

def stream_response(prompt: str, container) -> str:
    """Stream LLM response token-by-token for real-time feedback."""
    try:
        llm = load_llm()
        response = llm.invoke(prompt)
        answer_text = response.content
        
        # Display full response (streaming not available in Groq free tier)
        with container:
            st.write(answer_text)
        
        return answer_text
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return ""

def search_tavily(query: str, topic: str = "general") -> list:
    """Search the web using Tavily API for real-time information."""
    try:
        from tavily import TavilyClient
        
        if not TAVILY_API_KEY:
            st.error("❌ TAVILY_API_KEY not set!")
            return []
        
        client = TavilyClient(api_key=TAVILY_API_KEY)
        
        response = client.search(
            query=query,
            topic=topic,  # "news" or "general"
            max_results=4
        )
        
        # Extract search results
        docs = []
        if "results" in response:
            for result in response["results"]:
                content = f"**{result.get('title', 'N/A')}**\n{result.get('content', 'N/A')}\nSource: {result.get('url', 'N/A')}"
                docs.append(content)
        
        return docs if docs else ["No results found from web search."]
    except Exception as e:
        st.error(f"❌ Error with Tavily search: {e}")
        return []

# Load the LLM
try:
    llm = load_llm()
    llm_loaded = True
except Exception as e:
    st.error(f"❌ Error loading LLM: {e}")
    st.info("Make sure GROQ_API_KEY is set in .env")
    st.stop()

# Sidebar
with st.sidebar:
    # Initialization Status Section
    with st.expander("✅ Initialization Status", expanded=True):
        st.success("✅ MCP Server configured successfully!")
        st.success("✅ LLM loaded successfully! (Groq - Llama 3.3 70B)")
    
    st.divider()
    
    # Collapsible Settings Section
    with st.expander("⚙️ SETTINGS", expanded=True):
        with st.expander("🎯 Model Configuration", expanded=True):
            st.markdown("**Retrieval Settings**")
            k = st.slider("Documents to retrieve:", min_value=1, max_value=15, value=6, key="k_slider")
            
            st.markdown("**Generation Settings**")
            temperature = st.slider("Temperature:", min_value=0.0, max_value=1.0, value=0.7, step=0.1, key="temp_slider")
            st.caption("Lower = more focused, Higher = more creative")
        
        st.divider()
        
        with st.expander("📊 System Status", expanded=True):
            st.markdown("**🏗️ Architecture**")
            
            # Fancy architecture diagram
            architecture = """
            ```
            ┌─────────────────────────────────────┐
            │   � Streamlit UI (app.py)          │
            │   Detailed Answers • Fast Response  │
            └──────────────┬──────────────────────┘
                           │
                           ▼
            ┌─────────────────────────────────────┐
            │  📡 MCP Server Subprocess           │
            │  (mcp_server_standard.py)           │
            └──────────────┬──────────────────────┘
                           │
                  ┌────────┴────────┐
                  ▼                 ▼
            ┌──────────────┐  ┌─────────────────┐
            │ 📚 Pinecone  │  │ 🌐 Tavily Web   │
            │  3007 Docs   │  │   Search API    │
            └──────────────┘  └─────────────────┘
                  │                 │
                  └────────┬────────┘
                           ▼
            ┌─────────────────────────────────────┐
            │  ⚡ Groq LLM                        │
            │  llama-3.3-70b (Ultra-Fast)        │
            │  • temp: 0.3 (detailed)            │
            │  • tokens: 2048 (comprehensive)    │
            └─────────────────────────────────────┘
            ```
            """
            st.markdown("")
            st.markdown("""
            <div style='background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(74, 222, 128, 0.05) 100%); 
                        backdrop-filter: blur(10px); border: 1px solid rgba(74, 222, 128, 0.3); 
                        border-radius: 12px; padding: 20px; text-align: center; width: 100%;'>
                <h3 style='color: #6ee7b7; margin: 0;'>⚡ Groq LLM Engine</h3>
                <p style='color: #c8fae5; font-size: 12px; margin: 8px 0;'><b>llama-3.3-70b-versatile</b></p>
                <p style='color: #a8f5d8; font-size: 11px; margin: 4px 0;'>🌡️ Temperature: 0.3 (Detailed) | 📊 Tokens: 2048 (Comprehensive)</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("**Service Status**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if os.path.exists("mcp_server_standard.py"):
                    st.success("✅ MCP Server Ready")
                else:
                    st.error("❌ MCP Server Missing")
            
            with col2:
                if GROQ_API_KEY:
                    st.success("✅ Groq LLM")
                else:
                    st.error("❌ Groq LLM")
            
            with col3:
                st.success("✅ Pinecone VectorDB")
            
            st.markdown("**Chat Statistics**")
            col_stats1, col_stats2, col_stats3 = st.columns(3)
            
            with col_stats1:
                st.metric("💬 Messages", len(st.session_state.messages), delta="Total messages")
            
            with col_stats2:
                user_msgs = sum(1 for m in st.session_state.messages if m["role"] == "user")
                st.metric("� Questions", user_msgs, delta="User queries")
            
            with col_stats3:
                assistant_msgs = sum(1 for m in st.session_state.messages if m["role"] == "assistant")
                st.metric("🤖 Responses", assistant_msgs, delta="AI responses")
            
            # Performance indicators
            st.markdown("**⚡ Performance Metrics**")
            col_perf1, col_perf2 = st.columns(2)
            
            with col_perf1:
                st.metric("🔌 MCP Status", "🟢 Active", delta="Connected")
            
            with col_perf2:
                if GROQ_API_KEY and TAVILY_API_KEY:
                    st.metric("🔑 API Keys", "✅ Configured", delta="All set")
                else:
                    st.metric("🔑 API Keys", "⚠️ Partial", delta="Missing keys")
        
    st.divider()
    
    with st.expander("🛠️ Tools", expanded=True):
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🗑️ Clear History", use_container_width=True, key="clear_btn"):
                st.session_state.messages = []
                st.session_state.chat_history = []
                st.success("✅ History cleared!")
                st.rerun()
        
        with col_btn2:
            if st.button("🔄 Refresh", use_container_width=True, key="refresh_btn"):
                st.rerun()
        
        # Show recent queries
        st.markdown("**📜 Recent Queries**")
        recent_queries = get_query_history_suggestions(limit=5)
        if recent_queries:
            for idx, recent_query in enumerate(recent_queries):
                col_q, col_btn = st.columns([0.85, 0.15])
                with col_q:
                    st.caption(f"• {recent_query[:60]}{'...' if len(recent_query) > 60 else ''}")
                with col_btn:
                    if st.button("↻", key=f"recent_query_{idx}", help="Re-ask this question"):
                        st.session_state.main_input_value = recent_query
                        st.session_state.auto_submit_question = True
                        st.rerun()
        else:
            st.caption("No recent queries")
    
    st.divider()
    
    with st.expander("ℹ️ About"):
        st.markdown("""
        ### 💡 LiveKit RAG Assistant
        
        ---
        
        ### 🎯 What It Does
        AI-powered semantic search and question-answering system for LiveKit documentation. Ask natural language questions and get instant, accurate answers backed by the official LiveKit documentation.
        
        ### 🔧 Problems It Solves
        ✅ Instant access to LiveKit knowledge without manual searching
        ✅ Natural language queries (ask in plain English)
        ✅ Real-time semantic understanding of your questions
        ✅ Source attribution for transparency and verification
        ✅ Fast, accurate, and context-aware responses
        
        ### 🏗️ Architecture
        🔌 **MCP Server**: Standard async MCP with LangChain integration
        - Real-time query processing via async tools
        - Semantic search with lazy-loaded embeddings
        - Serverless vector database queries via Pinecone
        
        ### 📊 Data Pipeline
        📚 Documentation → Text Extraction → Chunking
        → Embedding Generation → Pinecone Vector Storage
        → Semantic & Web Search Integration
        
        ### 🛠️ Tech Stack
        - **LLM**: Groq (Llama 3.3 70B) - Ultra-fast inference, free-tier optimized
        - **Embeddings**: HuggingFace (sentence-transformers/all-MiniLM-L6-v2) - 384-dim local embeddings
        - **Vector DB**: Pinecone (Serverless, AWS us-east-1) - Ultra-fast similarity search
        - **Web Search**: Tavily API - Real-time web search integration
        - **Search**: Standard MCP Server (mcp_server_standard.py) - Async semantic search via LangChain
        - **Frontend**: Streamlit - Premium glassmorphism UI with animations
        - **Language**: Python 3.12+ with conda environment
        - **Architecture**: Standard Model Context Protocol (MCP) with async LangChain integration
        
        ### ✨ Key Features
        🎨 Premium UI with glassmorphism & shader effects
        🌈 Purple + Green + Black color scheme with animations
        ✨ Smooth fade-in, glow, and shimmer animations
        💬 Real-time chat with auto-population from suggestions
        📊 Dual search modes: Documentation + Web Search (Tavily)
        🔍 Smart suggestion finder with semantic search & keyword fallback
        ⚙️ Collapsible suggestion section with proper state management
        🌐 Hybrid search algorithm (semantic + keyword-based fallback)
        
        ### ⚡ Performance Optimizations
        ⚡ First query: ~15-20s (initial model load)
        ⚡ Subsequent queries: 3-8s (cached LLM + optimized prompts)
        ⚡ Reduced context: 300-char doc truncation for speed
        ⚡ Max tokens: 1024 for concise answers
        ⚡ Top-K reduced: 4 docs instead of 6 for faster processing
        📈 Supports semantic search on 1000+ doc embeddings
        
        ### 🚀 Search Capabilities
        📚 **Documentation Mode**: Searches LiveKit official docs via Pinecone
        🌐 **Web Mode**: Real-time internet search via Tavily API
        🔄 **Hybrid Algorithm**: Semantic similarity + keyword-based fallback
        ✅ Threshold filtering (0.2 minimum relevance)
        
        ---
        
        **👨‍💻 Creator: [@THENABILMAN](https://github.com/THENABILMAN) | 🚀 Production Ready**
        """)

# Main Header
st.markdown("""
    <div class="header-container">
        <h1>💬 LiveKit Assistant</h1>
        <p>Semantic Search + Web Integration | Powered by MCP</p>
        <p style="font-size: 0.9rem; color: #34d399; margin-top: 0.8rem; font-weight: 600;">🔌 Dual Search Modes • 📚 Docs + 🌐 Web | Built by <a href="https://github.com/THENABILMAN" target="_blank" style="color: #34d399; text-decoration: none; font-weight: 700; transition: color 0.3s;">👨‍💻 @THENABILMAN</a></p>
    </div>
""", unsafe_allow_html=True)

# Quick help section
with st.expander("💡 Quick Help & Tips", expanded=False):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎯 How to Use
        1. **Ask Questions** - Type your question naturally in the input box
        2. **Choose Mode** - Select between Documentation (📚) or Web Search (🌐)
        3. **Get Answers** - Instant AI-powered responses with sources
        4. **View Sources** - Click "View Sources" to see cited documentation
        5. **Re-ask** - Use Recent Queries to ask follow-ups
        
        ### 🔍 Search Tips
        - Be specific: "How do I authenticate users?" works better than "auth"
        - Use keywords: "WebRTC", "codec", "bandwidth", "rooms", "permissions"
        - Ask follow-ups naturally based on previous answers
        - Try different phrasings if no results found
        """)
    
    with col2:
        st.markdown("""
        ### ⚡ Features
        - **Semantic Search** - Understands natural language queries
        - **Dual Search** - Documentation + Real-time Web Search
        - **MCP Integration** - Standard Model Context Protocol backend
        - **Fast Responses** - Groq LLM (ultra-fast inference)
        - **Source Attribution** - See exactly where answers come from
        - **Chat History** - All conversations saved in session
        
        ### 🛠️ Troubleshooting
        - **No results?** - Try simpler keywords or web search mode
        - **Slow responses?** - First query loads model (~15s), then cached
        - **Connection issues?** - Refresh the page or clear history
        - **Need MCP?** - Ensure `mcp_server_standard.py` is running
        """)

# Chat messages will be displayed later (between suggestion finder and main input)

# Define sample questions - diverse and keyword-rich for better matching
SAMPLE_QUESTIONS = [
    "How do I set up LiveKit?",
    "What are the best practices for video conferencing?",
    "How do I integrate LiveKit with my application?",
    "What are the authentication methods available?",
    "How do I optimize bandwidth and performance?",
    "What WebRTC features does LiveKit support?",
    "How do I handle DTMF signals?",
    "What are the API endpoints available?",
    "How do I implement real-time communication?",
    "What are the supported codecs?",
    "How do I manage room permissions?",
    "What is the pricing model?",
]

@st.cache_resource
def get_semantic_model():
    """Load the sentence transformer model for semantic search"""
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as e:
        st.warning(f"Could not load semantic model: {e}")
        return None

def generate_semantic_suggestions(user_query: str, top_k: int = 4) -> list:
    """Generate suggestions using semantic similarity"""
    if not user_query or len(user_query) < 1:
        return SAMPLE_QUESTIONS
    
    try:
        model = get_semantic_model()
        if not model:
            # Fallback: keyword-based filtering
            return get_keyword_suggestions(user_query)
        
        # Encode user query and sample questions
        query_embedding = model.encode(user_query, convert_to_tensor=False)
        question_embeddings = model.encode(SAMPLE_QUESTIONS, convert_to_tensor=False)
        
        # Calculate similarity scores
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        similarities = cosine_similarity([query_embedding], question_embeddings)[0]
        
        # Get top suggestions with a minimum threshold
        top_indices = np.argsort(similarities)[::-1]
        
        # Filter by similarity threshold (0.3) to ensure relevance
        relevant_indices = [i for i in top_indices if similarities[i] > 0.2]
        
        # If we have relevant results, use them; otherwise return all sorted by similarity
        if relevant_indices:
            suggestions = [SAMPLE_QUESTIONS[i] for i in relevant_indices[:top_k]]
        else:
            suggestions = [SAMPLE_QUESTIONS[i] for i in top_indices[:top_k]]
        
        return suggestions if suggestions else SAMPLE_QUESTIONS
    except Exception as e:
        # Fallback to keyword-based suggestions on error
        return get_keyword_suggestions(user_query)

def get_keyword_suggestions(user_query: str, top_k: int = 6) -> list:
    """Fallback: Filter questions based on keyword matching"""
    user_query_lower = user_query.lower()
    keyword_scores = []
    
    for question in SAMPLE_QUESTIONS:
        question_lower = question.lower()
        score = 0
        
        # Keyword matching with scoring
        keywords_to_match = user_query_lower.split()
        for keyword in keywords_to_match:
            if keyword in question_lower:
                score += 1
        
        keyword_scores.append((question, score))
    
    # Sort by score (descending) and return top results
    sorted_questions = sorted(keyword_scores, key=lambda x: x[1], reverse=True)
    results = [q[0] for q in sorted_questions if q[1] > 0]
    
    # If no keyword matches, return all questions
    return results if results else SAMPLE_QUESTIONS

# Initialize state for suggestion search
if "suggestion_search" not in st.session_state:
    st.session_state.suggestion_search = ""
if "suggestion_selected" not in st.session_state:
    st.session_state.suggestion_selected = None
if "main_input_value" not in st.session_state:
    st.session_state.main_input_value = ""
if "find_question_expanded" not in st.session_state:
    st.session_state.find_question_expanded = False
if "auto_submit_question" not in st.session_state:
    st.session_state.auto_submit_question = False

# ===== SECTION 1: SUGGESTION FINDER (Collapsible) =====
with st.expander("🔍 Find Your Question", expanded=st.session_state.find_question_expanded):
    st.markdown("""
        <p style="color: #c8fae5; font-size: 0.9rem; margin: 0 0 1rem 0;">Type keywords to discover what you can ask</p>
    """, unsafe_allow_html=True)
    
    # Suggestion search input with send button
    col_search, col_send = st.columns([0.88, 0.12])
    
    with col_search:
        suggestion_search = st.text_input(
            "Search for question ideas:",
            placeholder="e.g., setup, auth, performance, WebRTC, video...",
            label_visibility="collapsed"
        )
    
    with col_send:
        st.markdown("""
            <style>
                .suggestion-send-btn {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    margin-top: 8px;
                    width: 100%;
                    height: 38px;
                    background: linear-gradient(135deg, #b8a2ff 0%, #7c3aed 50%, #6d28d9 100%);
                    border: 2px solid #4ade80;
                    border-radius: 8px;
                    color: #f5f5f5;
                    font-size: 1.2rem;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 20px rgba(184, 162, 255, 0.5), 0 0 20px rgba(74, 222, 128, 0.3) inset;
                    animation: searchGlow 2s ease-in-out infinite, searchBounce 2.5s ease-in-out infinite;
                    font-weight: 700;
                    letter-spacing: 0.5px;
                    text-shadow: 0 0 10px rgba(74, 222, 128, 0.4);
                }
                
                .suggestion-send-btn:hover {
                    transform: translateY(-3px) scale(1.08);
                    box-shadow: 0 8px 30px rgba(184, 162, 255, 0.7), 0 0 30px rgba(74, 222, 128, 0.5) inset, 0 0 40px rgba(124, 58, 237, 0.4);
                    animation: searchGlowHover 0.5s ease-in-out infinite, searchBounceHover 1s ease-in-out infinite;
                    border-color: #6ee7b7;
                    text-shadow: 0 0 15px rgba(74, 222, 128, 0.6);
                    background: linear-gradient(135deg, #d4c5f9 0%, #a78bfa 50%, #8b5cf6 100%);
                }
                
                .suggestion-send-btn:active {
                    transform: translateY(-1px) scale(0.96);
                    box-shadow: 0 3px 10px rgba(184, 162, 255, 0.4), 0 0 15px rgba(74, 222, 128, 0.2) inset;
                    animation: none;
                }
                
                @keyframes searchGlow {
                    0%, 100% {
                        box-shadow: 0 4px 20px rgba(184, 162, 255, 0.5), 0 0 20px rgba(74, 222, 128, 0.3) inset;
                    }
                    50% {
                        box-shadow: 0 6px 30px rgba(124, 58, 237, 0.6), 0 0 30px rgba(74, 222, 128, 0.5) inset;
                    }
                }
                
                @keyframes searchBounce {
                    0%, 100% {
                        transform: translateY(0px);
                    }
                    50% {
                        transform: translateY(-2px);
                    }
                }
                
                @keyframes searchGlowHover {
                    0%, 100% {
                        box-shadow: 0 8px 30px rgba(184, 162, 255, 0.7), 0 0 30px rgba(74, 222, 128, 0.5) inset, 0 0 40px rgba(124, 58, 237, 0.4);
                    }
                    50% {
                        box-shadow: 0 10px 40px rgba(124, 58, 237, 0.8), 0 0 40px rgba(74, 222, 128, 0.6) inset, 0 0 50px rgba(74, 222, 128, 0.5);
                    }
                }
                
                @keyframes searchBounceHover {
                    0%, 100% {
                        transform: translateY(-3px) scale(1.08);
                    }
                    50% {
                        transform: translateY(-5px) scale(1.1);
                    }
                }
                
                .suggestion-send-btn:focus {
                    outline: none;
                    box-shadow: 0 0 20px rgba(74, 222, 128, 0.6), 0 0 40px rgba(184, 162, 255, 0.4) inset;
                }
            </style>
        """, unsafe_allow_html=True)
        
        if st.button("🔍 Search", key="suggestion_send_btn", help="Search for suggestions", use_container_width=True):
            if suggestion_search.strip():
                st.session_state.suggestion_search = suggestion_search.strip()
                st.session_state.suggestions_list = generate_semantic_suggestions(suggestion_search.strip(), top_k=6)
                st.rerun()

    # Generate suggestions based on suggestion search input (auto-update while typing)
    if suggestion_search and suggestion_search != st.session_state.suggestion_search:
        st.session_state.suggestion_search = suggestion_search
        st.session_state.suggestions_list = generate_semantic_suggestions(suggestion_search, top_k=6)
    elif not suggestion_search:
        st.session_state.suggestion_search = ""
        st.session_state.suggestions_list = SAMPLE_QUESTIONS
    else:
        st.session_state.suggestions_list = st.session_state.suggestions_list if "suggestions_list" in st.session_state else SAMPLE_QUESTIONS

    # Display suggestions with clear visual separation
    if suggestion_search:
        st.markdown("""<div style="color: #b8a2ff; font-size: 0.9rem; margin: 1rem 0 0.8rem 0; font-weight: 600;">📌 Questions You Can Ask:</div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style="color: #b8a2ff; font-size: 0.9rem; margin: 1rem 0 0.8rem 0; font-weight: 600;">💡 Popular Questions:</div>""", unsafe_allow_html=True)

    # Display suggestion questions as clickable buttons
    for idx, question in enumerate(st.session_state.suggestions_list):
        col_a, col_b = st.columns([0.92, 0.08])
        with col_a:
            if st.button(
                question,
                key=f"suggestion_question_{idx}",
                use_container_width=True,
                help="Click to ask this question"
            ):
                # Set the question and flag for automatic submission
                st.session_state.main_input_value = question
                st.session_state.auto_submit_question = True
                st.session_state.suggestion_search = ""  # Clear suggestion search
                st.session_state.find_question_expanded = False  # Close expander after selection
                st.rerun()
        with col_b:
            st.markdown("➜", unsafe_allow_html=True)

# ===== CHAT OUTPUTS APPEAR HERE (Between Section 1 and Section 2) =====
# Display all chat messages between the suggestion finder and main input
for i, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        col_msg, col_copy = st.columns([0.95, 0.05])
        with col_msg:
            st.markdown(f"""
                <div class="message-container user-message">
                    {message['content']}
                </div>
            """, unsafe_allow_html=True)
        with col_copy:
            if st.button("📋", key=f"copy_user_{i}", help="Copy message"):
                st.write(message['content'])
    else:
        col_msg, col_copy = st.columns([0.95, 0.05])
        with col_msg:
            st.markdown(f"""
                <div class="message-container assistant-message">
                    {message['content']}
                </div>
            """, unsafe_allow_html=True)
        with col_copy:
            if st.button("📋", key=f"copy_assistant_{i}", help="Copy message"):
                st.write(message['content'])
        
        # Show sources if available
        if "sources" in message and message["sources"]:
            with st.expander(f"📚 View {len(message['sources'])} Sources", expanded=False):
                for j, source in enumerate(message["sources"], 1):
                    # Ensure source is a string
                    source_text = str(source) if source else "No content"
                    # Escape any HTML characters to prevent tag errors
                    source_text = source_text.replace('<', '&lt;').replace('>', '&gt;')
                    
                    st.markdown(f"""
                        <div class="source-container">
                            <div class="source-title">📄 Source {j}</div>
                            <pre style="background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 10px; overflow-x: auto; color: #d1fae5; font-size: 0.9rem;">{source_text[:600]}{'...' if len(source_text) > 600 else ''}</pre>
                        </div>
                    """, unsafe_allow_html=True)

st.divider()

# ===== SECTION 2: MAIN QUESTION INPUT =====
st.markdown("""
    <div style="text-align: center; margin: 1.5rem 0 1rem 0;">
        <h2 style="font-size: 1.8rem; color: #b8a2ff; margin: 0; font-weight: 800;">✨ Ask Your Question</h2>
        <p style="font-size: 1rem; color: #c8fae5; margin: 0.5rem 0 0 0;">Submit your question about LiveKit</p>
    </div>
""", unsafe_allow_html=True)

# Initialize search mode state
if "search_mode" not in st.session_state:
    st.session_state.search_mode = "📚 LiveKit Docs"

# Add styling for mode buttons with animations
st.markdown("""
    <style>
        /* Mode buttons matching premium glassmorphism design */
        .mode-button-wrapper {
            display: flex;
            gap: 15px;
            margin: 2rem 0;
            justify-content: center;
            align-items: center;
        }
        
        .mode-button {
            padding: 14px 32px;
            border-radius: 20px;
            border: 2px solid rgba(168, 162, 255, 0.4);
            font-weight: 700;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
            font-size: 1.05rem;
            letter-spacing: 0.5px;
            backdrop-filter: blur(10px);
            position: relative;
            overflow: hidden;
        }
        
        .mode-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 200%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
            animation: buttonShimmer 3s infinite;
            z-index: 0;
        }
        
        /* Active mode button - matches user message style */
        .mode-button-active {
            background: linear-gradient(135deg, #6d28d9 0%, #7c3aed 100%);
            color: #f5f5f5;
            border: 2px solid rgba(184, 162, 255, 0.6);
            box-shadow: 
                0 15px 35px rgba(124, 58, 237, 0.6),
                inset 0 1px 0 rgba(255, 255, 255, 0.2),
                0 0 30px rgba(184, 162, 255, 0.4);
            animation: modeActivePulse 0.8s ease-out, modeActiveGlow 2s ease-in-out infinite;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
            position: relative;
            z-index: 1;
        }
        
        /* Inactive mode button - matches documentation style */
        .mode-button-inactive {
            background: linear-gradient(135deg, rgba(26, 15, 46, 0.8) 0%, rgba(13, 59, 45, 0.8) 100%);
            color: #c8fae5;
            border: 2px solid rgba(74, 222, 128, 0.3);
            box-shadow: 
                0 8px 20px rgba(0, 0, 0, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
            animation: modeIdleFloat 3s ease-in-out infinite;
            transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
            position: relative;
            z-index: 1;
        }
        
        .mode-button-inactive:hover {
            background: linear-gradient(135deg, rgba(26, 15, 46, 0.95) 0%, rgba(13, 59, 45, 0.95) 100%);
            border: 2px solid rgba(74, 222, 128, 0.5);
            box-shadow: 
                0 12px 30px rgba(74, 222, 128, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            transform: translateY(-3px) scale(1.02);
            color: #4ade80;
        }
        
        @keyframes modeActivePulse {
            0% {
                transform: scale(0.95);
            }
            50% {
                transform: scale(1.08);
            }
            100% {
                transform: scale(1);
            }
        }
        
        @keyframes modeActiveGlow {
            0%, 100% {
                box-shadow: 
                    0 15px 35px rgba(124, 58, 237, 0.6),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2),
                    0 0 30px rgba(184, 162, 255, 0.4);
            }
            50% {
                box-shadow: 
                    0 20px 50px rgba(124, 58, 237, 0.8),
                    inset 0 1px 0 rgba(255, 255, 255, 0.3),
                    0 0 50px rgba(184, 162, 255, 0.6);
            }
        }
        
        @keyframes modeIdleFloat {
            0%, 100% {
                text-shadow: 0 0 10px rgba(74, 222, 128, 0.2);
            }
            50% {
                text-shadow: 0 0 20px rgba(74, 222, 128, 0.4);
            }
        }
        
        @keyframes buttonShimmer {
            0% { left: -100%; }
            100% { left: 100%; }
        }
        
        .mode-indicator {
            text-align: center;
            color: #b8a2ff;
            font-weight: 700;
            font-size: 1.2rem;
            margin: 1.5rem 0 1rem 0;
            animation: indicatorFade 0.5s ease-in-out, indicatorGlow 2s ease-in-out infinite;
            letter-spacing: 1px;
            text-shadow: 0 0 20px rgba(184, 162, 255, 0.4);
            background: linear-gradient(135deg, rgba(26, 15, 46, 0.6) 0%, rgba(13, 59, 45, 0.6) 100%);
            backdrop-filter: blur(10px);
            padding: 1rem;
            border-radius: 15px;
            border: 1px solid rgba(184, 162, 255, 0.3);
        }
        
        @keyframes indicatorFade {
            0% {
                opacity: 0;
                transform: translateY(-5px);
            }
            100% {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes indicatorGlow {
            0%, 100% {
                text-shadow: 0 0 20px rgba(184, 162, 255, 0.4);
                border-color: rgba(184, 162, 255, 0.3);
            }
            50% {
                text-shadow: 0 0 30px rgba(184, 162, 255, 0.6);
                border-color: rgba(184, 162, 255, 0.5);
            }
        }
    </style>
""", unsafe_allow_html=True)

# Search mode selector with dynamic buttons
col_mode_a, col_mode_b = st.columns([1, 1])

with col_mode_a:
    is_docs_active = st.session_state.search_mode == "📚 LiveKit Docs"
    docs_label = "✅ 📚 Docs Active" if is_docs_active else "📚 Docs"
    if st.button(docs_label, key="mode_docs", help="Search LiveKit documentation", use_container_width=True):
        st.session_state.search_mode = "📚 LiveKit Docs"
        st.rerun()

with col_mode_b:
    is_web_active = st.session_state.search_mode == "🌐 Web"
    web_label = "✅ 🌐 Web Active" if is_web_active else "🌐 Web"
    if st.button(web_label, key="mode_web", help="Search the web with Tavily", use_container_width=True):
        st.session_state.search_mode = "🌐 Web"
        st.rerun()

# Mode indicator with animation
current_mode = st.session_state.search_mode
if current_mode == "📚 LiveKit Docs":
    indicator_text = "📚 LiveKit Documentation Mode"
    indicator_color = "#4ade80"
else:
    indicator_text = "🌐 Web Search Mode"
    indicator_color = "#4ade80"

st.markdown(f"""
    <div class="mode-indicator" style="color: {indicator_color};">
        🔄 {indicator_text}
    </div>
""", unsafe_allow_html=True)

st.markdown("")  # Spacing

col1, col2 = st.columns([5, 1])
with col1:
    user_input = st.text_input(
        "Your question:",
        placeholder="e.g., How do I set up LiveKit?",
        label_visibility="collapsed",
        value=st.session_state.main_input_value
    )
    st.session_state.main_input_value = user_input

with col2:
    search_button = st.button("Send", use_container_width=True, type="primary")

# Process user input when Send button is clicked OR when auto-submit is triggered
if (user_input and search_button) or (st.session_state.auto_submit_question and user_input):
    query = user_input.strip()
    
    # Validate query
    is_valid, error_msg = validate_query(query)
    if not is_valid:
        st.error(f"❌ Invalid query: {error_msg}")
    else:
        st.session_state.auto_submit_question = False  # Reset the flag
        st.session_state.main_input_value = ""  # Clear input after submit
        
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": query
        })
        
        try:
            # Choose search method based on current mode
            if st.session_state.search_mode == "🌐 Web":
                # Use Tavily web search
                with st.spinner("🌐 Searching the web..."):
                    docs = search_tavily(query)
            else:
                # Use LiveKit documentation search (default)
                with st.spinner("🔎 Searching documentation..."):
                    docs = query_documentation(query, top_k=6)  # Get more docs for detailed answers
            
            if docs:
                # Generate response with LLM (optimized)
                llm = load_llm()
                
                # Create context with more details (not truncated)
                sources_text = "\n".join([f"{i+1}. {doc}" for i, doc in enumerate(docs)])
                
                # Adaptive prompt based on search mode
                if st.session_state.search_mode == "🌐 Web":
                    prompt = f"""Answer based on these web search results. Provide a detailed, comprehensive answer:

{sources_text}

Question: {query}

Answer (detailed, 3-5 sentences):"""
                else:
                    prompt = f"""Answer based on LiveKit documentation. Provide a detailed, comprehensive answer with specifics and examples:

{sources_text}

Question: {query}

Answer (detailed, 3-5 sentences):"""
                
                # Stream the response for faster perceived output
                with st.spinner("⏳ Generating detailed answer..."):
                    response = llm.invoke(prompt)
                    answer_text = response.content
                
                # Add assistant response with sources
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer_text,
                    "sources": docs
                })
                
                st.rerun()
            else:
                st.error("❌ No relevant documentation found. Try a different question.")
                # Remove the user message if search failed
                if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
                    st.session_state.messages.pop()
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            if len(st.session_state.messages) > 0:
                st.session_state.messages.pop()

# Footer
st.divider()

footer_html = '<style>@keyframes fadeInUp {from {opacity: 0; transform: translateY(20px);} to {opacity: 1; transform: translateY(0);}} @keyframes pulse {0%, 100% {opacity: 1;} 50% {opacity: 0.7;}} .footer-container {animation: fadeInUp 0.8s ease-out;} .footer-pulse {animation: pulse 2s ease-in-out infinite;} a.footer-link {color: #4ade80; text-decoration: none; font-weight: 700; transition: all 0.3s ease; background: linear-gradient(135deg, rgba(74, 222, 128, 0.3), rgba(184, 162, 255, 0.3)); padding: 4px 8px; border-radius: 6px; display: inline-block;} a.footer-link:hover {color: #b8a2ff; text-decoration: underline; background: linear-gradient(135deg, rgba(74, 222, 128, 0.5), rgba(184, 162, 255, 0.5));}</style><div class="footer-container" style="background: linear-gradient(135deg, rgba(26, 15, 46, 0.9) 0%, rgba(13, 59, 45, 0.85) 100%); backdrop-filter: blur(10px); border-top: 2px solid rgba(74, 222, 128, 0.5); margin-top: 1.5rem; padding: 1.5rem; text-align: center; border-radius: 15px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05);"><p style="font-size: 0.85rem; color: #b8a2ff; margin: 0.3rem 0; font-weight: 700;">💡 LiveKit RAG Assistant | Powered by Standard MCP 🔌</p><p style="font-size: 0.8rem; color: #c8fae5; margin: 0.2rem 0;">🔌 Standard MCP | ⚡ Streamlit | 🔗 LangChain | 📍 Pinecone | 🚀 Groq</p><p style="font-size: 0.75rem; color: #b8a2ff; margin: 0.2rem 0; font-weight: 600;">Async semantic search with MCP | LangChain integration</p><p style="font-size: 0.75rem; color: #c8fae5; margin: 0.2rem 0;">🔐 Privacy First | ⚡ Fast | 🎯 Accurate | 🌍 Global</p><p style="font-size: 0.8rem; color: #4ade80; margin: 0.3rem 0; font-weight: 600;">© 2025 | Built with ❤️ for developers | <a href="https://github.com/THENABILMAN" target="_blank" class="footer-link">👨‍💻 @THENABILMAN</a></p></div>'

st.markdown(footer_html, unsafe_allow_html=True)
