import os
import subprocess
import sys
from fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from tools.managers.git_manager import GitManager
from tools.managers.sandbox_manager import SandboxManager
from tools.managers.sftp_manager import SftpManager
from tools.managers.search_manager import SearchManager
from tools.managers.youtube_manager import YoutubeManager
from tools.managers.misc_manager import MiscManager
from tools.managers.google_manager import GoogleManager
from tools.managers.neural_manager import NeuralManager

# Dependencies Bootloader
def install_deps():
    required = {"fastmcp": "fastmcp", "requests": "requests", "daytona": "daytona", "pymongo": "pymongo", "paramiko": "paramiko"}
    for imp, pkg in required.items():
        try: __import__(imp)
        except ImportError: subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

install_deps()

# ---------- API Key Auth Middleware ----------
# Every request must include:  Authorization: Bearer <MCP_API_KEY>
# Set MCP_API_KEY in Horizon environment variables.
# Claude's custom connector sends this automatically once you add it to the
# connector's auth configuration on claude.ai.

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        expected = os.environ.get("MCP_API_KEY", "")
        if not expected:
            # If no key is configured, block everything — fail secure.
            return JSONResponse({"error": "MCP_API_KEY not configured on server."}, status_code=503)

        auth_header = request.headers.get("Authorization", "")
        token = auth_header.removeprefix("Bearer ").strip()

        if token != expected:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        return await call_next(request)

mcp = FastMCP("NIPLEX-MCP")
mcp.http_app().add_middleware(APIKeyMiddleware)

git = GitManager()
sandbox = SandboxManager()
sftp = SftpManager()
search = SearchManager()
yt = YoutubeManager()
misc = MiscManager()
google = GoogleManager()
neural = NeuralManager()

# ==================== GITHUB ====================

@mcp.tool()
def git_list_repos():
    """List every repository under the Aj-Niplex GitHub account. No arguments. Returns repo names, one per line."""
    return git.call("list_repos")

@mcp.tool()
def git_create_repo(name: str, private: bool = True, description: str = "", auto_init: bool = True):
    """Create a new GitHub repository under Aj-Niplex.
    Args: name (repo name), private (default True), description (optional), auto_init (creates initial commit/README, default True).
    Returns the new repo's URL on success."""
    return git.call("create_repo", name=name, private=private, description=description, auto_init=auto_init)

@mcp.tool()
def git_update_repo_settings(repo: str, new_name: str = None, private: bool = None, description: str = None):
    """Rename a repo and/or change its visibility/description. Only the fields you pass are changed.
    Args: repo (current name), new_name (optional new name), private (optional True/False), description (optional).
    Use this to archive old/unused repos: rename to something clear like 'archived-<name>' and set private=True.
    NOTE: GitHub keeps redirects for renamed repos, but any hardcoded URL referencing the old name (e.g. in a
    deploy config) will need manual updating. Confirm with the user before renaming a repo that's actively deployed."""
    return git.call("update_repo_settings", repo=repo, new_name=new_name, private=private, description=description)

@mcp.tool()
def list_github_files(repo: str = "niplex-mcp", path: str = ""):
    """List files and folders at a path in a GitHub repo.
    Args: repo (repo name, defaults to 'niplex-mcp'), path (folder path, empty string = repo root).
    Returns file/folder names, one per line. Use before read_github_file to discover what exists."""
    return git.call("list_files", repo=repo, path=path)

@mcp.tool()
def read_github_file(repo: str, file_path: str):
    """Read the full text content of a file in a GitHub repo.
    Args: repo (repo name), file_path (full path from repo root, e.g. 'server.py' or 'src/main.py').
    Always call this before write_github_file to see current content and avoid overwriting unrelated changes."""
    return git.call("read_file", repo=repo, file_path=file_path)

@mcp.tool()
def write_github_file(repo: str, file_path: str, content: str, commit_message: str = "Update file via NIPLEX-MCP", branch: str = None):
    """Create or overwrite a file in a GitHub repo with a real commit.
    Args: repo (repo name), file_path (full path from repo root), content (complete new file content — this REPLACES the whole file, not a patch), commit_message (describe what and why), branch (optional, defaults to the repo's default branch).
    This triggers Horizon auto-deploy if the repo is niplex-mcp and branch is main/unset. Always read_github_file first."""
    return git.call("write_file", repo=repo, file_path=file_path, content=content, commit_message=commit_message, branch=branch)

@mcp.tool()
def git_create_branch(repo: str, branch_name: str, from_branch: str = "main"):
    """Create a new branch in a GitHub repo.
    Args: repo, branch_name (new branch name), from_branch (source branch, default 'main').
    Use this before making risky changes so they can be reviewed via a PR before merging to main."""
    return git.call("create_branch", repo=repo, branch_name=branch_name, from_branch=from_branch)

@mcp.tool()
def git_list_branches(repo: str = "niplex-mcp"):
    """List all branches in a GitHub repo. Args: repo (default 'niplex-mcp'). Returns branch names, one per line."""
    return git.call("list_branches", repo=repo)

@mcp.tool()
def git_list_commits(repo: str = "niplex-mcp", branch: str = "main", limit: int = 10):
    """List recent commits on a branch. Args: repo, branch (default 'main'), limit (max results, default 10).
    Returns short SHA, message, and author per line — useful for seeing recent history before making changes."""
    return git.call("list_commits", repo=repo, branch=branch, limit=limit)

@mcp.tool()
def git_get_commit(repo: str, sha: str):
    """Get full details of one specific commit: message and list of changed files with add/delete line counts.
    Args: repo, sha (commit hash, full or short — get one from git_list_commits)."""
    return git.call("get_commit", repo=repo, sha=sha)

@mcp.tool()
def git_create_issue(repo: str, title: str, body: str = "", labels: list = None):
    """Create a GitHub issue. Args: repo, title, body (optional description), labels (optional list of label name strings).
    Returns the new issue's URL."""
    return git.call("create_issue", repo=repo, title=title, body=body, labels=labels)

@mcp.tool()
def git_list_issues(repo: str = "niplex-mcp", state: str = "open"):
    """List issues in a repo. Args: repo, state ('open', 'closed', or 'all'). Returns issue number, title, and state per line."""
    return git.call("list_issues", repo=repo, state=state)

@mcp.tool()
def git_add_issue_comment(repo: str, issue_number: int, comment: str):
    """Add a comment to an existing GitHub issue. Args: repo, issue_number, comment (text to post)."""
    return git.call("add_issue_comment", repo=repo, issue_number=issue_number, comment=comment)

@mcp.tool()
def git_create_pull_request(repo: str, title: str, head: str, base: str = "main", body: str = ""):
    """Open a pull request. Args: repo, title, head (source branch with your changes), base (target branch, default 'main'), body (optional description).
    NOTE: there is no merge_pull_request tool — merging is deliberately left to manual review. Returns the new PR's URL."""
    return git.call("create_pull_request", repo=repo, title=title, head=head, base=base, body=body)

@mcp.tool()
def git_list_pull_requests(repo: str = "niplex-mcp", state: str = "open"):
    """List pull requests in a repo. Args: repo, state ('open', 'closed', or 'all'). Returns PR number, title, and branch info per line."""
    return git.call("list_pull_requests", repo=repo, state=state)

# ==================== SANDBOXES (code execution) ====================

@mcp.tool()
def execute_in_sandbox(cmd: str, ttl: int = 0):
    """Run a shell command in a disposable Daytona cloud sandbox. Best for longer-running or multi-step tasks that need to persist briefly.
    Args: cmd (shell command string), ttl (minutes to keep the sandbox alive after the command; 0 = destroy immediately after running, default 0).
    Returns stdout/stderr. Each call with ttl=0 is a fresh, isolated environment — no state carries over between calls."""
    return sandbox.call("execute_in_sandbox", cmd=cmd, ttl=ttl)

@mcp.tool()
def destroy_sandbox(id: str):
    """Manually kill a Daytona sandbox that was kept alive with ttl > 0. Args: id (sandbox ID returned by execute_in_sandbox)."""
    return sandbox.call("destroy_sandbox", id=id)

@mcp.tool()
def e2b_run_code(code: str, language: str = "python"):
    """Run code in a short-lived E2B sandbox with real internet access. Good for quick scripts, data processing, or testing snippets.
    Args: code (source code as a string), language (default 'python'; E2B also supports js, ts, r, java, bash).
    Returns execution output/result. Each call is a fresh sandbox, destroyed after running."""
    return sandbox.call("e2b_run_code", code=code, language=language)

@mcp.tool()
def e2b_screenshot():
    """Take a screenshot of a fresh E2B desktop (GUI) sandbox. No arguments. Returns a base64-encoded PNG image string.
    Use this to see what a virtual desktop currently looks like before or after computer-use actions."""
    return sandbox.call("e2b_screenshot")

@mcp.tool()
def e2b_computer_use(actions: list):
    """Perform GUI automation (mouse/keyboard/app launching) in an E2B desktop sandbox — for tasks that need an actual browser or app, not just code.
    Args: actions — a list of action dicts, each with a 'type' key. Supported types:
      {"type": "launch", "app": "<app name>"}
      {"type": "click", "x": <int>, "y": <int>}
      {"type": "write", "text": "<string to type>"}
      {"type": "hotkey", "keys": ["ctrl", "c"]}
      {"type": "wait", "seconds": <int>}
    Actions run in order, in one continuous sandbox session. Returns a base64 screenshot of the final state."""
    return sandbox.call("e2b_computer_use", actions=actions)

@mcp.tool()
def horizon_run_code(code: str, language: str = "python"):
    """Run code in Horizon's own free sandbox (no per-call API cost, unlike Daytona/E2B). Best default choice for quick code execution.
    Args: code (source code string), language (default 'python').
    Returns {"stdout", "stderr", "exit_code", "timed_out"}."""
    return sandbox.call("horizon_run_code", code=code, language=language)

@mcp.tool()
def horizon_health():
    """Check whether the Horizon free sandbox is reachable. No arguments. Returns 'ok' if healthy. Use this to diagnose sandbox connectivity before debugging code issues."""
    return sandbox.call("horizon_health")

# ==================== HIDENCLOUD (SFTP file access) ====================

@mcp.tool()
def list_hidencloud_files(path: str = "/"):
    """List files and folders on the HidenCloud production server via SFTP (no shell access — file listing only).
    Args: path (default '/' = root). This is where the live Niplex/Hermes agent deployment actually runs."""
    return sftp.call("list_files", path=path)

@mcp.tool()
def read_hidencloud_file(path: str):
    """Read a file's text content from the HidenCloud server via SFTP. Args: path (full file path).
    CAUTION: do not read '.env.txt' or similar credential files unless the user explicitly asks — it contains real secrets."""
    return sftp.call("read_file", path=path)

@mcp.tool()
def write_hidencloud_file(path: str, content: str):
    """Write/overwrite a file on the HidenCloud production server via SFTP. Args: path (full file path), content (complete new file content).
    This is a LIVE deployment — prove code works in a sandbox (horizon_run_code/e2b_run_code) first, then write here. No shell/restart capability exists — only file changes."""
    return sftp.call("write_file", path=path, content=content)

@mcp.tool()
def delete_hidencloud_file(path: str):
    """Permanently delete a file on the HidenCloud server via SFTP. Args: path (full file path). Irreversible — confirm with the user before calling on anything not obviously disposable."""
    return sftp.call("delete_file", path=path)

# ==================== SEARCH & SCRAPE ====================

@mcp.tool()
def search_web(q: str, m: str = "web"):
    """Broad internet search. Uses the You.com API if YOU_COM_API_KEY is configured (best quality); otherwise falls back to a free DuckDuckGo search via Jina's reader (no key needed).
    Args: q (search query), m (mode, default 'web'). Returns search result titles/URLs/snippets as text.
    Follow up with scrape_website on a specific result URL for full page content."""
    return search.call("search_web", q=q, m=m)

@mcp.tool()
def scrape_website(url: str):
    """Fetch and extract clean, readable text content from a specific webpage URL, via Jina's reader.
    Args: url (must be a full http:// or https:// URL to a public page — private IPs, localhost, and cloud metadata endpoints are blocked for security).
    Best used after search_web to read the full content of a specific result."""
    return search.call("scrape_website", url=url)

# ==================== YOUTUBE ====================

@mcp.tool()
def search_youtube(q: str, res: int = 10):
    """Search YouTube videos via the YouTube Data API. Args: q (search query), res (max results, default 10).
    Returns video titles, IDs, and channel names. Use get_youtube_details with returned IDs for full metadata."""
    return yt.call("search_youtube", q=q, res=res)

@mcp.tool()
def get_youtube_details(ids: list):
    """Get detailed metadata (title, description, stats) for specific YouTube videos.
    Args: ids — a list of video ID strings (get these from search_youtube results)."""
    return yt.call("get_video_details", ids=ids)

@mcp.tool()
def get_youtube_stats(ids: list):
    """Get statistics (subscriber count, view count, etc.) for specific YouTube channels.
    Args: ids — a list of channel ID strings."""
    return yt.call("get_channel_stats", ids=ids)

# ==================== MISC ====================

@mcp.tool()
def niplex_helper(q: str):
    """Generic echo/test utility — returns the input prefixed with 'NIPLEX Helper:'. Args: q (any string).
    Useful only for confirming the MCP connection itself is alive; has no real functionality."""
    return misc.call("helper", q=q)

# ==================== NEURAL (sub-agent layer -> Adarshs-Stack) ====================
# ask_neural / log_to_neural forward to a SEPARATE deployed MCP server
# (Neural-MCP, github.com/Aj-Niplex/Neural) which runs its own sub-agent
# (Agnes AI) against Adarshs-Stack. Requires NEURAL_MCP_URL and
# NEURAL_MCP_API_KEY to be configured here in Niplex-MCP's environment,
# matching Neural-MCP's own deployed URL and its NEURAL_MCP_API_KEY.

@mcp.tool()
def ask_neural(query: str):
    """Ask Neural (a sub-agent with its own memory search) about Adarsh — his projects, decisions,
    work history, or personal context stored in Adarshs-Stack. Forwards the query to a separate
    Neural-MCP server. If nothing relevant is stored, Neural says so rather than guessing.
    Args: query (a natural-language question, e.g. 'what did Adarsh work on with Claude this week')."""
    return neural.call("ask", query=query)

@mcp.tool()
def log_to_neural(summary: str):
    """Record new information for Neural to file into Adarshs-Stack. Neural decides WHERE it belongs
    (an existing wiki topic page, the inbox if uncertain, a session log, a plan, or a USER.md fact)
    rather than it always landing in one place. Use this to make something durable/findable later.
    Args: summary (a concise description of what happened or what should be remembered)."""
    return neural.call("log", summary=summary)

# ==================== GOOGLE WORKSPACE ====================
# Every tool below requires account="professional" or account="personal".
#   professional = adarsh.jaiswal.2112.aj@gmail.com
#   personal     = aj.jin.japan.2006@gmail.com
# There is no company account configured yet, and no direct-send email tool
# by design — gmail_create_draft is the only way to compose email; it
# creates a draft for manual human review and does NOT send anything.

@mcp.tool()
def gmail_search(account: str, query: str, max_results: int = 10):
    """Search Gmail messages. Args: account ('professional' or 'personal'), query (Gmail search syntax, e.g. 'from:someone in:inbox'), max_results (default 10).
    Returns message ID, date, sender, and subject per line. Use gmail_get_thread with a message/thread ID for full content."""
    return google.call("search_emails", account=account, query=query, max_results=max_results)

@mcp.tool()
def gmail_get_thread(account: str, thread_id: str):
    """Read the full content of an email thread. Args: account, thread_id (from gmail_search results). Returns all messages in the thread with headers and body text."""
    return google.call("get_thread_details", account=account, thread_id=thread_id)

@mcp.tool()
def gmail_create_draft(account: str, to: str, subject: str, body: str):
    """Create a Gmail draft for manual review — this does NOT send the email. Args: account, to (recipient email), subject, body (plain text).
    This is the only way to compose email via this MCP; there is intentionally no send tool. The user must open Gmail and send it themselves."""
    return google.call("create_draft", account=account, to=to, subject=subject, body=body)

@mcp.tool()
def calendar_list_events(account: str, time_min: str = None, time_max: str = None, max_results: int = 10):
    """List upcoming Google Calendar events. Args: account, time_min (optional ISO datetime, defaults to now), time_max (optional ISO datetime), max_results (default 10).
    Returns event ID, start time, and title per line."""
    return google.call("list_events", account=account, time_min=time_min, time_max=time_max, max_results=max_results)

@mcp.tool()
def calendar_create_event(account: str, summary: str, start_time: str, end_time: str, description: str = "", attendees: list = None):
    """Create a new Google Calendar event. Args: account, summary (event title), start_time/end_time (ISO 8601 datetime strings), description (optional), attendees (optional list of email address strings — sends them invites).
    Returns a link to the created event."""
    return google.call("create_event", account=account, summary=summary, start_time=start_time, end_time=end_time, description=description, attendees=attendees)

@mcp.tool()
def calendar_update_event(account: str, event_id: str, summary: str = None, start_time: str = None, end_time: str = None, status: str = None):
    """Update or cancel an existing Calendar event. Args: account, event_id (from calendar_list_events), summary/start_time/end_time (optional — only changes what's provided), status='cancelled' to delete the event entirely.
    Confirm with the user before cancelling an event that has attendees."""
    return google.call("update_event", account=account, event_id=event_id, summary=summary, start_time=start_time, end_time=end_time, status=status)

@mcp.tool()
def drive_search_files(account: str, query: str, max_results: int = 10):
    """Search Google Drive by filename. Args: account, query (text to match in file names), max_results (default 10).
    Returns file ID, name, MIME type, and last modified date per line."""
    return google.call("search_files", account=account, query=query, max_results=max_results)

@mcp.tool()
def docs_read(account: str, doc_id: str):
    """Read the full text content of a Google Doc. Args: account, doc_id (from drive_search_files results, or from a Docs URL)."""
    return google.call("read_doc", account=account, doc_id=doc_id)

@mcp.tool()
def docs_create(account: str, title: str, content: str = ""):
    """Create a new Google Doc. Args: account, title, content (optional initial text). Returns a link to the created doc."""
    return google.call("create_doc", account=account, title=title, content=content)

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=7860)
