"""
File: chat.py (relative to Chatbot_Agent)
"""

import os
import sys

# Set UTF-8 encoding for Windows console before any imports
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")

from agents.registry.registration import register_agents
from remove_emoji import remove_emoji
from orchestrator_enhanced import orchestrate


def chat_console():
    remove_emoji()
    register_agents()
    print("Welcome to the AI Agent Chat! Type 'exit' to quit.")
    conversation_history = []  # Out-history: full chat history
    while True:
        user_input = input("You: ")
        print("\n")
        if user_input.strip().lower() in ("exit", "quit"):  # Exit condition
            print("Goodbye!")
            break
        response = orchestrate(user_input, conversation_history, logs=False)
        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": str(response)})
        print("Chatbot:", response["GeneralQAAgent"], "\n\n")


if __name__ == "__main__":
    chat_console()
