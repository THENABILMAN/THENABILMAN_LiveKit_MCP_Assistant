"""
Minimal MCP Client for testing
"""

import asyncio
import sys
import os
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

async def test():
    """Test the minimal server."""
    print("Testing minimal MCP server...")
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[os.path.join(os.path.dirname(__file__), "minimal_server.py")]
    )
    
    async with stdio_client(server_params) as (read, write):
        print("✅ Connected!")
        
        async with ClientSession(read, write) as session:
            print("\n🔍 Calling echo tool...")
            response = await session.call_tool(
                name="echo"
            )
            
            print(f"✅ Response: {response.content[0].text}")

if __name__ == "__main__":
    asyncio.run(test())
