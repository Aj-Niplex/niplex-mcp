import os
import subprocess
import sys
from fastmcp import FastMCP
from tools.manager import MCPTools

# Dependencies Bootloader
def install_deps():
    required = {"fastmcp": "fastmcp", "requests": "requests", "daytona": "daytona", "pymongo": "pymongo", "paramiko": "paramiko"}
    for imp, pkg in required.items():
        try: __import__(imp)
        except ImportError: subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

install_deps()

mcp = FastMCP("NIPLEX-MCP")
tools = MCPTools()

@mcp.tool()
def list_github_files(path=""): return tools.list_files(path)

@mcp.tool()
def read_github_file(path): return tools.read_file(path)

@mcp.tool()
def write_github_file(path, content, message="Update file via NIPLEX-MCP"):
    return tools.write_file(path, content, message)

@mcp.tool()
def execute_in_sandbox(cmd, ttl=0): return tools.run_sandbox(cmd, ttl)

@mcp.tool()
def scrape_website(url): return tools.scrape_web(url)

@mcp.tool()
def search_web(q, m='web'): return tools.search_web(q, m)

@mcp.tool()
def search_youtube(q, res=10): return tools.search_youtube(q, res)

@mcp.tool()
def get_youtube_details(ids): return tools.get_yt_details(ids)

@mcp.tool()
def get_youtube_stats(ids): return tools.get_yt_stats(ids)

@mcp.tool()
def niplex_helper(q): return tools.helper(q)

@mcp.tool()
def list_hidencloud_files(path="/"): return tools.list_hidencloud_files(path)

@mcp.tool()
def read_hidencloud_file(path): return tools.read_hidencloud_file(path)

@mcp.tool()
def write_hidencloud_file(path, content): return tools.write_hidencloud_file(path, content)

@mcp.tool()
def delete_hidencloud_file(path): return tools.delete_hidencloud_file(path)

@mcp.tool()
def e2b_run_code(code, language="python"): return tools.e2b_run_code(code, language)

@mcp.tool()
def e2b_screenshot(): return tools.e2b_screenshot()

@mcp.tool()
def e2b_computer_use(actions): return tools.e2b_computer_use(actions)

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=7860)
