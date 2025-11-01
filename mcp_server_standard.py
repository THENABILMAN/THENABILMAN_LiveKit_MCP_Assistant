"""
Standard MCP Server with LangChain Integration
Model Context Protocol implementation for LiveKit Documentation Search
"""

import os
import sys
import logging
from typing import Any
from dotenv import load_dotenv

# MCP imports
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.types as types

# LangChain imports
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import Pinecone

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP Server
mcp_server = Server("livekit-assistant")

# API Keys
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME") or os.getenv("PINECONE_INDEX", "livekit-docs")

# Lazy loading globals
_embeddings = None
_vector_store = None

def get_embeddings():
    """Get or create embeddings model (lazy load)."""
    global _embeddings
    if _embeddings is None:
        logger.info("Loading HuggingFace embeddings model...")
        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    return _embeddings

def get_vector_store():
    """Get or create Pinecone vector store (lazy load)."""
    global _vector_store
    if _vector_store is None:
        logger.info(f"Initializing Pinecone vector store with index: {PINECONE_INDEX_NAME}")
        embeddings = get_embeddings()
        _vector_store = Pinecone(
            index_name=PINECONE_INDEX_NAME,
            embedding=embeddings
        )
        logger.info("✓ Pinecone vector store ready")
    return _vector_store

@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="search_documentation",
            description="Search LiveKit documentation using semantic search. Returns relevant documentation excerpts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query for LiveKit documentation"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 4)",
                        "default": 4
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="search_web",
            description="Search the web for information using Tavily API.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query for web search"
                    },
                    "topic": {
                        "type": "string",
                        "description": "Search topic type: 'general' or 'news'",
                        "default": "general"
                    }
                },
                "required": ["query"]
            }
        )
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent]:
    """Execute MCP tools."""
    try:
        if name == "search_documentation":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 4)
            
            logger.info(f"Searching documentation for: {query}")
            
            try:
                vector_store = get_vector_store()
                results = vector_store.similarity_search(query, k=top_k)
                
                logger.info(f"Found {len(results)} results")
                
                if not results:
                    return [TextContent(
                        type="text",
                        text="No relevant documentation found for your query. Please try a different search term or make sure the documentation index is populated."
                    )]
                
                # Format results
                formatted_results = []
                for i, doc in enumerate(results, 1):
                    content = f"**Document {i}:**\n{doc.page_content}\n"
                    if doc.metadata:
                        content += f"\nSource: {doc.metadata.get('source', 'Unknown')}\n"
                    formatted_results.append(content)
                
                response_text = "\n---\n".join(formatted_results)
                return [TextContent(type="text", text=response_text)]
                
            except Exception as e:
                logger.error(f"Vector store error: {str(e)}", exc_info=True)
                return [TextContent(
                    type="text",
                    text=f"Error accessing documentation database: {str(e)}\n\nPlease run: python ingest_docs.py"
                )]
        
        elif name == "search_web":
            query = arguments.get("query", "")
            topic = arguments.get("topic", "general")
            
            logger.info(f"Searching web for: {query}")
            
            from tavily import TavilyClient
            
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if not tavily_api_key:
                return [TextContent(
                    type="text",
                    text="Tavily API key not configured. Web search unavailable."
                )]
            
            client = TavilyClient(api_key=tavily_api_key)
            response = client.search(query=query, topic=topic, max_results=4)
            
            if "results" not in response or not response["results"]:
                return [TextContent(
                    type="text",
                    text="No web search results found."
                )]
            
            # Format web results
            formatted_results = []
            for i, result in enumerate(response["results"], 1):
                content = f"**Result {i}: {result.get('title', 'N/A')}**\n"
                content += f"{result.get('content', 'No content')}\n"
                content += f"Source: {result.get('url', 'N/A')}\n"
                formatted_results.append(content)
            
            response_text = "\n---\n".join(formatted_results)
            return [TextContent(type="text", text=response_text)]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        logger.error(f"Error calling tool {name}: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]

async def main():
    """Run the MCP server."""
    logger.info("Starting LiveKit Assistant MCP Server...")
    logger.info("✅ MCP Server initialized with:")
    logger.info("   - search_documentation tool")
    logger.info("   - search_web tool")
    logger.info("Ready for client connections...")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("MCP Server shutting down...")

if __name__ == "__main__":
    import asyncio
    
    # Handle command-line mode for direct queries
    if len(sys.argv) > 2 and sys.argv[1] == "search":
        query = sys.argv[2]
        top_k = int(sys.argv[3]) if len(sys.argv) > 3 else 4
        
        async def direct_search():
            try:
                vector_store = get_vector_store()
                results = vector_store.similarity_search(query, k=top_k)
                
                if not results:
                    print("No relevant documentation found.")
                    return
                
                formatted_results = []
                for i, doc in enumerate(results, 1):
                    content = f"**Document {i}:**\n{doc.page_content}\n"
                    if doc.metadata:
                        content += f"\nSource: {doc.metadata.get('source', 'Unknown')}\n"
                    formatted_results.append(content)
                
                print("\n---\n".join(formatted_results))
            except Exception as e:
                print(f"Error: {str(e)}", file=sys.stderr)
                sys.exit(1)
        
        asyncio.run(direct_search())
    else:
        asyncio.run(main())
