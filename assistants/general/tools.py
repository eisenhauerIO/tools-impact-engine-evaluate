from strands import tool

from assistants.general.agent import GeneralAssistant

assistant: GeneralAssistant | None = None  # injected at runtime

@tool(name="assist", description="General assistance on a query")
def general_assistant_tool(query: str) -> str:
    assert assistant is not None, "Assistant not initialized"
    return assistant.assist(query)
