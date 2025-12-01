import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

REMOTE_MCP_HOST = "http://gateway-remote:8080"
LOCAL_MCP_HOST  = "http://gateway-local:9011"

async def call_mcp(host, tool, args):
    """Call a tool from Docker MCP Catalogue or remote MCP."""
    async with streamablehttp_client(host) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            result = await s.call_tool(tool, args)
            c = result.content
            return getattr(c[0], "text", None) if c else f"{tool} no content"

print("###############################################")
print(asyncio.run(call_mcp(REMOTE_MCP_HOST, "paper_search", {"query": "dolphins"})))
print("###############################################")
print(asyncio.run(call_mcp(LOCAL_MCP_HOST, "search", {"query": "cats"})))
print("###############################################")
print("## List Customers - LOCAL")
print(asyncio.run(call_mcp(LOCAL_MCP_HOST, "list_customers", {})))
print("###############################################")
print("## List Customers - REMOTE")
print(asyncio.run(call_mcp(REMOTE_MCP_HOST, "list_customers", {})))


