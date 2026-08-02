from integrations.core_bridges import WebScraperBridge, YouComBridge


class SearchManager:
    """Owns web search (You.com API / free DuckDuckGo fallback) and Jina-based scraping."""

    def __init__(self):
        self.scraper = WebScraperBridge()
        self.you_com = YouComBridge()

    def describe(self):
        return {
            "namespace": "search",
            "description": "Broad web search and targeted webpage scraping/extraction.",
            "tools": {
                "search_web": "Broad internet search. Uses You.com API if YOU_COM_API_KEY is set, else free DuckDuckGo fallback via Jina. Args: q, m (mode, default 'web').",
                "scrape_website": "Extract clean readable content from a specific URL via Jina's reader. Args: url.",
            }
        }

    def call(self, tool: str, **kwargs):
        if tool == "search_web":
            return self.you_com.search(kwargs.get("q"), kwargs.get("m", "web"))
        if tool == "scrape_website":
            return self.scraper.scrape(kwargs.get("url"))
        return f"Unknown search tool: {tool}"
