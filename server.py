from fastmcp import FastMCP
from tools.manager import MCPTools

mcp = FastMCP("NIPLEX-MCP")
tools = MCPTools()

@mcp.tool()
def list_github_files(path: str = "") -> str:
    """List files in the NIPLEX-MCP repository. Path is relative to root."""
    return tools.list_files(path)

@mcp.tool()
def read_github_file(file_path: str) -> str:
    """Read the content of a specific file in the NIPLEX-MCP repository."""
    return tools.read_file(file_path)

@mcp.tool()
def execute_in_sandbox(command: str) -> str:
    """Runs a command in a temporary Daytona sandbox and destroys it immediately."""
    return tools.run_sandbox(command)

@mcp.tool()
def niplex_helper(query: str) -> str:
    """A helper tool for NIPLEX operations."""
    return tools.helper(query)

if __name__ == "__main__":
    port = 7860
    mcp.run(transport="http", host="0.0.0.0", port=port)
