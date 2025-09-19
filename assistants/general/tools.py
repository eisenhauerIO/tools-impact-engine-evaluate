from strands import tool
from .agent import GeneralAssistantAgent

@tool
def general_assistant_tool(query: str) -> str:
    """
    Handle general knowledge queries that fall outside specialized domains.
    Provides concise, accurate responses to non-specialized questions.
    """
    print("Routed to General Assistant")
    agent = GeneralAssistantAgent()
    return agent.answer(query)