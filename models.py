from ollama import chat
# One‑off: send a single user message
response = chat(
    model="deepseek-r1:1.5b",
    messages=[{"role": "user", "content": "Explain Newton's first law."}],
    
)

print(response.message.content)  # Output the response content