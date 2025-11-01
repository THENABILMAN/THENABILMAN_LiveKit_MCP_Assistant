"""
Minimal MCP Server for testing
"""

import asyncio
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolResult
from mcp.server.models import InitializationOptions

# Create server
server = Server("test-server")

@server.list_tools()
async def list_tools():
    """List tools."""
    return [
        Tool(
            name="echo",
            description="Echo the input"
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    """Call a tool."""
    import sys
    print(f"DEBUG: call_tool called with name={name}, arguments={arguments}", file=sys.stderr)
    
    if name == "echo":
        text = arguments.get("text", "") if arguments else ""
        return CallToolResult(
            content=[TextContent(type="text", text=f"You said: {text}")]
        )
    else:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unknown tool: {name}")],
            isError=True
        )

async def main():
    """Run the server."""
    async with stdio_server() as (read, write):
        await server.run(
            read,
            write,
            InitializationOptions(
                server_name="test-server",
                server_version="1.0.0",
                capabilities={}
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
