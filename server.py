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
def niplex_helper(query: str) -> str:
    """A helper tool for NIPLEX operations."""
    return tools.helper(query)

if __name__ == "__main__":
    port = 7860
    mcp.run(transport="http", host="0.0.0.0", port=port)
