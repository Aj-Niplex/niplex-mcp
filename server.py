import os
import subprocess
import sys
from fastmcp import FastMCP
from tools.managers.git_manager import GitManager
from tools.managers.sandbox_manager import SandboxManager
from tools.managers.sftp_manager import SftpManager
from tools.managers.search_manager import SearchManager
from tools.managers.youtube_manager import YoutubeManager
from tools.managers.misc_manager import MiscManager
from tools.managers.google_manager import GoogleManager

# Dependencies Bootloader
def install_deps():
    required = {"fastmcp": "fastmcp", "requests": "requests", "daytona": "daytona", "pymongo": "pymongo", "paramiko": "paramiko"}
    for imp, pkg in required.items():
        try: __import__(imp)
        except ImportError: subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

install_deps()

mcp = FastMCP("NIPLEX-MCP")

git = GitManager()
sandbox = SandboxManager()
sftp = SftpManager()
search = SearchManager()
yt = YoutubeManager()
misc = MiscManager()
google = GoogleManager()

# ---------- git ----------

@mcp.tool()
def git_list_repos():
    return git.call("list_repos")

@mcp.tool()
def git_create_repo(name: str, private: bool = True, description: str = "", auto_init: bool = True):
    return git.call("create_repo", name=name, private=private, description=description, auto_init=auto_init)

@mcp.tool()
def list_github_files(repo: str = "niplex-mcp", path: str = ""):
    return git.call("list_files", repo=repo, path=path)

@mcp.tool()
def read_github_file(repo: str, file_path: str):
    return git.call("read_file", repo=repo, file_path=file_path)

@mcp.tool()
def write_github_file(repo: str, file_path: str, content: str, commit_message: str = "Update file via NIPLEX-MCP", branch: str = None):
    return git.call("write_file", repo=repo, file_path=file_path, content=content, commit_message=commit_message, branch=branch)

@mcp.tool()
def git_create_branch(repo: str, branch_name: str, from_branch: str = "main"):
    return git.call("create_branch", repo=repo, branch_name=branch_name, from_branch=from_branch)

@mcp.tool()
def git_list_branches(repo: str = "niplex-mcp"):
    return git.call("list_branches", repo=repo)

@mcp.tool()
def git_list_commits(repo: str = "niplex-mcp", branch: str = "main", limit: int = 10):
    return git.call("list_commits", repo=repo, branch=branch, limit=limit)

@mcp.tool()
def git_get_commit(repo: str, sha: str):
    return git.call("get_commit", repo=repo, sha=sha)

@mcp.tool()
def git_create_issue(repo: str, title: str, body: str = "", labels: list = None):
    return git.call("create_issue", repo=repo, title=title, body=body, labels=labels)

@mcp.tool()
def git_list_issues(repo: str = "niplex-mcp", state: str = "open"):
    return git.call("list_issues", repo=repo, state=state)

@mcp.tool()
def git_add_issue_comment(repo: str, issue_number: int, comment: str):
    return git.call("add_issue_comment", repo=repo, issue_number=issue_number, comment=comment)

@mcp.tool()
def git_create_pull_request(repo: str, title: str, head: str, base: str = "main", body: str = ""):
    return git.call("create_pull_request", repo=repo, title=title, head=head, base=base, body=body)

@mcp.tool()
def git_list_pull_requests(repo: str = "niplex-mcp", state: str = "open"):
    return git.call("list_pull_requests", repo=repo, state=state)

# ---------- sandbox ----------

@mcp.tool()
def execute_in_sandbox(cmd: str, ttl: int = 0):
    return sandbox.call("execute_in_sandbox", cmd=cmd, ttl=ttl)

@mcp.tool()
def destroy_sandbox(id: str):
    return sandbox.call("destroy_sandbox", id=id)

@mcp.tool()
def e2b_run_code(code: str, language: str = "python"):
    return sandbox.call("e2b_run_code", code=code, language=language)

@mcp.tool()
def e2b_screenshot():
    return sandbox.call("e2b_screenshot")

@mcp.tool()
def e2b_computer_use(actions: list):
    return sandbox.call("e2b_computer_use", actions=actions)

@mcp.tool()
def horizon_run_code(code: str, language: str = "python"):
    return sandbox.call("horizon_run_code", code=code, language=language)

@mcp.tool()
def horizon_health():
    return sandbox.call("horizon_health")

# ---------- sftp ----------

@mcp.tool()
def list_hidencloud_files(path: str = "/"):
    return sftp.call("list_files", path=path)

@mcp.tool()
def read_hidencloud_file(path: str):
    return sftp.call("read_file", path=path)

@mcp.tool()
def write_hidencloud_file(path: str, content: str):
    return sftp.call("write_file", path=path, content=content)

@mcp.tool()
def delete_hidencloud_file(path: str):
    return sftp.call("delete_file", path=path)

# ---------- search ----------

@mcp.tool()
def search_web(q: str, m: str = "web"):
    return search.call("search_web", q=q, m=m)

@mcp.tool()
def scrape_website(url: str):
    return search.call("scrape_website", url=url)

# ---------- youtube ----------

@mcp.tool()
def search_youtube(q: str, res: int = 10):
    return yt.call("search_youtube", q=q, res=res)

@mcp.tool()
def get_youtube_details(ids: list):
    return yt.call("get_video_details", ids=ids)

@mcp.tool()
def get_youtube_stats(ids: list):
    return yt.call("get_channel_stats", ids=ids)

# ---------- misc ----------

@mcp.tool()
def niplex_helper(q: str):
    return misc.call("helper", q=q)

# ---------- google (account = "professional" | "personal" | "company") ----------

@mcp.tool()
def gmail_search(account: str, query: str, max_results: int = 10):
    return google.call("search_emails", account=account, query=query, max_results=max_results)

@mcp.tool()
def gmail_get_thread(account: str, thread_id: str):
    return google.call("get_thread_details", account=account, thread_id=thread_id)

@mcp.tool()
def gmail_create_draft(account: str, to: str, subject: str, body: str):
    return google.call("create_draft", account=account, to=to, subject=subject, body=body)

@mcp.tool()
def calendar_list_events(account: str, time_min: str = None, time_max: str = None, max_results: int = 10):
    return google.call("list_events", account=account, time_min=time_min, time_max=time_max, max_results=max_results)

@mcp.tool()
def calendar_create_event(account: str, summary: str, start_time: str, end_time: str, description: str = "", attendees: list = None):
    return google.call("create_event", account=account, summary=summary, start_time=start_time, end_time=end_time, description=description, attendees=attendees)

@mcp.tool()
def calendar_update_event(account: str, event_id: str, summary: str = None, start_time: str = None, end_time: str = None, status: str = None):
    return google.call("update_event", account=account, event_id=event_id, summary=summary, start_time=start_time, end_time=end_time, status=status)

@mcp.tool()
def drive_search_files(account: str, query: str, max_results: int = 10):
    return google.call("search_files", account=account, query=query, max_results=max_results)

@mcp.tool()
def docs_read(account: str, doc_id: str):
    return google.call("read_doc", account=account, doc_id=doc_id)

@mcp.tool()
def docs_create(account: str, title: str, content: str = ""):
    return google.call("create_doc", account=account, title=title, content=content)

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=7860)
