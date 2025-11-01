"""
Standard MCP Server with LangChain Integration
Model Context Protocol implementation for LiveKit Documentation Search
Using proper stdio-based communication (Conventional MCP)
"""

import os
import sys
import asyncio
import logging
from typing import Any
from dotenv import load_dotenv

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolResult
import mcp.types as types
from mcp.server.models import InitializationOptions

# LangChain imports
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import Pinecone

# Tavily imports
from tavily import TavilyClient

load_dotenv()

# Configure logging (output to stderr to not interfere with MCP protocol on stdout)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Initialize MCP Server
mcp_server = Server("livekit-assistant")

# API Keys
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME") or os.getenv("PINECONE_INDEX", "livekit-docs")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

# Lazy loading globals
_embeddings = None
_vector_store = None
_tavily_client = None

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

def get_tavily_client():
    """Get or create Tavily client (lazy load)."""
    global _tavily_client
    if _tavily_client is None:
        if not TAVILY_API_KEY:
            logger.warning("TAVILY_API_KEY not set")
            return None
        _tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        logger.info("✓ Tavily client ready")
    return _tavily_client

@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="search_documentation",
            description="Search LiveKit documentation",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="search_web",
            description="Search the web",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "topic": {"type": "string"}
                },
                "required": ["query"]
            }
        )
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    """Execute MCP tools."""
    logger.info(f"========== TOOL CALL ==========")
    logger.info(f"Tool name: {name}")
    logger.info(f"Arguments type: {type(arguments)}")
    logger.info(f"Arguments: {arguments}")
    logger.info(f"==============================")
    
    try:
        if name == "search_documentation":
            # Validate arguments
            if arguments is None:
                logger.error("Arguments is None!")
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: Arguments is None")],
                    isError=True
                )
                
            if not isinstance(arguments, dict):
                logger.error(f"Arguments is not a dict, it's {type(arguments)}: {arguments}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: Arguments must be a dict, got {type(arguments)}")],
                    isError=True
                )
            
            if "query" not in arguments:
                logger.error(f"Missing 'query' in arguments: {list(arguments.keys())}")
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: Missing required 'query' parameter")],
                    isError=True
                )
            
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 4)
            
            logger.info(f"Searching documentation for: {query} (top_k={top_k})")
            
            try:
                vector_store = get_vector_store()
                results = vector_store.similarity_search(query, k=top_k)
                
                logger.info(f"Found {len(results)} results")
                
                if not results:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text="No relevant documentation found for your query. Please try a different search term or make sure the documentation index is populated."
                        )]
                    )
                
                # Format results
                formatted_results = []
                for i, doc in enumerate(results, 1):
                    content = f"**Document {i}:**\n{doc.page_content}\n"
                    if doc.metadata:
                        content += f"\nSource: {doc.metadata.get('source', 'Unknown')}\n"
                    formatted_results.append(content)
                
                response_text = "\n---\n".join(formatted_results)
                return CallToolResult(content=[TextContent(type="text", text=response_text)])
                
            except Exception as e:
                logger.error(f"Vector store error: {str(e)}", exc_info=True)
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Error accessing documentation database: {str(e)}\n\nPlease run: python ingest_comprehensive.py"
                    )],
                    isError=True
                )
        
        elif name == "search_web":
            query = arguments.get("query", "")
            topic = arguments.get("topic", "general")
            
            logger.info(f"Searching web for: {query}")
            
            try:
                client = get_tavily_client()
                if not client:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text="Web search is not configured. Set TAVILY_API_KEY environment variable."
                        )],
                        isError=True
                    )
                
                response = client.search(
                    query=query,
                    topic=topic,
                    max_results=5
                )
                
                if not response or not response.get("results"):
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text="No web search results found."
                        )]
                    )
                
                # Format results
                formatted_results = []
                for i, result in enumerate(response["results"], 1):
                    content = f"**Result {i}:**\n"
                    content += f"Title: {result.get('title', 'N/A')}\n"
                    content += f"URL: {result.get('url', 'N/A')}\n"
                    content += f"Content: {result.get('content', 'N/A')}\n"
                    formatted_results.append(content)
                
                response_text = "\n---\n".join(formatted_results)
                return CallToolResult(content=[TextContent(type="text", text=response_text)])
                
            except Exception as e:
                logger.error(f"Web search error: {str(e)}", exc_info=True)
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Web search error: {str(e)}"
                    )],
                    isError=True
                )
        
        else:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )]
            )
    
    except Exception as e:
        logger.error(f"Error calling tool {name}: {str(e)}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )],
            isError=True
        )

async def main():
    """Main entry point for MCP server."""
    logger.info("🚀 Starting MCP Server on stdio...")
    logger.info("✅ MCP Server initialized with:")
    logger.info("   - search_documentation tool")
    logger.info("   - search_web tool")
    logger.info("Ready for client connections...")
    
    # Import server components
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream, 
            write_stream,
            InitializationOptions(
                server_name="livekit-assistant",
                server_version="1.0.0",
                capabilities={}
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
