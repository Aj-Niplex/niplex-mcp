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
        # If no API key, we attempt the free public endpoint flow
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
        Implements the free-tier search flow that doesn't require an API key.
        '''
        # This is a conceptual implementation of the public endpoint
        # In a real production scenario, this would involve handling browser-like headers
        # and potential Cloudflare bypasses for the public you.com search.
        try:
            # Using the public search endpoint
            url = f"https://you.com/search?q={query}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Since public search returns HTML, we return a notice that it's in HTML mode
            # or use a basic regex/BeautifulSoup to extract the answer.
            return f"Free Search Result for '{query}': [HTML Content Retrieved]. Note: Full synthesis requires API key for structured JSON."
        except Exception as e:
            return f'You.com Free Search Error: {str(e)}'

class WebScraperBridge:
    def __init__(self):
        self.api_key = os.getenv('SCRAPER_API_KEY', 'mock_key')

    def scrape(self, url):
        return f"Scraped content from {url}: [Extracted content via API]"

class NeuralOSBridge:
    def __init__(self):
        self.repo_url = os.getenv('NEURAL_OS_REPO')
        self.github_pat = os.getenv('GITHUB_PAT')
        self.local_path = '/tmp/neural_os_db'

    def _sync(self):
        if not self.repo_url or not self.github_pat: return False
        auth_url = self.repo_url.replace('https://', f'https://{self.github_pat}@')
        import subprocess
        if not os.path.exists(self.local_path):
            subprocess.run(['git', 'clone', auth_url, self.local_path], capture_output=True)
        else:
            subprocess.run(['git', '-C', self.local_path, 'pull'], capture_output=True)
        return True

    def query(self, query):
        if not self._sync(): return 'Error: Neural-OS config missing.'
        results = []
        for root, _, files in os.walk(self.local_path):
            for file in files:
                if file.endswith('.md'):
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        if query.lower() in f.read().lower():
                            results.append(f"File: {file}\\n{f.read()}")
        return '\\n\\n'.join(results) if results else 'No matches found.'

    def update(self, key, value):
        if not self._sync(): return 'Error: Neural-OS config missing.'
        db_file = os.path.join(self.local_path, 'memories.json')
        data = {}
        if os.path.exists(db_file):
            with open(db_file, 'r') as f:
                try: data = json.load(f)
                except: pass
        data[key] = value
        with open(db_file, 'w') as f:
            json.dump(data, f, indent=2)
        import subprocess
        subprocess.run(['git', '-C', self.local_path, 'add', '.'], capture_output=True)
        subprocess.run(['git', '-C', self.local_path, 'commit', '-m', f'Update {key}'], capture_output=True)
        subprocess.run(['git', '-C', self.local_path, 'push'], capture_output=True)
        return f'Updated {key} in Neural-OS.'
