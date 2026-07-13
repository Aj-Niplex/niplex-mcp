import os
import subprocess
import sys

# --- BOOTLOADER: Ensure dependencies are installed at runtime ---
def install_dependencies():
    required = {
        "fastmcp": "fastmcp",
        "requests": "requests",
        "daytona": "daytona"
    }
    for import_name, pkg_name in required.items():
        try:
            __import__(import_name)
        except ImportError:
            print(f"Installing missing dependency: {pkg_name}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name])

install_dependencies()
# --------------------------------------------------------------

import requests
import time
import base64
from fastmcp import FastMCP
from integrations.github import GithubBridge
from integrations.daytona import DaytonaBridge
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
def execute_in_sandbox(command: str, ttl_minutes: int = 0) -> str:
    """
    Runs a command in a Daytona sandbox. 
    ttl_minutes: If > 0, the sandbox stays alive for this many minutes.
    If 0 (default), the sandbox is destroyed immediately.
    """
    return tools.run_sandbox(command, ttl_minutes)

@mcp.tool()
def delete_sandbox(sandbox_id: str) -> str:
    """Manually destroys a specific Daytona sandbox immediately."""
    return tools.destroy_sandbox(sandbox_id)

@mcp.tool()
def query_neural_os(query: str) -> str:
    """Query the Neural-OS Life Database for goals, tasks, and profiles."""
    return tools.query_neural_os(query)

@mcp.tool()
def update_neural_os(key: str, value: str) -> str:
    """Update a record in the Neural-OS Life Database."""
    return tools.update_neural_os(key, value)

@mcp.tool()
def scrape_website(url: str) -> str:
    """Scrape content from a website via the NIPLEX Web Scraper API."""
    return tools.scrape_web(url)

@mcp.tool()
def search_web(query: str, mode: str = 'web') -> str:
    """
    Perform a web search via You.com. 
    mode: 'web' for fast search, 'research' for deep agentic synthesis.
    """
    return tools.search_web(query, mode)

@mcp.tool()
def niplex_helper(query: str) -> str:
    """A helper tool for NIPLEX operations."""
    return tools.helper(query)

@mcp.tool()
def call_remote_mcp(server: str, tool: str, args: str) -> str:
    """
    Delegates a tool call to another MCP server.
    server: Key or URL of the remote server.
    tool: Name of the tool to call.
    args: JSON string of arguments.
    """
    import json
    try:
        parsed_args = json.loads(args)
        return tools.call_remote_tool(server, tool, parsed_args)
    except json.JSONDecodeError:
        return "Error: arguments must be a valid JSON string."

if __name__ == "__main__":
    port = 7860
    mcp.run(transport="http", host="0.0.0.0", port=port)
