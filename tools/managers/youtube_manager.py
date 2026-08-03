from integrations.youtube import YoutubeBridge


class YoutubeManager:
    """Owns YouTube Data API operations."""

    def __init__(self):
        self.youtube = YoutubeBridge()

    def describe(self):
        return {
            "namespace": "yt",
            "description": "YouTube search and metadata lookups via the YouTube Data API.",
            "tools": {
                "search_youtube": "Search YouTube videos. Args: q, res (max results, default 10).",
                "get_video_details": "Get details for video IDs. Args: ids (list of video ID strings).",
                "get_channel_stats": "Get stats for channel IDs. Args: ids (list of channel ID strings).",
            }
        }

    def call(self, tool: str, **kwargs):
        if tool == "search_youtube":
            return self.youtube.search_videos(kwargs.get("q"), kwargs.get("res", 10))
        if tool == "get_video_details":
            return self.youtube.get_video_details(kwargs.get("ids"))
        if tool == "get_channel_stats":
            return self.youtube.get_channel_stats(kwargs.get("ids"))
        return f"Unknown yt tool: {tool}"
