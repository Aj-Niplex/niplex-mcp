import os
import requests
from typing import List, Dict, Any, Optional
import json

class YoutubeBridge:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        self.base_url = 'https://www.googleapis.com/youtube/v3'

    def _make_request(self, endpoint, params):
        params['key'] = self.api_key
        try:
            response = requests.get(self.base_url + endpoint, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

    def _strip_bloat(self, data):
        '''
        Implement Kirbah-style token optimization.
        Strips redundant metadata, eTags, and excessive localization data.
        '''
        if isinstance(data, list):
            return [self._strip_bloat(item) for item in data]
        
        if isinstance(data, dict):
            essential_fields = {
                'snippet': ['title', 'description', 'publishedAt', 'channelTitle', 'thumbnails'],
                'statistics': ['viewCount', 'likeCount', 'commentCount'],
                'contentDetails': ['duration', 'caption'],
                'id': None,
                'channelId': None,
                'title': None,
                'description': None,
            }
            
            filtered = {}
            for key, allowed_values in essential_fields.items():
                if key in data:
                    if allowed_values is None:
                        filtered[key] = data[key]
                    elif isinstance(data[key], dict) and allowed_values:
                        nested = {k: v for k, v in data[key].items() if k in allowed_values}
                        filtered[key] = nested
            
            return filtered
        
        return data

    def search_videos(self, query, max_results=10, order='relevance'):
        params = {
            'q': query,
            'part': 'snippet',
            'maxResults': max_results,
            'order': order,
            'type': 'video'
        }
        res = self._make_request('/search', params)
        if 'error' in res: return res['error']
        
        items = [self._strip_bloat(item) for item in res.get('items', [])]
        return json.dumps(items, indent=2)

    def get_video_details(self, video_ids):
        ids_string = ','.join(video_ids)
        params = {
            'id': ids_string,
            'part': 'snippet,statistics,contentDetails'
        }
        res = self._make_request('/videos', params)
        if 'error' in res: return res['error']
        
        items = [self._strip_bloat(item) for item in res.get('items', [])]
        return json.dumps(items, indent=2)

    def get_channel_stats(self, channel_ids):
        ids_string = ','.join(channel_ids)
        params = {
            'id': ids_string,
            'part': 'snippet,statistics'
        }
        res = self._make_request('/channels', params)
        if 'error' in res: return res['error']
        
        items = [self._strip_bloat(item) for item in res.get('items', [])]
        return json.dumps(items, indent=2)

    def get_transcript(self, video_id):
        try:
            return 'Transcript for ' + str(video_id) + ' requested. [System: Install "youtube-transcript-api" for full access]'
        except Exception as e:
            return 'Transcript Error: ' + str(e)
