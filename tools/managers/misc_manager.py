from importlib.metadata import version, PackageNotFoundError


class MiscManager:
    """Small standalone utilities that don't warrant their own namespace yet."""

    # Maps requirements.txt entries to their actual importable distribution
    # name, where different (e.g. the PyPI package "google-auth" installs
    # as distribution "google-auth" but a couple of these do differ).
    TRACKED_PACKAGES = [
        "fastmcp", "requests", "daytona", "pymongo", "paramiko",
        "e2b-code-interpreter", "e2b-desktop",
        "google-auth", "google-auth-oauthlib", "google-api-python-client",
    ]

    def describe(self):
        return {
            "namespace": "misc",
            "description": "Miscellaneous small utilities.",
            "tools": {
                "helper": "Generic echo/helper tool. Args: q.",
                "versions": "Report exact installed versions of every package in requirements.txt, as actually running right now. Use before pinning requirements.txt so pins match reality instead of guessing.",
            }
        }

    def call(self, tool: str, **kwargs):
        if tool == "helper":
            return f"NIPLEX Helper: {kwargs.get('q')}"
        if tool == "versions":
            return self._versions()
        return f"Unknown misc tool: {tool}"

    def _versions(self) -> str:
        lines = []
        for pkg in self.TRACKED_PACKAGES:
            try:
                lines.append(f"{pkg}=={version(pkg)}")
            except PackageNotFoundError:
                lines.append(f"{pkg}: NOT FOUND (checked as installed under this name)")
        return "\n".join(lines)
