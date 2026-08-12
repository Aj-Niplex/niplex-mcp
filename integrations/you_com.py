# DEPRECATED — not imported by any active manager.
#
# search_manager.py uses integrations/core_bridges.py's YouComBridge,
# which falls back to a free DuckDuckGo/Jina search when no API key is
# configured. This file was an older duplicate that just errored out
# instead. Re-exporting the current version so anything that still
# imports from here gets the working implementation.

from integrations.core_bridges import YouComBridge

__all__ = ["YouComBridge"]
