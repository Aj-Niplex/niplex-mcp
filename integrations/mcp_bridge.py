import requests
import json
import os

class MCPClientBridge:
    def __init__(self):
        # Store registered servers to avoid passing URL every time
        self.servers = {
            "youtube": os.getenv('YOUTUBE_MCP_URL', 'http://youtube-mcp:7860'),
            "neural_os": os.getenv('NEURAL_OS_MCP_URL', 'http://neural-os-mcp:7860'),
        }

    def call_tool(self, server_key, tool_name, arguments):
        '''
        Calls a tool on a remote MCP server.
        server_key: Key from self.servers or a direct URL.
        '''
        url = self.servers.get(server_key, server_key)
        
        if not url.startswith('http'):
            return 'Error: Invalid server URL ' + str(url)

        # Standard MCP JSON-RPC over HTTP payload
        payload = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'tools/call',
            'params': {
                'name': tool_name,
                'arguments': arguments
            }
        }

        try:
            response = requests.post(url + '/call', json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                return 'Remote MCP Error: ' + str(result['error'])
            
            return json.dumps(result.get('result', {}), indent=2)
            
        except requests.exceptions.RequestException as e:
            return 'MCP Connection Error (' + str(server_key) + '): ' + str(e)

    def register_server(self, key, url):
        self.servers[key] = url
        return 'Server ' + str(key) + ' registered at ' + str(url)
