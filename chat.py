from main import orchestrate
import os 
os.environ["PYTHONIOENCODING"] = "utf-8"
def chat_console():
    print("Welcome to the AI Agent Chat! Type 'exit' to quit.")
    conversation_history = []  # Out-history: full chat history
    while True:
        user_input = input("You: ")
        print("\n")
        if user_input.strip().lower() in ("exit", "quit"):  # Exit condition
            print("Goodbye!")
            break
        # Add user message to conversation history
        conversation_history.append({"role": "user", "content": user_input})
        # Pass conversation_history to orchestrate
        response = orchestrate(user_input, conversation_history=conversation_history, logs=True)
        # Add assistant response to conversation history
        conversation_history.append({"role": "assistant", "content": str(response)})
        print("Chatbot:", response, "\n\n")

if __name__ == "__main__":
    chat_console()

