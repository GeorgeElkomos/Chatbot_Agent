from pydantic import BaseModel

class QAResponse(BaseModel):
    response: str
