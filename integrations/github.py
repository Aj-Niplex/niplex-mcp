from typing import Any, Dict, Optional
import requests
import os

class GithubBridge:
    def __init__(self, user: str, repo: str):
        self.user = user
        self.repo = repo
        self.token = os.environ.get("GITHUB_PAT")

    def request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Any:
        url = f"https://api.github.com/{endpoint}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        if not self.token:
            return {"error": "GITHUB_PAT environment variable not set."}
        
        res = requests.request(method, url, headers=headers, json=data)
        if res.status_code != 200:
            return {"error": f"GitHub API Error {res.status_code}: {res.text}"}
        return res.json()

    def list_files(self, path: str = "") -> str:
        endpoint = f"repos/{self.user}/{self.repo}/contents/{path}"
        data = self.request(endpoint)
        if "error" in data: return data["error"]
        files = [item["name"] for item in data]
        return "\n".join(files) if files else "No files found."

    def read_file(self, file_path: str) -> str:
        endpoint = f"repos/{self.user}/{self.repo}/contents/{file_path}"
        data = self.request(endpoint)
        if "error" in data: return data["error"]
        import base64
        content = data.get("content", "")
        if not content: return "File is empty."
        return base64.b64decode(content).decode("utf-8")
