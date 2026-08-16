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
                "update_repo_settings": "Rename/change visibility/description of a repo. Args: repo, new_name (optional), private (optional), description (optional).",
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
        # Explicit allowlist — only these 15 methods are reachable from a
        # tool call, matching exactly what's documented in describe() above.
        # (Previously this used getattr(self.github, tool), which meant
        # ANY public method on GithubBridge was callable this way, not just
        # the ones meant to be exposed — safe today only because every
        # caller happens to be a hardcoded string, but fragile.)
        if tool == "list_repos":
            return self.github.list_repos()
        if tool == "create_repo":
            return self.github.create_repo(**kwargs)
        if tool == "update_repo_settings":
            return self.github.update_repo_settings(**kwargs)
        if tool == "list_files":
            return self.github.list_files(**kwargs)
        if tool == "read_file":
            return self.github.read_file(**kwargs)
        if tool == "write_file":
            return self.github.write_file(**kwargs)
        if tool == "create_branch":
            return self.github.create_branch(**kwargs)
        if tool == "list_branches":
            return self.github.list_branches(**kwargs)
        if tool == "list_commits":
            return self.github.list_commits(**kwargs)
        if tool == "get_commit":
            return self.github.get_commit(**kwargs)
        if tool == "create_issue":
            return self.github.create_issue(**kwargs)
        if tool == "list_issues":
            return self.github.list_issues(**kwargs)
        if tool == "add_issue_comment":
            return self.github.add_issue_comment(**kwargs)
        if tool == "create_pull_request":
            return self.github.create_pull_request(**kwargs)
        if tool == "list_pull_requests":
            return self.github.list_pull_requests(**kwargs)
        return f"Unknown git tool: {tool}"
