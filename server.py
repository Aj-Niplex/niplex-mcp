import os
from fastmcp import FastMCP

mcp = FastMCP("NIPLEX-MCP")

@mcp.tool()
def niplex_helper(query: str) -> str:
    """A helper tool for NIPLEX operations."""
    return f"NIPLEX-MCP Helper response to: {query}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    mcp.run(transport="http", host="0.0.0.0", port=port)