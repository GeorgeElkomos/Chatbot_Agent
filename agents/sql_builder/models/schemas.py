from pydantic import BaseModel

class DatabaseResponse(BaseModel):
    response: str
