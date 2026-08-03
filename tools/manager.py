from tools.managers.git_manager import GitManager
from tools.managers.sandbox_manager import SandboxManager
from tools.managers.sftp_manager import SftpManager
from tools.managers.search_manager import SearchManager
from tools.managers.youtube_manager import YoutubeManager
from tools.managers.misc_manager import MiscManager
from tools.managers.google_manager import GoogleManager


class Router:
    """
    Thin orchestrator. Does not contain business logic itself — every real
    operation lives in a specialist manager (tools/managers/*.py), each
    owning one domain (git, sandbox, sftp, search, yt, misc, google).

    Exposes exactly two entry points to the outside world:
      - list_namespaces(): what domains/tools exist, without loading them all
      - call_tool(namespace, tool, **kwargs): dispatch to the right specialist

    This keeps the tool schema small regardless of how many total tools
    exist underneath, and keeps each domain's logic isolated so nothing
    outside e.g. git_manager.py needs to know how GitHub auth works.
    """

    def __init__(self):
        self._managers = {}
        self._factories = {
            "git": GitManager,
            "sandbox": SandboxManager,
            "sftp": SftpManager,
            "search": SearchManager,
            "yt": YoutubeManager,
            "misc": MiscManager,
            "google": GoogleManager,
        }

    def _get_manager(self, namespace: str):
        if namespace not in self._managers:
            factory = self._factories.get(namespace)
            if factory is None:
                return None
            self._managers[namespace] = factory()
        return self._managers[namespace]

    def list_namespaces(self, namespace: str = None):
        """
        No args: list all namespaces with a short description (cheap, no
        specialist manager is instantiated for this).
        With a namespace: return that namespace's full tool list + arg docs
        (this DOES instantiate that one specialist manager).
        """
        if namespace is None:
            return {
                "git": "GitHub operations (files, branches, commits, issues, PRs) across all your repos.",
                "sandbox": "Code execution: Daytona (long-run) + E2B (short-run, computer use).",
                "sftp": "HidenCloud server file operations via SFTP (no shell access).",
                "search": "Broad web search + targeted webpage scraping/extraction.",
                "yt": "YouTube search and metadata via the YouTube Data API.",
                "misc": "Small standalone utilities.",
                "google": "Gmail (search/read/draft, no direct send), Calendar, Drive & Docs.",
            }
        mgr = self._get_manager(namespace)
        if mgr is None:
            return f"Unknown namespace: {namespace}. Call list_namespaces() with no args to see available namespaces."
        return mgr.describe()

    def call_tool(self, namespace: str, tool: str, **kwargs):
        mgr = self._get_manager(namespace)
        if mgr is None:
            return f"Unknown namespace: {namespace}. Call list_namespaces() with no args to see available namespaces."
        return mgr.call(tool, **kwargs)
