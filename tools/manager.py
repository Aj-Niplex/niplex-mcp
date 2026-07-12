from integrations.github import GithubBridge
from integrations.daytona import DaytonaBridge
import os

class MCPTools:
    def __init__(self):
        self.github = GithubBridge(user="Aj-Niplex", repo="niplex-mcp")
        self.daytona = DaytonaBridge(api_key="dtn_615e28da297188987212472de1f9f14fc152687780df3d3e9be300fe82d1066f")

    def list_files(self, path: str = "") -> str:
        return self.github.list_files(path)

    def read_file(self, file_path: str) -> str:
        return self.github.read_file(file_path)

    def write_file(self, file_path: str, content: str, commit_message: str = "Update via NIPLEX-MCP") -> str:
        return self.github.write_file(file_path, content, commit_message)

    def run_sandbox(self, command: str, ttl_minutes: int = 0) -> str:
        return self.daytona.execute_command(command, ttl_minutes)

    def write_sandbox_file(self, file_path: str, content: str) -> str:
        return self.daytona.write_file(file_path, content)

    def destroy_sandbox(self, sandbox_id: str) -> str:
        return self.daytona.delete_sandbox(sandbox_id)

    def helper(self, query: str) -> str:
        return f"NIPLEX-MCP Bridge Helper: {query}"
