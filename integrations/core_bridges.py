import os
import requests
import json
from typing import Any

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
        # If a real You.com API key is set, use the official API (best quality).
        # Otherwise fall back to a free, keyless broad search.
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
        '''
        Free-tier broad search, no API key needed.

        NOTE: You.com's own search page requires a signed-in session and
        returns nothing useful (login wall) for anonymous scraping — this is
        a deliberate gate on their end. s.jina.ai (Jina's own search
        endpoint) also now requires an API key.

        So the free path goes through DuckDuckGo's server-rendered HTML
        endpoint via Jina's reader (r.jina.ai) — no login wall, no JS
        rendering needed, works reliably keyless. This plays the "broad
        search" role; use scrape_website (Jina reader) on any of the
        resulting URLs afterwards to pull full clean content from a specific
        page.
        '''
        try:
            import urllib.parse
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

    def scrape(self, url):
        return requests.get("https://r.jina.ai/" + url, timeout=30).text
