#!/usr/bin/env python3
"""
# 📁 Teacher's Assistant Strands Agent

A specialized Strands agent that is the orchestrator to utilize sub-agents and tools at its disposal to answer a user query.

## What This Example Shows

"""
import os

from framework.strands_agent import create_strands_agent

from assistants import general_assistant


os.environ['MOCK_WORKFLOW'] = 'True'

# Create a file-focused agent with selected tools
arrow_agent = create_strands_agent(
    system_prompt=open("prompts/arrow.md").read(),
    tools=[general_assistant],
    callback_handler=None,
)




# Example usage
if __name__ == "__main__":

    print("\n📁 Teacher's Assistant Strands Agent 📁\n")
    print("Ask a question in any subject area, and I'll route it to the appropriate specialist.")
    print("Type 'exit' to quit.")

    # Interactive loop
    while True:
        user_input = input("\n> ")
        if user_input.lower() == "exit":
            print("\nGoodbye! 👋")
            break

        response = arrow_agent(user_input)
            
        # Extract and print only the relevant content from the specialized agent's response
        content = str(response)
        print(content)
            
        