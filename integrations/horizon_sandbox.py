import asyncio
import os
from typing import Any, Dict, List

from fastmcp import Client


class HorizonSandboxBridge:
    """
    Calls the `run_code` tool on our own Horizon-hosted 'sandbox' MCP
    server (https://sandbox.fastmcp.app/mcp) — a free alternative to
    paying for E2B/Daytona execution.

    Unlike GithubBridge/DaytonaBridge (plain REST via `requests`), this
    target is itself an MCP server, so we connect as an MCP *client*
    using fastmcp.Client rather than hitting a REST endpoint directly.

    Horizon enforces OAuth 2.1 on free-tier servers, but a plain Bearer
    token works fine for service-account-style access — pass it as a
    string to Client(auth=...) and FastMCP formats the Authorization
    header automatically.
    """

    def __init__(self, url: str = "https://sandbox.fastmcp.app/mcp", token: str = None):
        self.url = url
        self.token = token or os.environ.get("SANDBOX_TOKEN")

    def _run_async(self, coro):
        """FastMCP's Client is async-only; our manager/call() layer is
        sync, so each call opens a short-lived event loop. Fine for the
        call-and-return pattern used here — not meant for high-throughput
        concurrent use."""
        return asyncio.run(coro)

    async def _call_tool(self, tool_name: str, **kwargs) -> Any:
        async with Client(self.url, auth=self.token) as client:
            result = await client.call_tool(tool_name, kwargs)
            return result

    def run_code(self, code: str, language: str = "python") -> Dict:
        if not self.token:
            return {"error": "SANDBOX_TOKEN not set."}
        try:
            result = self._run_async(self._call_tool("run_code", code=code, language=language))
            # FastMCP client returns a CallToolResult; unwrap to the
            # actual dict payload our server's run_code returns.
            if hasattr(result, "data"):
                return result.data
            if hasattr(result, "content"):
                return {"raw": [str(c) for c in result.content]}
            return {"raw": str(result)}
        except Exception as e:
            return {"error": f"Horizon sandbox call failed: {e}"}

    def health(self) -> str:
        if not self.token:
            return "SANDBOX_TOKEN not set."
        try:
            result = self._run_async(self._call_tool("health"))
            if hasattr(result, "data"):
                return result.data
            return str(result)
        except Exception as e:
            return f"Horizon sandbox unreachable: {e}"
