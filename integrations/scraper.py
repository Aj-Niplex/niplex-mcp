# DEPRECATED — not imported by any active manager.
#
# search_manager.py uses integrations/core_bridges.py's WebScraperBridge,
# which actually checks URLs before fetching them (blocks localhost,
# private IPs, and cloud metadata endpoints like 169.254.169.254). This
# file used to be a separate, non-functional mock with none of that
# protection. Re-exporting the safe version so anything that still
# imports from here gets the real, protected implementation instead of
# quietly losing that protection.

from integrations.core_bridges import WebScraperBridge

__all__ = ["WebScraperBridge"]
