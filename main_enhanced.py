"""
Enhanced Main API with Conversation History and User Interaction Support
Maintains conversation context and allows agents to ask for missing information
"""

import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from remove_emoji import remove_emoji
from orchestrator_enhanced import orchestrate
from agents.registry.registration import register_agents
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class Message(BaseModel):
    """Single conversation message"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


class ChatbotRequest(BaseModel):
    """Request with conversation history support"""
    user_input: str
    conversation_history: List[Message] = []
    session_id: Optional[str] = None


class ChatbotResponse(BaseModel):
    """Response with status and conversation tracking"""
    status: str  # "success", "needs_input", "error"
    response: Optional[Dict[str, Any]] = None
    question: Optional[str] = None  # If needs_input, this is the question to ask user
    conversation_history: List[Message] = []
    message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    message: str


app = FastAPI(title="Enhanced Chatbot API with Conversation History", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

remove_emoji()
register_agents()

# In-memory conversation storage (use Redis/database for production)
conversations: Dict[str, List[Message]] = {}


@app.post("/chatbot/public", response_model=ChatbotResponse)
async def chatbot_endpoint(request: ChatbotRequest):
    """
    Enhanced chatbot endpoint with conversation history support
    
    Maintains conversation context and handles when agents need more information
    """
    try:
        if not request.user_input.strip():
            raise HTTPException(status_code=400, detail="user_input cannot be empty")
        
        # Convert Pydantic models to dicts for orchestrator
        conversation_history = [msg.model_dump() for msg in request.conversation_history]
        
        # Add current user message to history
        conversation_history.append({
            "role": "user",
            "content": request.user_input
        })
        
        # Store conversation if session_id provided
        if request.session_id:
            conversations[request.session_id] = conversation_history
        
        # Run orchestration with conversation history
        result = orchestrate(
            user_request=request.user_input,
            conversation_history=conversation_history,
            logs=False,
            interactive=True  # Enable asking user for missing info
        )
        
        # Check if agent needs more information
        if isinstance(result, dict) and result.get("status") == "needs_input":
            return ChatbotResponse(
                status="needs_input",
                question=result.get("question"),
                conversation_history=[Message(**msg) for msg in conversation_history],
                message="Agent needs more information to continue. Please answer the question."
            )
        
        # Add assistant response to conversation history
        assistant_message = {
            "role": "assistant",
            "content": str(result)
        }
        conversation_history.append(assistant_message)
        
        # Update stored conversation
        if request.session_id:
            conversations[request.session_id] = conversation_history
        
        return ChatbotResponse(
            status="success",
            response=result,
            conversation_history=[Message(**msg) for msg in conversation_history],
            message="Request processed successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/chatbot/continue", response_model=ChatbotResponse)
async def chatbot_continue(request: ChatbotRequest):
    """
    Continue a conversation after user provides requested information
    
    Use this endpoint when previous response had status="needs_input"
    """
    try:
        if not request.user_input.strip():
            raise HTTPException(status_code=400, detail="user_input cannot be empty")
        
        # Retrieve conversation history
        conversation_history = []
        if request.session_id and request.session_id in conversations:
            conversation_history = conversations[request.session_id]
        else:
            conversation_history = [msg.model_dump() for msg in request.conversation_history]
        
        # Add user's answer to history
        conversation_history.append({
            "role": "user",
            "content": request.user_input
        })
        
        # Continue orchestration with updated history
        result = orchestrate(
            user_request=request.user_input,
            conversation_history=conversation_history,
            logs=False,
            interactive=True
        )
        
        # Check if still needs more information
        if isinstance(result, dict) and result.get("status") == "needs_input":
            return ChatbotResponse(
                status="needs_input",
                question=result.get("question"),
                conversation_history=[Message(**msg) for msg in conversation_history],
                message="Agent needs more information to continue."
            )
        
        # Add assistant response
        assistant_message = {
            "role": "assistant",
            "content": str(result)
        }
        conversation_history.append(assistant_message)
        
        # Update stored conversation
        if request.session_id:
            conversations[request.session_id] = conversation_history
        
        return ChatbotResponse(
            status="success",
            response=result,
            conversation_history=[Message(**msg) for msg in conversation_history],
            message="Request processed successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/conversation/{session_id}", response_model=List[Message])
async def get_conversation(session_id: str):
    """
    Retrieve full conversation history for a session
    """
    if session_id not in conversations:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return [Message(**msg) for msg in conversations[session_id]]


@app.delete("/conversation/{session_id}")
async def delete_conversation(session_id: str):
    """
    Delete conversation history for a session
    """
    if session_id not in conversations:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del conversations[session_id]
    return {"status": "success", "message": f"Conversation {session_id} deleted"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy", 
        message="Enhanced Chatbot API with conversation history is running successfully"
    )


# Run the FastAPI server with uvicorn
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        print("=" * 80)
        print("🚀 Starting Enhanced Chatbot API Server")
        print("=" * 80)
        print("\n✅ Features:")
        print("   - Conversation history tracking")
        print("   - Agent can ask for missing information")
        print("   - Session management")
        print("   - Multi-turn conversations")
        print("\n📡 Endpoints:")
        print("   POST /chatbot/public - Main chat endpoint")
        print("   POST /chatbot/continue - Continue conversation after providing info")
        print("   GET  /conversation/{session_id} - Get conversation history")
        print("   DELETE /conversation/{session_id} - Delete conversation")
        print("   GET  /health - Health check")
        print("\n" + "=" * 80)
        uvicorn.run("main_enhanced:app", host="0.0.0.0", port=8080, reload=True)
    else:
        # Interactive test mode
        print("=" * 80)
        print("🧪 INTERACTIVE TEST MODE")
        print("=" * 80)
        print("\nTesting enhanced orchestrator with conversation history...")
        
        conversation_history = []
        
        # Test 1: Ask about employee
        print("\n[Test 1] User: 'Show me John's expense violations'")
        result1 = orchestrate(
            "Show me John's expense violations",
            conversation_history=conversation_history,
            logs=True,
            interactive=True
        )
        
        if isinstance(result1, dict) and result1.get("status") == "needs_input":
            print(f"\n🤖 Agent Question: {result1['question']}")
            print("\n[User provides answer]: 'John Smith'")
            
            conversation_history.append({"role": "user", "content": "Show me John's expense violations"})
            conversation_history.append({"role": "assistant", "content": result1['question']})
            conversation_history.append({"role": "user", "content": "John Smith"})
            
            result2 = orchestrate(
                "John Smith",
                conversation_history=conversation_history,
                logs=True,
                interactive=True
            )
            print("\n✅ Final Result:")
            import json
            print(json.dumps(result2, indent=2))
        else:
            print("\n✅ Result:")
            import json
            print(json.dumps(result1, indent=2))
        
        print("\n" + "=" * 80)
        print("Check ai-output/history.json for detailed conversation tracking!")
        print("=" * 80)
