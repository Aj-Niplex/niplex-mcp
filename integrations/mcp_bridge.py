# DEPRECATED — not wired to any tool.
#
# This early design called other MCP servers with NO authentication at
# all, over plain hardcoded internal URLs (e.g. http://youtube-mcp:7860).
# The current, safe way to call another one of our own MCP servers is
# the pattern in integrations/horizon_sandbox.py: fastmcp.Client(url,
# auth=<token>). Left inert on purpose — raises immediately if anything
# tries to use it — so nothing can silently reconnect this and start
# making unauthenticated calls without anyone noticing.

class MCPClientBridge:
    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "MCPClientBridge is deprecated and sends requests with no "
            "authentication — do not use. See integrations/horizon_sandbox.py "
            "for the current, authenticated pattern for calling another MCP server."
        )
