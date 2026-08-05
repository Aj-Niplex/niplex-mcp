import os
import json
import base64
from email.mime.text import MIMEText


class GoogleWorkspaceBridge:
    """
    Gmail + Calendar + Drive/Docs, multi-account.

    Each account ("professional", "personal", "company") has its own OAuth
    Client (from the same Google Cloud project) and its own token, stored as
    separate env var pairs:
        GOOGLE_<ACCOUNT>_CREDENTIALS_JSON
        GOOGLE_<ACCOUNT>_TOKEN_JSON

    e.g. GOOGLE_PROFESSIONAL_CREDENTIALS_JSON / GOOGLE_PROFESSIONAL_TOKEN_JSON

    NOTE ON FIRST-TIME AUTH: each account needs its own one-time OAuth
    consent (headless server can't open a browser) — done once per account
    via a local/sandbox script, producing that account's token.json content
    for GOOGLE_<ACCOUNT>_TOKEN_JSON. After that, refresh is automatic.
    """

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents",
    ]

    VALID_ACCOUNTS = ("professional", "personal", "company")

    def __init__(self, account: str):
        if account not in self.VALID_ACCOUNTS:
            raise ValueError(f"Unknown account '{account}'. Must be one of {self.VALID_ACCOUNTS}.")
        self.account = account
        prefix = f"GOOGLE_{account.upper()}_"
        self.creds_json = os.environ.get(prefix + "CREDENTIALS_JSON")
        self.token_json = os.environ.get(prefix + "TOKEN_JSON")
        self._creds = None

    def _get_credentials(self):
        if self._creds is not None:
            return self._creds, None
        if not self.creds_json:
            return None, f"GOOGLE_{self.account.upper()}_CREDENTIALS_JSON not configured."
        if not self.token_json:
            return None, f"GOOGLE_{self.account.upper()}_TOKEN_JSON not configured (one-time OAuth not completed yet for '{self.account}')."
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request

            token_data = json.loads(self.token_json)
            creds = Credentials.from_authorized_user_info(token_data, self.SCOPES)

            if creds.expired and creds.refresh_token:
                creds.refresh(Request())

            self._creds = creds
            return creds, None
        except Exception as e:
            return None, f"Google auth error ({self.account}): {str(e)}"

    # ---------- Gmail ----------

    def search_emails(self, query: str, max_results: int = 10) -> str:
        creds, err = self._get_credentials()
        if err:
            return err
        try:
            from googleapiclient.discovery import build
            service = build("gmail", "v1", credentials=creds)
            results = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
            messages = results.get("messages", [])
            if not messages:
                return "No emails found."
            lines = []
            for m in messages:
                msg = service.users().messages().get(userId="me", id=m["id"], format="metadata",
                                                        metadataHeaders=["From", "Subject", "Date"]).execute()
                headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
                lines.append(f"[{m['id']}] {headers.get('Date','')} | {headers.get('From','')} | {headers.get('Subject','(no subject)')}")
            return "\n".join(lines)
        except Exception as e:
            return f"Gmail search error: {str(e)}"

    def get_thread_details(self, thread_id: str) -> str:
        creds, err = self._get_credentials()
        if err:
            return err
        try:
            from googleapiclient.discovery import build
            service = build("gmail", "v1", credentials=creds)
            thread = service.users().threads().get(userId="me", id=thread_id, format="full").execute()
            parts_out = []
            for msg in thread.get("messages", []):
                headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
                body = self._extract_body(msg["payload"])
                parts_out.append(f"From: {headers.get('From','')}\nSubject: {headers.get('Subject','')}\nDate: {headers.get('Date','')}\n\n{body}")
            return "\n\n---\n\n".join(parts_out) if parts_out else "Thread empty or not found."
        except Exception as e:
            return f"Gmail thread error: {str(e)}"

    def _extract_body(self, payload) -> str:
        if payload.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
        return "(no readable body)"

    def create_draft(self, to: str, subject: str, body: str) -> str:
        creds, err = self._get_credentials()
        if err:
            return err
        try:
            from googleapiclient.discovery import build
            service = build("gmail", "v1", credentials=creds)
            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            draft = service.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
            return f"Draft created (id: {draft['id']}) to {to}, subject: {subject}, from account: {self.account}"
        except Exception as e:
            return f"Gmail draft error: {str(e)}"

    def send_email(self, to: str, subject: str, body: str) -> str:
        """
        Direct-send. NOT wired to a tool by default — create_draft is the
        default path for anything AI-composed.
        """
        creds, err = self._get_credentials()
        if err:
            return err
        try:
            from googleapiclient.discovery import build
            service = build("gmail", "v1", credentials=creds)
            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
            return f"Email sent (id: {sent['id']}) to {to}, subject: {subject}, from account: {self.account}"
        except Exception as e:
            return f"Gmail send error: {str(e)}"

    # ---------- Calendar ----------

    def list_events(self, time_min: str = None, time_max: str = None, max_results: int = 10) -> str:
        creds, err = self._get_credentials()
        if err:
            return err
        try:
            from googleapiclient.discovery import build
            import datetime
            service = build("calendar", "v3", credentials=creds)
            if not time_min:
                time_min = datetime.datetime.utcnow().isoformat() + "Z"
            events_result = service.events().list(
                calendarId="primary", timeMin=time_min, timeMax=time_max,
                maxResults=max_results, singleEvents=True, orderBy="startTime"
            ).execute()
            events = events_result.get("items", [])
            if not events:
                return "No upcoming events found."
            lines = []
            for e in events:
                start = e["start"].get("dateTime", e["start"].get("date"))
                lines.append(f"[{e['id']}] {start} - {e.get('summary', '(no title)')}")
            return "\n".join(lines)
        except Exception as e:
            return f"Calendar list error: {str(e)}"

    def create_event(self, summary: str, start_time: str, end_time: str, description: str = "", attendees: list = None) -> str:
        creds, err = self._get_credentials()
        if err:
            return err
        try:
            from googleapiclient.discovery import build
            service = build("calendar", "v3", credentials=creds)
            event_body = {
                "summary": summary,
                "description": description,
                "start": {"dateTime": start_time},
                "end": {"dateTime": end_time},
            }
            if attendees:
                event_body["attendees"] = [{"email": a} for a in attendees]
            event = service.events().insert(calendarId="primary", body=event_body).execute()
            return f"Event created: {event.get('htmlLink')}"
        except Exception as e:
            return f"Calendar create error: {str(e)}"

    def update_event(self, event_id: str, summary: str = None, start_time: str = None, end_time: str = None, status: str = None) -> str:
        creds, err = self._get_credentials()
        if err:
            return err
        try:
            from googleapiclient.discovery import build
            service = build("calendar", "v3", credentials=creds)
            event = service.events().get(calendarId="primary", eventId=event_id).execute()
            if summary:
                event["summary"] = summary
            if start_time:
                event["start"]["dateTime"] = start_time
            if end_time:
                event["end"]["dateTime"] = end_time
            if status == "cancelled":
                service.events().delete(calendarId="primary", eventId=event_id).execute()
                return f"Event {event_id} cancelled."
            updated = service.events().update(calendarId="primary", eventId=event_id, body=event).execute()
            return f"Event updated: {updated.get('htmlLink')}"
        except Exception as e:
            return f"Calendar update error: {str(e)}"

    # ---------- Drive & Docs ----------

    def search_files(self, query: str, max_results: int = 10) -> str:
        creds, err = self._get_credentials()
        if err:
            return err
        try:
            from googleapiclient.discovery import build
            service = build("drive", "v3", credentials=creds)
            results = service.files().list(
                q=f"name contains '{query}'", pageSize=max_results,
                fields="files(id, name, mimeType, modifiedTime)"
            ).execute()
            files = results.get("files", [])
            if not files:
                return "No files found."
            lines = [f"[{f['id']}] {f['name']} ({f['mimeType']}) modified {f['modifiedTime']}" for f in files]
            return "\n".join(lines)
        except Exception as e:
            return f"Drive search error: {str(e)}"

    def read_doc(self, doc_id: str) -> str:
        creds, err = self._get_credentials()
        if err:
            return err
        try:
            from googleapiclient.discovery import build
            service = build("docs", "v1", credentials=creds)
            doc = service.documents().get(documentId=doc_id).execute()
            text_parts = []
            for elem in doc.get("body", {}).get("content", []):
                if "paragraph" in elem:
                    for run in elem["paragraph"].get("elements", []):
                        if "textRun" in run:
                            text_parts.append(run["textRun"].get("content", ""))
            return "".join(text_parts) if text_parts else "(empty document)"
        except Exception as e:
            return f"Docs read error: {str(e)}"

    def create_doc(self, title: str, content: str = "") -> str:
        creds, err = self._get_credentials()
        if err:
            return err
        try:
            from googleapiclient.discovery import build
            service = build("docs", "v1", credentials=creds)
            doc = service.documents().create(body={"title": title}).execute()
            doc_id = doc["documentId"]
            if content:
                service.documents().batchUpdate(
                    documentId=doc_id,
                    body={"requests": [{"insertText": {"location": {"index": 1}, "text": content}}]}
                ).execute()
            return f"Doc created: https://docs.google.com/document/d/{doc_id}/edit"
        except Exception as e:
            return f"Docs create error: {str(e)}"
