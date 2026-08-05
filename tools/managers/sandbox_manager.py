import os
from integrations.daytona import DaytonaBridge
from integrations.e2b_bridge import E2BBridge
from integrations.horizon_sandbox import HorizonSandboxBridge


class SandboxManager:
    """Owns code execution: Daytona (long-run), E2B (short-run + computer use),
    and Horizon (free self-hosted run_code, no per-use sandbox API cost)."""

    def __init__(self):
        self.daytona = DaytonaBridge(api_key=os.getenv("DAYTONA_API_KEY"))
        self.e2b = E2BBridge()
        self.horizon = HorizonSandboxBridge(url=os.getenv("HORIZON_SANDBOX_URL", "https://sandbox.fastmcp.app/mcp"))

    def describe(self):
        return {
            "namespace": "sandbox",
            "description": "Code execution sandboxes. Daytona for longer/kept-alive runs, E2B for short quick runs and desktop computer-use automation, Horizon for free code execution on our own hosted MCP server.",
            "tools": {
                "execute_in_sandbox": "Run a shell command in a disposable Daytona sandbox. Args: cmd, ttl (minutes, default 0 = destroy instantly).",
                "destroy_sandbox": "Manually destroy a kept-alive Daytona sandbox. Args: id.",
                "e2b_run_code": "Run code in a short-lived E2B sandbox. Args: code, language (default 'python').",
                "e2b_screenshot": "Take a screenshot of a fresh E2B desktop sandbox. Returns base64 PNG.",
                "e2b_computer_use": "Run a sequence of GUI actions (click/write/hotkey/launch/wait) in an E2B desktop sandbox. Args: actions (list of dicts).",
                "horizon_run_code": "Run code on our free Horizon-hosted sandbox MCP server. No per-call cost, generous but not unlimited (60s timeout, 1.5GB memory), full internet + env access. Args: code, language (default 'python').",
                "horizon_health": "Check whether the Horizon sandbox server is reachable.",
            }
        }

    def call(self, tool: str, **kwargs):
        if tool == "execute_in_sandbox":
            return self.daytona.execute_command(kwargs.get("cmd"), kwargs.get("ttl", 0))
        if tool == "destroy_sandbox":
            return self.daytona.delete_sandbox(kwargs.get("id"))
        if tool == "e2b_run_code":
            return self.e2b.run_code(kwargs.get("code"), kwargs.get("language", "python"))
        if tool == "e2b_screenshot":
            return self.e2b.desktop_screenshot()
        if tool == "e2b_computer_use":
            return self.e2b.desktop_run_actions(kwargs.get("actions", []))
        if tool == "horizon_run_code":
            return self.horizon.run_code(kwargs.get("code"), kwargs.get("language", "python"))
        if tool == "horizon_health":
            return self.horizon.health()
        return f"Unknown sandbox tool: {tool}"
