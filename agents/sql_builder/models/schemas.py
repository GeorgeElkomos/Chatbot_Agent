from pydantic import BaseModel

class DatabaseResponse(BaseModel):
    User_Frendly_response: str
    Table_Data: str
