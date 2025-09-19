from strands import Agent

def create_strands_agent(system_prompt, tools, callback_handler=None):
    return Agent(
        system_prompt=system_prompt,
        callback_handler=callback_handler,
        tools=tools,
    )
