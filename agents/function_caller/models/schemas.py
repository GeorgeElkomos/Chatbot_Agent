"""
File: agents/function_caller/models/schemas.py (relative to Chatbot_Agent)

✅ ENHANCED: Added proper Pydantic schema for function_caller output
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class FunctionCallResponse(BaseModel):
    """
    Structured response from FunctionCaller agent
    Contains complete API function call details
    """
    function_name: str
    description: str
    method: str  # GET, POST, PUT, DELETE
    url: str
    auth_required: bool
    response: str  # User-friendly explanation
    required_fields: Optional[List[str]] = None
    body: Optional[Dict[str, Any]] = None
    path_parameters: Optional[Dict[str, Any]] = None
    query_parameters: Optional[Dict[str, Any]] = None
    missing_data: Optional[List[str]] = None
    tags: Optional[List[str]] = None
