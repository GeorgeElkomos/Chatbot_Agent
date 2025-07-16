"""
File: agents/general_qa/models/schemas.py (relative to Chatbot_Agent)
"""
from pydantic import BaseModel

class QAResponse(BaseModel):
    response: str
