# Moved from tools/function_tools.py
# Add any function_caller agent-specific tool code here

from agents.function_caller.utils.helpers import find_matching_function


def call_function_from_user_intent(user_intent: str, user_data: dict = None) -> dict:
    """
    Given a user intent string and optional user data, find the best matching function and prepare the API call details.
    Returns a dict with method, url, required params, and a sample request body.
    """
    func = find_matching_function(user_intent)
    if not func:
        return {"error": "No matching function found for the user request."}
    # Prepare the API call details
    method = func.get("method")
    url = func.get("url")
    params = func.get("parameters", {})
    body_schema = params.get("body")
    required_fields = body_schema.get("required", []) if body_schema else []
    properties = body_schema.get("properties", {}) if body_schema else {}
    # Build a sample body from user_data or placeholders
    body = {}
    for field in required_fields:
        if user_data and field in user_data:
            body[field] = user_data[field]
        else:
            body[field] = f"<{field}>"  # placeholder
    # Add optional fields if user_data provided
    if user_data:
        for field in properties:
            if field not in body and field in user_data:
                body[field] = user_data[field]
    return {
        "function_name": func.get("name"),
        "description": func.get("description"),
        "method": method,
        "url": url,
        "required_fields": required_fields,
        "body": body,
        "auth_required": func.get("auth_required", True),
        "tags": func.get("tags", [])
    }
