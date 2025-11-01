"""
MCP Client for connecting to mcp_server_standard.py
Provides a persistent connection interface for Streamlit application
"""

import asyncio
import json
import sys
import os
import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class MCPClient:
    """Manages persistent connection to MCP server."""
    
    def __init__(self):
        self.process = None
        self.session = None
        self._initialized = False
    
    @asynccontextmanager
    async def _get_session(self):
        """Context manager for MCP client session."""
        try:
            from mcp.client.stdio import stdio_client, StdioServerParameters
            from mcp.client.session import ClientSession
            
            # Get path to server
            server_path = os.path.join(os.path.dirname(__file__), "mcp_server_standard.py")
            
            # Create server parameters
            server_params = StdioServerParameters(
                command=sys.executable,
                args=[server_path]
            )
            
            # Connect to server via stdio
            async with stdio_client(server_params) as (read, write):
                logger.info("✅ Connected to MCP Server")
                # Create session
                async with ClientSession(read, write) as session:
                    yield session
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {str(e)}")
            raise
    
    async def search_documentation(
        self, 
        query: str, 
        top_k: int = 4
    ) -> List[str]:
        """
        Search LiveKit documentation via MCP server.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of formatted documentation chunks
        """
        try:
            async with self._get_session() as session:
                logger.info(f"Searching documentation for: {query}")
                
                # Call tool via MCP protocol
                response = await session.call_tool(
                    name="search_documentation",
                    arguments={
                        "query": query,
                        "top_k": top_k
                    }
                )
                
                # Extract text from response
                if response and hasattr(response, 'content') and response.content:
                    # Response is a list of TextContent objects
                    text_content = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])
                    
                    # If response is already good, return as-is
                    if text_content.strip():
                        # Split by document separators and filter
                        docs = []
                        for section in text_content.split("---"):
                            section = section.strip()
                            if section and len(section) > 20:
                                docs.append(section)
                        
                        if docs:
                            logger.info(f"✓ Retrieved {len(docs)} documentation chunks")
                            return docs
                    
                    logger.warning(f"Empty or invalid response from documentation search: {text_content[:100]}")
                    return []
                else:
                    logger.warning(f"No content in response: {response}")
                    return []
                    
        except Exception as e:
            logger.error(f"Documentation search error: {str(e)}", exc_info=True)
            raise
    
    async def search_web(
        self,
        query: str,
        topic: str = "general"
    ) -> List[Dict[str, str]]:
        """
        Search web via MCP server.
        
        Args:
            query: Search query
            topic: Search topic type ('general' or 'news')
            
        Returns:
            List of search results with title, url, content
        """
        try:
            async with self._get_session() as session:
                logger.info(f"Searching web for: {query}")
                
                # Call tool via MCP protocol
                response = await session.call_tool(
                    name="search_web",
                    arguments={
                        "query": query,
                        "topic": topic
                    }
                )
                
                # Extract text from response
                if response and hasattr(response, 'content') and response.content:
                    text_content = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])
                    
                    # Parse formatted results
                    results = []
                    for result_section in text_content.split("---"):
                        result_section = result_section.strip()
                        if result_section and len(result_section) > 20:
                            results.append(result_section)
                    
                    logger.info(f"✓ Retrieved {len(results)} web results")
                    return results if results else []
                else:
                    logger.warning("Empty response from web search")
                    return []
                    
        except Exception as e:
            logger.error(f"Web search error: {str(e)}")
            raise
    
    async def list_available_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools."""
        try:
            async with self._get_client() as (read, write):
                tools = await read.list_tools()
                logger.info(f"✓ Available tools: {[t.name for t in tools]}")
                return tools
        except Exception as e:
            logger.error(f"Error listing tools: {str(e)}")
            raise


# Global client instance (for Streamlit caching)
_mcp_client: Optional[MCPClient] = None

def get_mcp_client() -> MCPClient:
    """Get or create global MCP client instance."""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client


# Streamlit-friendly wrapper functions
def search_documentation_sync(query: str, top_k: int = 4) -> List[str]:
    """
    Synchronous wrapper for documentation search.
    Use this in Streamlit apps.
    """
    client = get_mcp_client()
    try:
        # Handle event loop for Streamlit compatibility
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        logger.info(f"🔍 Searching for: {query}")
        
        # Run async function
        results = loop.run_until_complete(
            client.search_documentation(query, top_k)
        )
        
        if results:
            logger.info(f"✅ Found {len(results)} results")
        else:
            logger.warning(f"⚠️ No results found for: {query}")
            
        return results
    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        return []


def search_web_sync(query: str, topic: str = "general") -> List[Dict[str, str]]:
    """
    Synchronous wrapper for web search.
    Use this in Streamlit apps.
    """
    client = get_mcp_client()
    try:
        # Handle event loop for Streamlit compatibility
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        logger.info(f"🌐 Web searching for: {query}")
        
        # Run async function
        results = loop.run_until_complete(
            client.search_web(query, topic)
        )
        
        if results:
            logger.info(f"✅ Found {len(results)} web results")
        else:
            logger.warning(f"⚠️ No web results found for: {query}")
            
        return results
    except Exception as e:
        logger.error(f"Web search failed: {str(e)}", exc_info=True)
        return []
