"""
Test MCP Server and Client connection
"""

import asyncio
import sys
import os
import subprocess

async def test_mcp():
    """Test MCP server and client"""
    print("=" * 60)
    print("🧪 Testing MCP Server and Client")
    print("=" * 60)
    
    try:
        from mcp.client.stdio import stdio_client, StdioServerParameters
        from mcp.client.session import ClientSession
        print("✅ MCP client imported successfully")
        
        # Get the path to mcp_server_standard.py
        server_path = os.path.join(os.path.dirname(__file__), "mcp_server_standard.py")
        print(f"\n📍 Server path: {server_path}")
        print(f"   Exists: {os.path.exists(server_path)}")
        
        print("\n🚀 Connecting to MCP Server...")
        
        # Create server parameters
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[server_path]
        )
        
        async with stdio_client(server_params) as (read, write):
            print("✅ Connected to MCP Server!")
            
            # Create session
            async with ClientSession(read, write) as session:
                # Test documentation search directly
                print("\n🔍 Testing documentation search...")
                test_query = "LiveKit installation"
                print(f"   Query: '{test_query}'")
                
                try:
                    response = await session.call_tool(
                        name="search_documentation",
                        arguments={
                            "query": test_query,
                            "top_k": 3
                        }
                    )
                    
                    if response and hasattr(response, 'content') and response.content:
                        text = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])
                        print(f"✅ Got response ({len(text)} chars)")
                        print(f"\n📄 Response preview:")
                        print(f"   {text[:300]}")
                    else:
                        print(f"❌ No response: {response}")
                except Exception as e:
                    print(f"❌ Error calling tool: {str(e)}")
                    import traceback
                    traceback.print_exc()
                
                print("\n" + "=" * 60)
                print("✅ MCP test completed successfully!")
                print("=" * 60)
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_mcp())
    sys.exit(0 if success else 1)
