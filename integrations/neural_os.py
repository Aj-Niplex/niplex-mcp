# DEPRECATED — not wired to any tool.
#
# This was an early scaffold for a "Neural-OS" concept. query()/update()
# used to return a hardcoded, made-up string (fake goals/tasks) as if it
# were real data — genuinely risky if anything had ever called it
# thinking it was live. The actual, working implementation is
# integrations/neural_bridge.py, which talks to the real, separately
# deployed Neural-MCP server backed by Adarshs-Stack. Left inert on
# purpose so nothing can accidentally surface fabricated personal
# information as if it were true.

class NeuralOSBridge:
    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "NeuralOSBridge is deprecated and returned fake placeholder data — "
            "do not use. See integrations/neural_bridge.py (ask_neural / "
            "log_to_neural) for the real implementation."
        )
