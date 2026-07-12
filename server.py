import os
import requests
from fastmcp import FastMCP

mcp = FastMCP("NIPLEX-MCP")

# Configuration - The token is pulled from the server's environment variables
GITHUB_PAT = os.environ.get("GITHUB_PAT")
GITHUB_USER = "Aj-Niplex"
REPO_NAME = "niplex-mcp"

def github_request(endpoint, method="GET", data=None):
    url = f"https://api.github.com/{endpoint}"
    headers = {
        "Authorization": f"token {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json"
    }
    if not GITHUB_PAT:
        return {"error": "GITHUB_PAT environment variable not set on server."}
    
    res = requests.request(method, url, headers=headers, json=data)
    if res.status_code != 200:
        return {"error": f"GitHub API Error {res.status_code}: {res.text}"}
    return res.json()

@mcp.tool()
def list_github_files(path: str = "") -> str:
    """List files in the NIPLEX-MCP repository. Path is relative to root."""
    endpoint = f"repos/{GITHUB_USER}/{REPO_NAME}/contents/{path}"
    data = github_request(endpoint)
    if "error" in data:
        return data["error"]
    
    files = [item["name"] for item in data]
    return "\n".join(files) if files else "No files found."

@mcp.tool()
def read_github_file(file_path: str) -> str:
    """Read the content of a specific file in the NIPLEX-MCP repository."""
    endpoint = f"repos/{GITHUB_USER}/{REPO_NAME}/contents/{file_path}"
    data = github_request(endpoint)
    if "error" in data:
        return data["error"]
    
    import base64
    content_encoded = data.get("content", "")
    if not content_encoded:
        return "File is empty or not found."
    
    # GitHub API returns base64 encoded content
    content_decoded = base64.b64decode(content_encoded).decode("utf-8")
    return content_decoded

@mcp.tool()
def niplex_helper(query: str) -> str:
    """A helper tool for NIPLEX operations."""
    return f"NIPLEX-MCP Helper response to: {query}"

if __name__ == "__main__":
    port = 7860
    mcp.run(transport="http", host="0.0.0.0", port=port)
