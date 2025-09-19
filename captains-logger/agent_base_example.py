import os
import logging

# CRITICAL: Set AWS environment variables BEFORE importing strands
# This was key to solving my region configuration issues
os.environ['AWS_PROFILE'] = 'default'
os.environ['AWS_REGION'] = 'us-west-2'  # Use a region where you have model access

# Configure logging for better debugging
# logging.basicConfig(level=logging.DEBUG, 
format='%(levelname)s | %(name)s | %(message)s'

from strands import Agent, tool
from strands_tools import calculator, current_time, python_repl

# Define a custom tool
@tool
def letter_counter(word: str, letter: str) -> int:
    """
    Count occurrences of a specific letter in a word.
    
    Args:
        word (str): The input word to search in
        letter (str): The specific letter to count
        
    Returns:
        int: The number of occurrences of the letter in the word
    """
    if not isinstance(word, str) or not isinstance(letter, str):
        return 0
    
    if len(letter) != 1:
        raise ValueError("The 'letter' parameter must be a single character")
        
    return word.lower().count(letter.lower())

# Create the agent with tools and specify the model
# Use a model ID you confirmed access to in your region
agent = Agent(
    tools=[calculator, current_time, python_repl, letter_counter],
    model="us.anthropic.claude-3-5-haiku-20241022-v1:0"  # Specify your model
)

# Define a message to test the agent
message = """
I have 4 requests:
1. What is the time right now?
2. Calculate 3111696 / 74088
3. Tell me how many letter R's are in the word "strawberry"
4. Output a script that does what we just spoke about!
   Use your python tools to confirm that the script works before outputting it
"""

# Run the agent and handle any errors
if __name__ == "__main__":
    try:
        print("Running the agent...")
        response = agent(message)
        print("\nAgent Response:")
        print(response)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()