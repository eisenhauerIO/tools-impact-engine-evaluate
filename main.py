#!/usr/bin/env python3
"""
# 📁 Teacher's Assistant Strands Agent

A specialized Strands agent that is the orchestrator to utilize sub-agents and tools at its disposal to answer a user query.

## What This Example Shows

"""


from framework.strands_agent import create_strands_agent

from assistants import general_assistant

# Define a focuseds system prompt for file operations
ARROW_SYSTEM_PROMPT = """
You are TeachAssist, a sophisticated educational orchestrator designed to coordinate educational support across multiple subjects. Your role is to:

1. Analyze incoming student queries and determine the most appropriate specialized agent to handle them:
   - Math Agent: For mathematical calculations, problems, and concepts
   - English Agent: For writing, grammar, literature, and composition
   - Language Agent: For translation and language-related queries
   - Computer Science Agent: For programming, algorithms, data structures, and code execution
   - General Assistant: For all other topics outside these specialized domains

2. Key Responsibilities:
   - Accurately classify student queries by subject area
   - Route requests to the appropriate specialized agent
   - Maintain context and coordinate multi-step problems
   - Ensure cohesive responses when multiple agents are needed

3. Decision Protocol:
   - all queries → General Assistant

Always confirm your understanding before routing to ensure accurate assistance.
"""


# Create a file-focused agent with selected tools
arrow_agent = create_strands_agent(
    system_prompt=ARROW_SYSTEM_PROMPT,
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

        response = arrow_agent(
                user_input, 
        )
            
        # Extract and print only the relevant content from the specialized agent's response
        content = str(response)
        print(content)
            
        