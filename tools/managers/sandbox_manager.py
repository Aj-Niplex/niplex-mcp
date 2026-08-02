import os
from integrations.daytona import DaytonaBridge
from integrations.e2b_bridge import E2BBridge


class SandboxManager:
    """Owns code execution: Daytona (long-run) and E2B (short-run + computer use)."""

    def __init__(self):
        self.daytona = DaytonaBridge(api_key=os.getenv("DAYTONA_API_KEY"))
        self.e2b = E2BBridge()

    def describe(self):
        return {
            "namespace": "sandbox",
            "description": "Code execution sandboxes. Daytona for longer/kept-alive runs, E2B for short quick runs and desktop computer-use automation.",
            "tools": {
                "execute_in_sandbox": "Run a shell command in a disposable Daytona sandbox. Args: cmd, ttl (minutes, default 0 = destroy instantly).",
                "destroy_sandbox": "Manually destroy a kept-alive Daytona sandbox. Args: id.",
                "e2b_run_code": "Run code in a short-lived E2B sandbox. Args: code, language (default 'python').",
                "e2b_screenshot": "Take a screenshot of a fresh E2B desktop sandbox. Returns base64 PNG.",
                "e2b_computer_use": "Run a sequence of GUI actions (click/write/hotkey/launch/wait) in an E2B desktop sandbox. Args: actions (list of dicts).",
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
        return f"Unknown sandbox tool: {tool}"
