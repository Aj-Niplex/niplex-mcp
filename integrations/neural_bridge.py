import os
import asyncio


class NeuralBridge:
    """
    Calls Neural-MCP (a separate deployed MCP server) as a proper MCP
    client — not a raw REST call, since Neural-MCP exposes tools over the
    MCP protocol. Requires:
        NEURAL_MCP_URL      — e.g. https://neural-mcp.up.horizon.sh/mcp
        NEURAL_MCP_API_KEY  — same key set as NEURAL_MCP_API_KEY on Neural-MCP's side
    """

    def __init__(self):
        self.url = os.environ.get("NEURAL_MCP_URL")
        self.api_key = os.environ.get("NEURAL_MCP_API_KEY")

    def _call_tool_sync(self, tool_name: str, **kwargs) -> str:
        if not self.url:
            return "NEURAL_MCP_URL not configured — Neural-MCP hasn't been deployed/wired yet."
        if not self.api_key:
            return "NEURAL_MCP_API_KEY not configured."

        async def _call():
            from fastmcp import Client
            # Current fastmcp versions don't accept `headers=` on the
            # top-level Client constructor — bearer tokens go through the
            # `auth` parameter instead, which fastmcp formats into the
            # Authorization header for us.
            async with Client(self.url, auth=self.api_key) as client:
                result = await client.call_tool(tool_name, kwargs)
                return result.content[0].text if result.content else str(result)

        try:
            return asyncio.run(_call())
        except Exception as e:
            return f"Neural-MCP call error: {str(e)}"

    def ask(self, query: str) -> str:
        return self._call_tool_sync("ask_neural", query=query)

    def log(self, summary: str) -> str:
        return self._call_tool_sync("log_to_neural", summary=summary)
