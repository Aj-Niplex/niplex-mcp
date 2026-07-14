from integrations.github import GithubBridge
from integrations.daytona import DaytonaBridge
from integrations.core_bridges import NeuralOSBridge, WebScraperBridge, YouComBridge, CacheService
from integrations.youtube import YoutubeBridge
import os

class MCPTools:
    def __init__(self):
        self.github = GithubBridge(user="Aj-Niplex", repo="niplex-mcp")
        self.daytona = DaytonaBridge(api_key=os.getenv('DAYTONA_API_KEY'))
        self.neural_os = NeuralOSBridge()
        self.scraper = WebScraperBridge()
        self.you_com = YouComBridge()
        self.youtube = YoutubeBridge()
        self.cache = CacheService()
        self.cache.connect()

    def list_files(self, path=""): return self.github.list_files(path)
    def read_file(self, file_path): return self.github.read_file(file_path)
    def write_file(self, path, content, msg="Update"): return self.github.write_file(path, content, msg)
    def run_sandbox(self, cmd, ttl=0): return self.daytona.execute_command(cmd, ttl)
    def destroy_sandbox(self, id): return self.daytona.delete_sandbox(id)
    def query_neural_os(self, q): return self.neural_os.query(q)
    def update_neural_os(self, k, v): return self.neural_os.update(k, v)
    def scrape_web(self, url): return self.scraper.scrape(url)
    def search_web(self, q, m='web'): return self.you_com.search(q, m)
    def search_youtube(self, q, res=10): return self.youtube.search_videos(q, res)
    def get_yt_details(self, ids): return self.youtube.get_video_details(ids)
    def get_yt_stats(self, ids): return self.youtube.get_channel_stats(ids)
    def helper(self, q): return f"NIPLEX Helper: {q}"
