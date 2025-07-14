from pydantic import BaseModel

class NavigationResponse(BaseModel):
    response: str
    navigation_link: str = ""
