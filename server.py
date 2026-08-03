import os
import subprocess
import sys
from fastmcp import FastMCP
from tools.manager import Router

# Dependencies Bootloader
def install_deps():
    required = {"fastmcp": "fastmcp", "requests": "requests", "daytona": "daytona", "pymongo": "pymongo", "paramiko": "paramiko"}
    for imp, pkg in required.items():
        try: __import__(imp)
        except ImportError: subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

install_deps()

mcp = FastMCP("NIPLEX-MCP")
router = Router()

@mcp.tool()
def list_namespaces(namespace: str = None):
    """
    Discover available tool namespaces, or (with a namespace given) the
    full tool list + argument docs for that one namespace.
    Namespaces: git, sandbox, sftp, search, yt, misc.
    Call with no args first to see what's available.
    """
    return router.list_namespaces(namespace)

@mcp.tool()
def call_tool(namespace: str, tool: str, **kwargs):
    """
    Call any tool in any namespace. Use list_namespaces first to discover
    valid namespace/tool/argument combinations.
    Example: call_tool(namespace="git", tool="list_repos")
    Example: call_tool(namespace="sandbox", tool="execute_in_sandbox", cmd="echo hi")
    """
    return router.call_tool(namespace, tool, **kwargs)

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=7860)
