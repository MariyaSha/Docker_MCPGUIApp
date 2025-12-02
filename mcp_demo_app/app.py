import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

# respective hosts/ports from docker-compose.yaml
REMOTE_MCP_HOST = "http://gateway-remote:8080"
LOCAL_MCP_HOST  = "http://gateway-local:9011"

async def call_mcp(host, tool, args):
    """
    Call a tool from Docker MCP Catalogue.
    - host: REMOTE_MCP_HOST or LOCAL_MCP_HOST
    - tool: string of tool name
    - args: dict of tool arguments or {}
    """
    # connect to different MCP Gateways
    async with streamablehttp_client(host) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            # call different tools with optional arguments
            result = await s.call_tool(tool, args)
            # verify results were returned with no errors
            c = result.content
            return getattr(c[0], "text", None) if c else f"{tool} no content"

print("###############################################")
# call tool from huggingface server
print(asyncio.run(call_mcp(REMOTE_MCP_HOST, "paper_search", {"query": "dolphins"})))
print("###############################################")
# call tool from duckduckgo server
print(asyncio.run(call_mcp(LOCAL_MCP_HOST, "search", {"query": "cats"})))
print("###############################################")
print("## List Customers - LOCAL")
# call tool from stripe server (local)
print(asyncio.run(call_mcp(LOCAL_MCP_HOST, "list_customers", {})))
print("###############################################")
print("## List Customers - REMOTE")
# call tool from stripe-remote server (remote)
print(asyncio.run(call_mcp(REMOTE_MCP_HOST, "list_customers", {})))

# you don't need to mention the name of the server -
# you only need the tool name! 