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

    def write_file(self, file_path: str, content: str, commit_message: str = "Update file via NIPLEX-MCP") -> str:
        # 1. Get the current SHA of the file if it exists
        endpoint = f"repos/{self.user}/{self.repo}/contents/{file_path}"
        current_data = self.request(endpoint)
        sha = None
        if "sha" in current_data:
            sha = current_data["sha"]
        elif "error" in current_data and "404" not in current_data["error"]:
            return current_data["error"]

        # 2. Prepare the PUT request
        import base64
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        
        data = {
            "message": commit_message,
            "content": encoded_content
        }
        if sha:
            data["sha"] = sha

        res = self.request(endpoint, method="PUT", data=data)
        if "error" in res:
            return res["error"]
        
        return f"Successfully updated {file_path} in GitHub."
