"""
File: agents/function_caller/tools/function_tools.py (relative to Chatbot_Agent)

✅ ENHANCED: Following analytics agent gold standard pattern
Single execution tool with complete function matching and API call preparation
"""

from crewai.tools import tool
import json


def _load_project_functions() -> dict:
    """Load functions from System-Info"""
    with open("./System-Info/functions.json", "r", encoding="utf-8") as f:
        return json.load(f)


def _find_matching_function(user_intent: str) -> dict:
    """
    Find best matching function based on user intent.
    Uses multi-stage matching: exact name → keyword match → fuzzy match
    """
    functions = _load_project_functions().get("functions", [])
    user_intent_lower = user_intent.lower()
    
    # Stage 1: Exact name match
    for func in functions:
        if func["name"].lower() in user_intent_lower:
            return func
    
    # Stage 2: Tag-based match
    for func in functions:
        tags = func.get("tags", [])
        if any(tag.lower() in user_intent_lower for tag in tags):
            return func
    
    # Stage 3: Description keyword match
    for func in functions:
        desc = func.get("description", "").lower()
        # Check if significant words from description appear in intent
        desc_words = [w for w in desc.split() if len(w) > 4]  # Only meaningful words
        if any(word in user_intent_lower for word in desc_words[:5]):  # Check top 5 words
            return func
    
    # Stage 4: Function name component match
    for func in functions:
        name_parts = func["name"].replace("_", " ").lower().split()
        if any(part in user_intent_lower for part in name_parts if len(part) > 3):
            return func
    
    return None


@tool
def execute_function_call(user_intent: str, user_data: dict = None) -> dict:
    """
    Execute API function call preparation based on user intent.
    
    Args:
        user_intent: Natural language description of what user wants to do
        user_data: Optional dictionary with parameter values user has provided
    
    Returns:
        Complete API call details including method, URL, required fields, and sample body
    """
    # Find matching function
    func = _find_matching_function(user_intent)
    
    if not func:
        return {
            "error": "No matching function found",
            "message": f"Could not find an API function matching: '{user_intent}'",
            "suggestion": "Try rephrasing your request or ask what functions are available"
        }
    
    # Extract function details
    method = func.get("method", "GET")
    url = func.get("url", "")
    params = func.get("parameters", {})
    body_schema = params.get("body")
    query_params = params.get("query", {})
    path_params = params.get("path", {})
    
    # Build required fields list
    required_fields = []
    if body_schema:
        required_fields = body_schema.get("required", [])
    
    # Build sample request body
    body = {}
    if body_schema:
        properties = body_schema.get("properties", {})
        
        # Add required fields (from user_data or as placeholders)
        for field in required_fields:
            if user_data and field in user_data:
                body[field] = user_data[field]
            else:
                # Create smart placeholder based on type
                field_info = properties.get(field, {})
                field_type = field_info.get("type", "string")
                if field_type == "string":
                    body[field] = f"<{field}>"
                elif field_type == "number" or field_type == "integer":
                    body[field] = 0
                elif field_type == "boolean":
                    body[field] = False
                else:
                    body[field] = f"<{field}>"
        
        # Add optional fields if user provided them
        if user_data:
            for field, field_info in properties.items():
                if field not in body and field in user_data:
                    body[field] = user_data[field]
    
    # Prepare path parameters
    path_info = {}
    for param_name, param_info in path_params.items():
        if user_data and param_name in user_data:
            path_info[param_name] = user_data[param_name]
        else:
            path_info[param_name] = f"<{param_name}>"
    
    # Prepare query parameters
    query_info = {}
    for param_name, param_info in query_params.items():
        if user_data and param_name in user_data:
            query_info[param_name] = user_data[param_name]
    
    # Build response
    result = {
        "function_name": func.get("name"),
        "description": func.get("description"),
        "method": method,
        "url": url,
        "auth_required": func.get("auth_required", True),
        "tags": func.get("tags", []),
    }
    
    if required_fields:
        result["required_fields"] = required_fields
    
    if body:
        result["body"] = body
    
    if path_info:
        result["path_parameters"] = path_info
    
    if query_info:
        result["query_parameters"] = query_info
    
    # Check for missing required data
    missing_fields = []
    if body:
        missing_fields = [field for field in required_fields if f"<{field}>" in str(body.get(field, ""))]
    if path_info:
        missing_fields.extend([field for field, value in path_info.items() if f"<{field}>" in str(value)])
    
    if missing_fields:
        result["missing_data"] = missing_fields
        result["message"] = f"Missing required data: {', '.join(missing_fields)}"
    else:
        result["message"] = "API call ready to execute"
    
    return result

