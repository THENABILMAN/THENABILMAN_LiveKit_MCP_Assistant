"""
Direct test of MCP server initialization
"""

import asyncio
import sys
import os

async def test_server():
    """Test MCP server directly"""
    print("Testing MCP Server startup...")
    
    # Import and run the main function
    sys.path.insert(0, os.path.dirname(__file__))
    from mcp_server_standard import main
    
    print("Running server main...")
    try:
        await asyncio.wait_for(main(), timeout=5)
    except asyncio.TimeoutError:
        print("✅ Server started and is listening (timeout expected)")
    except KeyboardInterrupt:
        print("Interrupted")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_server())
