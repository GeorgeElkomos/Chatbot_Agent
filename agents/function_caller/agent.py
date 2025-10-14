"""
File: agents/function_caller/agent.py (relative to Chatbot_Agent)

✅ ENHANCED: Following analytics agent gold standard pattern
Functions embedded in backstory for optimal LLM reasoning
"""
from crewai import Agent
from agents.llm_config import basic_llm
from agents.function_caller.tools.function_tools import execute_function_call
import json

def _load_functions_for_backstory():
    """Load and format API functions for backstory - analytics pattern"""
    with open("./System-Info/functions.json", "r", encoding="utf-8") as f:
        functions_data = json.load(f)
    
    # Format as expert-level API documentation
    functions_text = "## COMPLETE API FUNCTIONS KNOWLEDGE BASE\n\n"
    functions_text += "You have expert knowledge of all available API functions in the system.\n"
    functions_text += "Each function has specific parameters, authentication requirements, and use cases.\n\n"
    
    # Group by tags for better organization
    by_tag = {}
    for func in functions_data.get("functions", []):
        tags = func.get("tags", ["general"])
        for tag in tags:
            if tag not in by_tag:
                by_tag[tag] = []
            by_tag[tag].append(func)
    
    for tag, funcs in sorted(by_tag.items()):
        functions_text += f"### {tag.upper()} Functions\n\n"
        for func in funcs:
            name = func.get("name", "")
            desc = func.get("description", "")
            method = func.get("method", "")
            url = func.get("url", "")
            params = func.get("parameters", {})
            body_schema = params.get("body", {})
            required = body_schema.get("required", []) if body_schema else []
            auth = func.get("auth_required", True)
            
            functions_text += f"**{name}**\n"
            functions_text += f"- **Description:** {desc}\n"
            functions_text += f"- **Method:** {method}\n"
            functions_text += f"- **URL:** `{url}`\n"
            functions_text += f"- **Auth Required:** {'Yes' if auth else 'No'}\n"
            if required:
                functions_text += f"- **Required Fields:** {', '.join(required)}\n"
            functions_text += "\n"
    
    return functions_text

_FUNCTIONS_CONTEXT = _load_functions_for_backstory()

function_caller_agent = Agent(
    role="Expert API Function Orchestrator",
    goal=(
        "Map user requests to the correct API function and prepare complete, valid API call details. "
        "Return structured JSON with function name, method, URL, required parameters, and sample request body."
    ),
    backstory=(
        "You are the **Expert API Function Orchestrator** with complete knowledge of all backend API endpoints. "
        "You excel at understanding user intent and mapping it to the appropriate API function with all required parameters.\n\n"
        f"{_FUNCTIONS_CONTEXT}\n"
        "## API EXPERTISE\n\n"
        "**Your Responsibilities:**\n"
        "1. **Intent Analysis:** Parse user requests to identify which API function they need\n"
        "2. **Parameter Extraction:** Extract all required and optional parameters from user input\n"
        "3. **Validation:** Ensure all required fields are present, request missing data if needed\n"
        "4. **API Call Preparation:** Generate complete API call details with proper formatting\n\n"
        "**Common Request Patterns:**\n"
        "- 'Show me [resource]' → Map to GET endpoint for that resource\n"
        "- 'Create [resource]' → Map to POST endpoint, extract required fields\n"
        "- 'Update [resource]' → Map to PUT/PATCH endpoint, extract ID and fields\n"
        "- 'Delete [resource]' → Map to DELETE endpoint, extract ID\n\n"
        "**Response Format:**\n"
        "Always return structured JSON with:\n"
        "- function_name: The matched function name\n"
        "- description: What the function does\n"
        "- method: HTTP method (GET/POST/PUT/DELETE)\n"
        "- url: Full API endpoint URL\n"
        "- required_fields: List of required parameters\n"
        "- body: Complete request body (with user data or placeholders)\n"
        "- auth_required: Whether authentication is needed\n\n"
        "**Error Handling:**\n"
        "- If no matching function found: Return clear error explaining why\n"
        "- If missing required data: List what's missing and how to provide it\n"
        "- If ambiguous request: Ask clarifying questions\n\n"
        "Use your single tool `execute_function_call` to process the user request and return the API details."
    ),
    llm=basic_llm,
    tools=[execute_function_call],  # ✅ Single clean tool (analytics pattern)
    verbose=False,
)

