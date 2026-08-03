class MiscManager:
    """Small standalone utilities that don't warrant their own namespace yet."""

    def describe(self):
        return {
            "namespace": "misc",
            "description": "Miscellaneous small utilities.",
            "tools": {
                "helper": "Generic echo/helper tool. Args: q.",
            }
        }

    def call(self, tool: str, **kwargs):
        if tool == "helper":
            return f"NIPLEX Helper: {kwargs.get('q')}"
        return f"Unknown misc tool: {tool}"
