from importlib.metadata import version, PackageNotFoundError
from integrations.core_bridges import CacheService


class MiscManager:
    """Small standalone utilities that don't warrant their own namespace yet."""

    TRACKED_PACKAGES = [
        "fastmcp", "requests", "daytona", "pymongo", "paramiko",
        "e2b-code-interpreter", "e2b-desktop",
        "google-auth", "google-auth-oauthlib", "google-api-python-client",
    ]

    def __init__(self):
        self._cache = None  # lazy — only connect when actually needed

    def _get_cache(self):
        if self._cache is None:
            self._cache = CacheService()
            self._cache.connect()
        return self._cache

    def describe(self):
        return {
            "namespace": "misc",
            "description": "Miscellaneous small utilities.",
            "tools": {
                "helper": "Generic echo/helper tool. Args: q.",
                "versions": "Report exact installed versions of every package in requirements.txt, as actually running right now. Use before pinning requirements.txt so pins match reality instead of guessing.",
                "recent_errors": "Read back recent errors logged by search_web/scrape_website (and anything else wired to CacheService.log_error). Requires MDB_MCP_CONNECTION_STRING to be configured. Args: limit (default 20).",
            }
        }

    def call(self, tool: str, **kwargs):
        if tool == "helper":
            return f"NIPLEX Helper: {kwargs.get('q')}"
        if tool == "versions":
            return self._versions()
        if tool == "recent_errors":
            return self._get_cache().get_recent_errors(limit=kwargs.get("limit", 20))
        return f"Unknown misc tool: {tool}"

    def _versions(self) -> str:
        lines = []
        for pkg in self.TRACKED_PACKAGES:
            try:
                lines.append(f"{pkg}=={version(pkg)}")
            except PackageNotFoundError:
                lines.append(f"{pkg}: NOT FOUND (checked as installed under this name)")
        return "\n".join(lines)
