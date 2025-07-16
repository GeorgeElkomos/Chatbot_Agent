"""
File: agents/sql_builder/models/schemas.py (relative to Chatbot_Agent)
"""
from pydantic import BaseModel

class DatabaseResponse(BaseModel):
    User_Frendly_response: str
    HTML_TABLE_DATA: str
