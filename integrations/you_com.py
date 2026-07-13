import requests
import os
import json

class YouComBridge:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('YOU_COM_API_KEY')
        self.base_url = 'https://api.you.com/v1/search'

    def search(self, query, mode='web'):
        '''
        Perform a search using You.com API.
        mode: 'web' for fast search, 'research' for deep agentic synthesis.
        '''
        if not self.api_key:
            return 'Error: YOU_COM_API_KEY not configured.'

        headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'query': query,
            'search_type': mode
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'answer' in data:
                return data['answer']
            elif 'results' in data:
                return json.dumps(data['results'], indent=2)
            else:
                return json.dumps(data, indent=2)
                
        except requests.exceptions.RequestException as e:
            return f'You.com API Error: {str(e)}'
