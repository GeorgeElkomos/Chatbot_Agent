"""
File: agents/function_caller/utils/helpers.py (relative to Chatbot_Agent)
"""
# Moved from utils/helpers.py
# Add any function_caller agent-specific helper code here


import json


def _load_project_functions() -> dict:
    with open("./System-Info/functions.json", "r", encoding="utf-8") as f:
        return json.load(f)

def find_matching_function(user_intent: str) -> dict:
    """
    Tries to find a function in functions.json that matches the user intent (by name or description).
    Returns the function dict or None if not found.
    """
    functions = _load_project_functions().get("functions", [])
    user_intent_lower = user_intent.lower()
    # Try exact name match first
    for func in functions:
        if func["name"].lower() in user_intent_lower:
            return func
    # Try description match
    for func in functions:
        if any(word in user_intent_lower for word in func["name"].lower().split("_")):
            return func
        if func["description"] and any(word in user_intent_lower for word in func["description"].lower().split()):
            return func
    # Try fuzzy match (contains any function name word)
    for func in functions:
        if any(word in user_intent_lower for word in func["name"].replace("_", " ").split()):
            return func
    return None
