"""
File: agents/page_navigator/models/schemas.py (relative to Chatbot_Agent)
"""
from pydantic import BaseModel

class NavigationResponse(BaseModel):
    response: str
    navigation_link: str = ""
