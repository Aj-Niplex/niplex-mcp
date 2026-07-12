import os
import requests
import time
import base64
from fastmcp import FastMCP

mcp = FastMCP("NIPLEX-MCP")

# Configuration
GITHUB_PAT = os.environ.get("GITHUB_PAT")
GITHUB_USER = "Aj-Niplex"
REPO_NAME = "niplex-mcp"

DAYTONA_API_KEY = "dtn_615e28da297188987212472de1f9f14fc152687780df3d3e9be300fe82d1066f"
DAYTONA_API_URL = "https://app.daytona.io/api"

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

def daytona_request(endpoint, method="GET", data=None):
    url = f"{DAYTONA_API_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {DAYTONA_API_KEY}",
        "Content-Type": "application/json"
    }
    res = requests.request(method, url, headers=headers, json=data)
    if res.status_code not in [200, 201]:
        return {"error": f"Daytona API Error {res.status_code}: {res.text}"}
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
    
    content_decoded = base64.b64decode(content_encoded).decode("utf-8")
    return content_decoded

@mcp.tool()
def niplex_helper(query: str) -> str:
    """A helper tool for NIPLEX operations."""
    return f"NIPLEX-MCP Helper response to: {query}"

@mcp.tool()
def execute_in_sandbox(command: str) -> str:
    """
    Runs a command in a temporary Daytona sandbox. 
    The sandbox is provisioned, executed, and destroyed immediately to save credits.
    """
    try:
        # 1. PROVISION: Create Workspace
        create_res = daytona_request("workspaces", method="POST", data={"name": "temp-exec-sandbox"})
        if "error" in create_res:
            return f"Provisioning Error: {create_res['error']}"
        
        workspace_id = create_res.get("id")
        if not workspace_id:
            return "Error: Failed to retrieve workspace ID from Daytona."

        # 2. WAIT: Poll until workspace is ready
        max_retries = 10
        ready = False
        for _ in range(max_retries):
            status_res = daytona_request(f"workspaces/{workspace_id}")
            if status_res.get("status") == "running":
                ready = True
                break
            time.sleep(3)
        
        if not ready:
            daytona_request(f"workspaces/{workspace_id}", method="DELETE")
            return "Error: Sandbox failed to start within the timeout period."

        # 3. EXECUTE: Run the command
        exec_res = daytona_request(f"workspaces/{workspace_id}/exec", method="POST", data={"command": command})
        output = exec_res.get("stdout", "") + exec_res.get("stderr", "")
        if not output and "error" in exec_res:
            output = exec_res["error"]

        # 4. DESTROY: Immediately stop/delete workspace to save credits
        daytona_request(f"workspaces/{workspace_id}", method="DELETE")
        
        return f"[Disposable Sandbox Result]:\n{output}"

    except Exception as e:
        return f"Critical Error during sandbox execution: {str(e)}"

if __name__ == "__main__":
    port = 7860
    mcp.run(transport="http", host="0.0.0.0", port=port)
