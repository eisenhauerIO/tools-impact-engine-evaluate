#!/usr/bin/env python3
"""
# 📁 Teacher's Assistant Strands Agent

A specialized Strands agent that is the orchestrator to utilize sub-agents and tools at its disposal to answer a user query.

## What This Example Shows

"""

from strands import Agent
from strands_tools import file_read, file_write, editor
#from english_assistant import english_assistant
#from language_assistant import language_assistant
#from math_assistant import math_assistant
#from computer_science_assistant import computer_science_assistant
from assistants.general.tools import assist_tool as assist

# Define a focuseds system prompt for file operations
TEACHER_SYSTEM_PROMPT = """
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
arrow_agent = Agent(
    system_prompt=TEACHER_SYSTEM_PROMPT,
    callback_handler=None,
    tools=[assist],
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
            
        