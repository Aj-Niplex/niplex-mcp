from integrations.google_bridge import GoogleWorkspaceBridge


class GoogleManager:
    """
    Gmail (read + draft only, NOT direct send), Calendar, Drive/Docs.

    send_email exists in the bridge but is intentionally NOT exposed here.
    create_draft is the default path for anything AI-composed — this
    matches the project's APPROVAL_MODE=off caution: an autonomous agent
    should not be able to directly send email without a human review step.
    """

    def __init__(self):
        self.google = GoogleWorkspaceBridge()

    def describe(self):
        return {
            "namespace": "google",
            "description": "Gmail (search/read/draft — no direct send), Calendar, Drive & Docs.",
            "tools": {
                "search_emails": "Search Gmail. Args: query (Gmail search syntax), max_results (default 10).",
                "get_thread_details": "Read full email thread content. Args: thread_id.",
                "create_draft": "Create a Gmail draft for manual review (does NOT send). Args: to, subject, body.",
                "list_events": "List upcoming Calendar events. Args: time_min (optional ISO), time_max (optional ISO), max_results (default 10).",
                "create_event": "Create a Calendar event. Args: summary, start_time (ISO), end_time (ISO), description (optional), attendees (optional list of emails).",
                "update_event": "Update or cancel a Calendar event. Args: event_id, summary/start_time/end_time (optional), status='cancelled' to cancel.",
                "search_files": "Search Drive by filename. Args: query, max_results (default 10).",
                "read_doc": "Read a Google Doc's text content. Args: doc_id.",
                "create_doc": "Create a new Google Doc. Args: title, content (optional).",
            }
        }

    def call(self, tool: str, **kwargs):
        method = getattr(self.google, tool, None)
        if method is None or tool == "send_email":
            return f"Unknown or disabled google tool: {tool} (send_email is intentionally not available — use create_draft instead)"
        return method(**kwargs)
