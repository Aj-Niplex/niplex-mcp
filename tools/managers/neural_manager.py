from integrations.neural_bridge import NeuralBridge


class NeuralManager:
    """Routes to Neural-MCP — the sub-agent layer that reads/writes Adarshs-Stack."""

    def __init__(self):
        self.neural = NeuralBridge()

    def describe(self):
        return {
            "namespace": "neural",
            "description": "Ask questions about Adarsh's history/context, or file new durable information — both handled by Neural-MCP's sub-agent.",
            "tools": {
                "ask": "Ask Neural a question. Args: query.",
                "log": "File new information for Neural to route appropriately. Args: summary.",
            }
        }

    def call(self, tool: str, **kwargs):
        if tool == "ask":
            return self.neural.ask(kwargs.get("query"))
        if tool == "log":
            return self.neural.log(kwargs.get("summary"))
        return f"Unknown neural tool: {tool}"
