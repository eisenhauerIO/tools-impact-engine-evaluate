import os
from strands import Agent

class GeneralAssistantAgent:
    @staticmethod
    def _read_system_prompt() -> str:
        path = os.path.join(os.path.dirname(__file__), "general_prompt.md")
        with open(path, encoding="utf-8") as f:
            return f.read()

    def __init__(self):
        self.agent = Agent(
            system_prompt=self._read_system_prompt(),
            tools=[],
        )

    def answer(self, query: str) -> str:
        prompt = (
            "Answer this general knowledge question concisely, remembering to start by acknowledging that you are not an expert in this specific area: "
            + query
        )
        try:
            response = str(self.agent(prompt))
            return response or "Sorry, I couldn't provide an answer to your question."
        except Exception as e:
            return f"Error processing your question: {e}"
