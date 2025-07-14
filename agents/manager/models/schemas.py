from pydantic import BaseModel

class ManagerDecision(BaseModel):
    next_agent: str
    next_task_description: str
    stop: bool = False
