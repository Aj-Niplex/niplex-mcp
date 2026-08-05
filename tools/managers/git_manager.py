from integrations.github import GithubBridge


class GitManager:
    """Owns all GitHub operations across ALL repos under the account."""

    def __init__(self):
        self.github = GithubBridge(user="Aj-Niplex")

    def describe(self):
        return {
            "namespace": "git",
            "description": "GitHub repository, file, branch, commit, issue, and PR operations across all your repos.",
            "tools": {
                "list_repos": "List all repositories under your account.",
                "create_repo": "Create a new repository. Args: name, private (default True), description (optional), auto_init (default True).",
                "list_files": "List files/dirs in a repo path. Args: repo (default 'niplex-mcp'), path (default '').",
                "read_file": "Read a file's content. Args: repo, file_path.",
                "write_file": "Create/update a file with a commit. Args: repo, file_path, content, commit_message, branch (optional).",
                "create_branch": "Create a new branch. Args: repo, branch_name, from_branch (default 'main').",
                "list_branches": "List branches in a repo. Args: repo (default 'niplex-mcp').",
                "list_commits": "List recent commits. Args: repo, branch (default 'main'), limit (default 10).",
                "get_commit": "Get details of a specific commit. Args: repo, sha.",
                "create_issue": "Create an issue. Args: repo, title, body (optional), labels (optional list).",
                "list_issues": "List issues. Args: repo, state (default 'open').",
                "add_issue_comment": "Comment on an issue. Args: repo, issue_number, comment.",
                "create_pull_request": "Create a PR. Args: repo, title, head, base (default 'main'), body (optional).",
                "list_pull_requests": "List PRs. Args: repo, state (default 'open').",
            }
        }

    def call(self, tool: str, **kwargs):
        method = getattr(self.github, tool, None)
        if method is None:
            return f"Unknown git tool: {tool}"
        return method(**kwargs)
