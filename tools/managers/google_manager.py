from integrations.google_bridge import GoogleWorkspaceBridge


class GoogleManager:
    """
    Gmail (read + draft only, NOT direct send), Calendar, Drive/Docs —
    across 3 separate accounts: professional, personal, company.

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
            "description": "Gmail (search/read/draft — no direct send), Calendar, Drive & Docs. Every tool needs account='professional'|'personal'|'company'.",
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

    def call(self, tool: str, account: str = None, **kwargs):
        if tool == "send_email":
            return "Unknown or disabled google tool: send_email (intentionally not available — use create_draft instead)"
        if account is None:
            return "Missing required 'account' argument: must be 'professional', 'personal', or 'company'."
        try:
            bridge = self._get_bridge(account)
        except ValueError as e:
            return str(e)
        method = getattr(bridge, tool, None)
        if method is None:
            return f"Unknown google tool: {tool}"
        return method(**kwargs)
