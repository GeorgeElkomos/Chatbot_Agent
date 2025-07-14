from pydantic import BaseModel

class DatabaseResponse(BaseModel):
    User_Frendly_response: str
    HTML_TABLE_DATA: str
