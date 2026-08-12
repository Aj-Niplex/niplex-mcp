from integrations.google_bridge import GoogleWorkspaceBridge


class GoogleManager:
    """
    Gmail (read + draft only, NOT direct send), Calendar, Drive/Docs —
    across 2 accounts: professional, personal. (A third "company" account
    was deliberately deferred — see integrations/google_bridge.py.)

    send_email exists in the bridge but is intentionally NOT exposed here.
    create_draft is the default path for anything AI-composed.
    """

    def __init__(self):
        self._bridges = {}

    def _get_bridge(self, account: str):
        if account not in self._bridges:
            self._bridges[account] = GoogleWorkspaceBridge(account=account)
        return self._bridges[account]

    def describe(self):
        return {
            "namespace": "google",
            "description": "Gmail (search/read/draft — no direct send), Calendar, Drive & Docs. Every tool needs account='professional'|'personal'.",
            "tools": {
                "search_emails": "Search Gmail. Args: account, query, max_results (default 10).",
                "get_thread_details": "Read full email thread content. Args: account, thread_id.",
                "create_draft": "Create a Gmail draft for manual review (does NOT send). Args: account, to, subject, body.",
                "list_events": "List upcoming Calendar events. Args: account, time_min (optional ISO), time_max (optional ISO), max_results (default 10).",
                "create_event": "Create a Calendar event. Args: account, summary, start_time (ISO), end_time (ISO), description (optional), attendees (optional list of emails).",
                "update_event": "Update or cancel a Calendar event. Args: account, event_id, summary/start_time/end_time (optional), status='cancelled' to cancel.",
                "search_files": "Search Drive by filename. Args: account, query, max_results (default 10).",
                "read_doc": "Read a Google Doc's text content. Args: account, doc_id.",
                "create_doc": "Create a new Google Doc. Args: account, title, content (optional).",
            }
        }

    # Explicit allowlist — only these 9 methods are reachable from a tool
    # call, matching exactly what's documented in describe() above.
    # (Previously everything past the send_email check used
    # getattr(bridge, tool), meaning any public method on
    # GoogleWorkspaceBridge was callable this way — the send_email block
    # below only existed because of that gap. Now new bridge methods stay
    # unreachable until explicitly added here, no case-by-case blocklisting
    # required.)
    _ALLOWED_TOOLS = {
        "search_emails", "get_thread_details", "create_draft",
        "list_events", "create_event", "update_event",
        "search_files", "read_doc", "create_doc",
    }

    def call(self, tool: str, account: str = None, **kwargs):
        if tool == "send_email":
            return "Unknown or disabled google tool: send_email (intentionally not available — use create_draft instead)"
        if tool not in self._ALLOWED_TOOLS:
            return f"Unknown google tool: {tool}"
        if account is None:
            return "Missing required 'account' argument: must be 'professional' or 'personal'."
        try:
            bridge = self._get_bridge(account)
        except ValueError as e:
            return str(e)
        method = getattr(bridge, tool)
        return method(**kwargs)
