from typing import Any, Dict, Optional
import requests
import os

class GithubBridge:
    """
    Multi-repo capable. `user` stays fixed (your account), but `repo` is now
    passed per-call so any repo under that account is reachable, not just
    niplex-mcp. Every method defaults repo="niplex-mcp" for backward compat.
    """

    def __init__(self, user: str = "Aj-Niplex"):
        self.user = user
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
        if res.status_code not in (200, 201, 204):
            return {"error": f"GitHub API Error {res.status_code}: {res.text}"}
        if res.status_code == 204 or not res.text:
            return {"success": True}
        return res.json()

    # ---------- Files ----------

    def list_files(self, repo: str = "niplex-mcp", path: str = "") -> str:
        endpoint = f"repos/{self.user}/{repo}/contents/{path}"
        data = self.request(endpoint)
        if isinstance(data, dict) and "error" in data: return data["error"]
        files = [item["name"] for item in data]
        return "\n".join(files) if files else "No files found."

    def read_file(self, repo: str, file_path: str) -> str:
        endpoint = f"repos/{self.user}/{repo}/contents/{file_path}"
        data = self.request(endpoint)
        if isinstance(data, dict) and "error" in data:
            return data["error"]
        if isinstance(data, list):
            return f"Error: '{file_path}' is a directory, not a file."
        content = data.get("content", "")
        encoding = data.get("encoding", "base64")
        if encoding == "base64":
            import base64
            try:
                return base64.b64decode(content).decode("utf-8")
            except UnicodeDecodeError:
                return "Error: file is binary and cannot be decoded as text."
        return content

    def write_file(self, repo: str, file_path: str, content: str, commit_message: str = "Update file via NIPLEX-MCP", branch: Optional[str] = None) -> str:
        endpoint = f"repos/{self.user}/{repo}/contents/{file_path}"
        params = f"?ref={branch}" if branch else ""
        current_data = self.request(endpoint + params)
        sha = None
        if isinstance(current_data, dict) and "sha" in current_data:
            sha = current_data["sha"]
        elif isinstance(current_data, dict) and "error" in current_data and "404" not in current_data["error"]:
            return current_data["error"]

        import base64
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        data = {"message": commit_message, "content": encoded_content}
        if sha:
            data["sha"] = sha
        if branch:
            data["branch"] = branch

        res = self.request(endpoint, method="PUT", data=data)
        if "error" in res:
            return res["error"]
        return f"Successfully updated {file_path} in {repo}" + (f" on branch {branch}." if branch else ".")

    # ---------- Repos ----------

    def list_repos(self) -> str:
        endpoint = "user/repos?per_page=100&affiliation=owner"
        data = self.request(endpoint)
        if isinstance(data, dict) and "error" in data: return data["error"]
        names = [r["name"] for r in data]
        return "\n".join(names) if names else "No repositories found."

    # ---------- Branches ----------

    def create_branch(self, repo: str, branch_name: str, from_branch: str = "main") -> str:
        ref_endpoint = f"repos/{self.user}/{repo}/git/ref/heads/{from_branch}"
        ref_data = self.request(ref_endpoint)
        if isinstance(ref_data, dict) and "error" in ref_data:
            return ref_data["error"]
        sha = ref_data.get("object", {}).get("sha")
        if not sha:
            return f"Could not resolve SHA for branch '{from_branch}'."

        create_endpoint = f"repos/{self.user}/{repo}/git/refs"
        data = {"ref": f"refs/heads/{branch_name}", "sha": sha}
        res = self.request(create_endpoint, method="POST", data=data)
        if "error" in res:
            return res["error"]
        return f"Branch '{branch_name}' created from '{from_branch}' in {repo}."

    def list_branches(self, repo: str = "niplex-mcp") -> str:
        endpoint = f"repos/{self.user}/{repo}/branches"
        data = self.request(endpoint)
        if isinstance(data, dict) and "error" in data:
            return data["error"]
        names = [b["name"] for b in data]
        return "\n".join(names) if names else "No branches found."

    # ---------- Commits ----------

    def list_commits(self, repo: str = "niplex-mcp", branch: str = "main", limit: int = 10) -> str:
        endpoint = f"repos/{self.user}/{repo}/commits?sha={branch}&per_page={limit}"
        data = self.request(endpoint)
        if isinstance(data, dict) and "error" in data:
            return data["error"]
        lines = []
        for c in data:
            sha_short = c["sha"][:7]
            msg = c["commit"]["message"].split("\n")[0]
            author = c["commit"]["author"]["name"]
            lines.append(f"{sha_short} - {msg} ({author})")
        return "\n".join(lines) if lines else "No commits found."

    def get_commit(self, repo: str, sha: str) -> str:
        endpoint = f"repos/{self.user}/{repo}/commits/{sha}"
        data = self.request(endpoint)
        if isinstance(data, dict) and "error" in data:
            return data["error"]
        msg = data["commit"]["message"]
        files = data.get("files", [])
        file_lines = [f"  {f['filename']} (+{f['additions']}/-{f['deletions']})" for f in files]
        return f"Commit {sha}\nMessage: {msg}\nFiles changed:\n" + "\n".join(file_lines)

    # ---------- Issues ----------

    def create_issue(self, repo: str, title: str, body: str = "", labels: Optional[list] = None) -> str:
        endpoint = f"repos/{self.user}/{repo}/issues"
        data = {"title": title, "body": body}
        if labels:
            data["labels"] = labels
        res = self.request(endpoint, method="POST", data=data)
        if "error" in res:
            return res["error"]
        return f"Issue #{res['number']} created in {repo}: {res['html_url']}"

    def list_issues(self, repo: str = "niplex-mcp", state: str = "open") -> str:
        endpoint = f"repos/{self.user}/{repo}/issues?state={state}"
        data = self.request(endpoint)
        if isinstance(data, dict) and "error" in data:
            return data["error"]
        lines = [f"#{i['number']} - {i['title']} ({i['state']})" for i in data if "pull_request" not in i]
        return "\n".join(lines) if lines else "No issues found."

    def add_issue_comment(self, repo: str, issue_number: int, comment: str) -> str:
        endpoint = f"repos/{self.user}/{repo}/issues/{issue_number}/comments"
        res = self.request(endpoint, method="POST", data={"body": comment})
        if "error" in res:
            return res["error"]
        return f"Comment added to issue #{issue_number} in {repo}."

    # ---------- Pull Requests ----------

    def create_pull_request(self, repo: str, title: str, head: str, base: str = "main", body: str = "") -> str:
        endpoint = f"repos/{self.user}/{repo}/pulls"
        data = {"title": title, "head": head, "base": base, "body": body}
        res = self.request(endpoint, method="POST", data=data)
        if "error" in res:
            return res["error"]
        return f"PR #{res['number']} created in {repo}: {res['html_url']}"

    def list_pull_requests(self, repo: str = "niplex-mcp", state: str = "open") -> str:
        endpoint = f"repos/{self.user}/{repo}/pulls?state={state}"
        data = self.request(endpoint)
        if isinstance(data, dict) and "error" in data:
            return data["error"]
        lines = [f"#{p['number']} - {p['title']} ({p['head']['ref']} -> {p['base']['ref']})" for p in data]
        return "\n".join(lines) if lines else "No pull requests found."

    # NOTE: merge_pull_request intentionally NOT implemented yet.
    # Auto-merging is a bigger trust boundary than read/create — worth a
    # deliberate decision with the user before wiring it in.
