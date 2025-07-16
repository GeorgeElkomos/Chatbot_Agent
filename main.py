import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from remove_emoji import remove_emoji
from orchestrator import orchestrate
from agents.registry.registration import register_agents
from typing import Dict, Any
from pydantic import BaseModel

class ChatbotRequest(BaseModel):
    user_input: str

class ChatbotResponse(BaseModel):
    status: str
    response: Dict[str, Any]
    message: str = None

class HealthResponse(BaseModel):
    status: str
    message: str

app = FastAPI(title="Chatbot API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

remove_emoji()
register_agents()

# FastAPI Endpoints
@app.post("/chatbot/public", response_model=ChatbotResponse)
async def chatbot_endpoint(request: ChatbotRequest):
    try:
        if not request.user_input.strip():
            raise HTTPException(status_code=400, detail="user_input cannot be empty")
        final_outputs = orchestrate(request.user_input, logs=False)
        return ChatbotResponse(
            status="success",
            response=final_outputs,
            message="Request processed successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        message="Chatbot API is running successfully"
    )

# Run the FastAPI server with uvicorn
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
    else:
        _user_request = "summarize the Last transfer."
        print("User Input:", _user_request)
        response = orchestrate(_user_request, logs=False)
        print("Final outputs:", response)