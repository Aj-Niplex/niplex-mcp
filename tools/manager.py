from integrations.github import GithubBridge
from integrations.daytona import DaytonaBridge
from integrations.core_bridges import WebScraperBridge, YouComBridge, CacheService
from integrations.youtube import YoutubeBridge
from integrations.hidencloud_sftp import HidenCloudSFTPBridge
from integrations.e2b_bridge import E2BBridge
import os

class MCPTools:
    def __init__(self):
        self.github = GithubBridge(user="Aj-Niplex", repo="niplex-mcp")
        self.daytona = DaytonaBridge(api_key=os.getenv('DAYTONA_API_KEY'))
        self.scraper = WebScraperBridge()
        self.you_com = YouComBridge()
        self.youtube = YoutubeBridge()
        self.hidencloud = HidenCloudSFTPBridge()
        self.e2b = E2BBridge()
        self.cache = CacheService()
        self.cache.connect()

    def list_files(self, path=""): return self.github.list_files(path)
    def read_file(self, file_path): return self.github.read_file(file_path)
    def write_file(self, path, content, msg="Update"): return self.github.write_file(path, content, msg)
    def run_sandbox(self, cmd, ttl=0): return self.daytona.execute_command(cmd, ttl)
    def destroy_sandbox(self, id): return self.daytona.delete_sandbox(id)
    def scrape_web(self, url): return self.scraper.scrape(url)
    def search_web(self, q, m='web'): return self.you_com.search(q, m)
    def search_youtube(self, q, res=10): return self.youtube.search_videos(q, res)
    def get_yt_details(self, ids): return self.youtube.get_video_details(ids)
    def get_yt_stats(self, ids): return self.youtube.get_channel_stats(ids)
    def helper(self, q): return f"NIPLEX Helper: {q}"

    def list_hidencloud_files(self, path="/"): return self.hidencloud.list_files(path)
    def read_hidencloud_file(self, path): return self.hidencloud.read_file(path)
    def write_hidencloud_file(self, path, content): return self.hidencloud.write_file(path, content)
    def delete_hidencloud_file(self, path): return self.hidencloud.delete_file(path)

    def e2b_run_code(self, code, language="python"): return self.e2b.run_code(code, language)
    def e2b_screenshot(self): return self.e2b.desktop_screenshot()
    def e2b_computer_use(self, actions): return self.e2b.desktop_run_actions(actions)

    # ---------- git_* namespace (new GitHub tools) ----------
    def git_create_branch(self, branch_name, from_branch="main"): return self.github.create_branch(branch_name, from_branch)
    def git_list_branches(self): return self.github.list_branches()
    def git_list_commits(self, branch="main", limit=10): return self.github.list_commits(branch, limit)
    def git_get_commit(self, sha): return self.github.get_commit(sha)
    def git_create_issue(self, title, body="", labels=None): return self.github.create_issue(title, body, labels)
    def git_list_issues(self, state="open"): return self.github.list_issues(state)
    def git_add_issue_comment(self, issue_number, comment): return self.github.add_issue_comment(issue_number, comment)
    def git_create_pull_request(self, title, head, base="main", body=""): return self.github.create_pull_request(title, head, base, body)
    def git_list_pull_requests(self, state="open"): return self.github.list_pull_requests(state)
