from integrations.core_bridges import WebScraperBridge, YouComBridge, CacheService


class SearchManager:
    """Owns web search (You.com API / free DuckDuckGo fallback) and Jina-based scraping."""

    def __init__(self):
        cache = CacheService()
        cache.connect()  # safe no-op if MDB_MCP_CONNECTION_STRING isn't set
        self.scraper = WebScraperBridge(cache=cache)
        self.you_com = YouComBridge(cache=cache)  # cache used for error logging only — results aren't cached

    def describe(self):
        return {
            "namespace": "search",
            "description": "Broad web search and targeted webpage scraping/extraction.",
            "tools": {
                "search_web": "Broad internet search. Uses You.com API if YOU_COM_API_KEY is set, else free DuckDuckGo fallback via Jina. Args: q, m (mode, default 'web').",
                "scrape_website": "Extract clean readable content from a specific URL via Jina's reader. Cached for 1 hour per URL if MDB_MCP_CONNECTION_STRING is configured — otherwise behaves exactly as before. Args: url.",
            }
        }

    def call(self, tool: str, **kwargs):
        if tool == "search_web":
            return self.you_com.search(kwargs.get("q"), kwargs.get("m", "web"))
        if tool == "scrape_website":
            return self.scraper.scrape(kwargs.get("url"))
        return f"Unknown search tool: {tool}"
