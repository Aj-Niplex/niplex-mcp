import os
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
    def __init__(self):
        self.connection_string = os.getenv('MDB_MCP_CONNECTION_STRING')
        self.client = None

    def connect(self):
        if not self.connection_string:
            return False
        try:
            from pymongo import MongoClient
            self.client = MongoClient(self.connection_string)
            return True
        except ImportError:
            return False
        except Exception:
            return False

    def get(self, key):
        if not self.client: return None
        try:
            db = self.client['mcp_cache']
            return db.cache.find_one({"_id": key})['value']
        except: return None

    def set(self, key, value):
        if not self.client: return
        try:
            db = self.client['mcp_cache']
            db.cache.update_one({"_id": key}, {"$set": {"value": value}}, upsert=True)
        except: pass

class YouComBridge:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('YOU_COM_API_KEY')
        self.base_url = 'https://api.you.com/v1/search'

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
            return f'Free Search Error: {str(e)}'

class WebScraperBridge:
    def __init__(self):
        self.api_key = os.getenv('SCRAPER_API_KEY', 'mock_key')

    def scrape(self, url: str) -> str:
        if not _is_safe_url(url):
            return f"Error: URL '{url}' is not allowed — must be a public http/https URL (no internal/private hosts)."
        jina_url = "https://r.jina.ai/" + url
        return requests.get(jina_url, timeout=30).text
