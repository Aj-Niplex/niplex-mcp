import os
import time
import requests
import json
from typing import Any
import urllib.parse

BLOCKED_HOSTS = {
    "localhost", "127.0.0.1", "0.0.0.0", "::1",
    "169.254.169.254",  # AWS/GCP metadata
    "metadata.google.internal",
    "metadata.internal",
}

def _is_safe_url(url: str) -> bool:
    """Block private/internal hosts and non-http(s) schemes."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.hostname or ""
        if host in BLOCKED_HOSTS:
            return False
        # Block private IP ranges
        import ipaddress
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
        except ValueError:
            pass  # hostname, not IP — fine
        return True
    except Exception:
        return False

class CacheService:
    """
    Optional cache + error log, both backed by MongoDB. Every method is a
    safe no-op if MDB_MCP_CONNECTION_STRING isn't set, or if the connection
    fails — callers always just get a clean miss/no-op, nothing ever breaks
    because of this.
    """
    def __init__(self):
        self.connection_string = os.getenv('MDB_MCP_CONNECTION_STRING')
        self.client = None
        self.connected = False

    def connect(self):
        if not self.connection_string:
            return False
        try:
            from pymongo import MongoClient
            self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=3000)
            self.client.admin.command('ping')
            self.connected = True
            return True
        except Exception:
            self.client = None
            self.connected = False
            return False

    # ---------- cache ----------

    def get(self, key, max_age_seconds=None):
        if not self.connected:
            return None
        try:
            db = self.client['mcp_cache']
            doc = db.cache.find_one({"_id": key})
            if not doc:
                return None
            if max_age_seconds is not None and (time.time() - doc.get("cached_at", 0)) > max_age_seconds:
                return None  # too old — treat as a miss so it gets refreshed
            return doc['value']
        except Exception:
            return None

    def set(self, key, value):
        if not self.connected:
            return
        try:
            db = self.client['mcp_cache']
            db.cache.update_one(
                {"_id": key},
                {"$set": {"value": value, "cached_at": time.time()}},
                upsert=True,
            )
        except Exception:
            pass

    # ---------- error log ----------
    # A running record of failures across the system, so an error isn't
    # only visible in the one chat response it happened in. Nothing reads
    # this automatically — call get_recent_errors() (exposed as the
    # recent_errors tool) to actually look at it.

    def log_error(self, source: str, error: str, context: dict = None):
        if not self.connected:
            return
        try:
            db = self.client['mcp_cache']
            db.error_log.insert_one({
                "source": source,          # e.g. "scrape_website", "search_web"
                "error": str(error)[:2000],  # capped so one huge traceback can't blow up storage
                "context": context or {},
                "timestamp": time.time(),
            })
        except Exception:
            pass  # logging a failure should never itself cause a failure

    def get_recent_errors(self, limit: int = 20) -> str:
        if not self.connected:
            return "Error log not available — MDB_MCP_CONNECTION_STRING isn't configured."
        try:
            db = self.client['mcp_cache']
            docs = db.error_log.find().sort("timestamp", -1).limit(limit)
            lines = []
            for d in docs:
                ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(d.get("timestamp", 0)))
                lines.append(f"[{ts}] {d.get('source', '?')}: {d.get('error', '?')}")
            return "\n".join(lines) if lines else "No errors logged yet."
        except Exception as e:
            return f"Could not read error log: {str(e)}"

class YouComBridge:
    def __init__(self, api_key=None, cache: "CacheService" = None):
        self.api_key = api_key or os.getenv('YOU_COM_API_KEY')
        self.base_url = 'https://api.you.com/v1/search'
        self.cache = cache  # used for error logging only — search results are NOT cached (need to stay current)

    def search(self, query, mode='web'):
        if not self.api_key:
            return self._free_search(query, mode)
        headers = {'X-API-Key': self.api_key, 'Content-Type': 'application/json'}
        payload = {'query': query, 'search_type': mode}
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('answer', json.dumps(data.get('results', data), indent=2))
        except Exception as e:
            if self.cache:
                self.cache.log_error("search_web", str(e), {"query": query, "mode": mode})
            return f'You.com API Error: {str(e)}'

    def _free_search(self, query, mode):
        try:
            encoded_query = urllib.parse.quote(query)
            ddg_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            jina_url = "https://r.jina.ai/" + ddg_url
            response = requests.get(jina_url, timeout=30)
            response.raise_for_status()
            text = response.text
            return text[:4000] if len(text) > 4000 else text
        except Exception as e:
            if self.cache:
                self.cache.log_error("search_web_free_fallback", str(e), {"query": query, "mode": mode})
            return f'Free Search Error: {str(e)}'

class WebScraperBridge:
    """
    Scrapes a URL via Jina's reader, with SSRF protection. Results are
    cached per-URL for SCRAPE_CACHE_TTL_SECONDS if a CacheService is passed
    in and connected. Failures get logged to the same CacheService's error
    log (if connected) instead of just vanishing once the response is read.
    """
    SCRAPE_CACHE_TTL_SECONDS = 3600  # 1 hour

    def __init__(self, cache: "CacheService" = None):
        self.api_key = os.getenv('SCRAPER_API_KEY', 'mock_key')
        self.cache = cache

    def scrape(self, url: str) -> str:
        if not _is_safe_url(url):
            return f"Error: URL '{url}' is not allowed — must be a public http/https URL (no internal/private hosts)."

        cache_key = f"scrape:{url}"
        if self.cache:
            cached = self.cache.get(cache_key, max_age_seconds=self.SCRAPE_CACHE_TTL_SECONDS)
            if cached is not None:
                return cached

        jina_url = "https://r.jina.ai/" + url
        try:
            response = requests.get(jina_url, timeout=30)
            response.raise_for_status()
            result = response.text
        except Exception as e:
            if self.cache:
                self.cache.log_error("scrape_website", str(e), {"url": url})
            return f"Scrape error: {str(e)}"

        if self.cache:
            self.cache.set(cache_key, result)

        return result
