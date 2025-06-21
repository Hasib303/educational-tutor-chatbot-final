from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import requests
import uuid
import os
from datetime import datetime

app = FastAPI(title="Educational Tutor Chatbot", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly include OPTIONS
    allow_headers=["*"],  # Allows all headers
)

# In-memory session storage
chat_sessions: Dict[str, list] = {}

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "mistralai/mistral-7b-instruct:free"
SYSTEM_PROMPT = "You are a helpful, accurate educator tutor."

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

class SessionResponse(BaseModel):
    session_id: str
    message: str

@app.get("/")
async def root():
    return {"message": "Educational Tutor Chatbot API", "version": "1.0.0"}

@app.post("/chat/new")
async def create_new_session():
    session_id = str(uuid.uuid4())
    chat_sessions[session_id] = []
    return SessionResponse(session_id=session_id, message="New chat session created")

@app.post("/chat")
async def chat_with_tutor(request: ChatRequest):
    print(f"API Key present: {bool(OPENROUTER_API_KEY)}")  # Debug log
    print(f"API Key length: {len(OPENROUTER_API_KEY) if OPENROUTER_API_KEY else 0}")  # Debug log
    
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenRouter API key not configured")
    
    print(f"Received message: {request.message}")  # Debug log
    
    # Handle session
    session_id = request.session_id or str(uuid.uuid4())
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    
    # Add user message to session history
    chat_sessions[session_id].append({
        "role": "user",
        "content": request.message,
        "timestamp": datetime.now().isoformat()
    })
    
    # Prepare messages for OpenRouter
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add recent chat history (last 10 messages)
    recent_messages = chat_sessions[session_id][-10:]
    for msg in recent_messages:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    try:
        print(f"Making request to OpenRouter with model: {MODEL_NAME}")  # Debug log
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY.strip()}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://educational-tutor-chatbot.onrender.com",
            "X-Title": "Educational Tutor Chatbot"
        }
        print(f"Headers: {headers}")  # Debug log
        
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7
            },
            timeout=30.0
        )
        
        print(f"OpenRouter response status: {response.status_code}")  # Debug log
        
        if response.status_code != 200:
            print(f"OpenRouter error: {response.text}")  # Debug log
            raise HTTPException(
                status_code=response.status_code,
                detail=f"OpenRouter API error: {response.text}"
            )
        
        result = response.json()
        assistant_response = result["choices"][0]["message"]["content"]
        
        print(f"Got response: {assistant_response[:100]}...")  # Debug log
        
        # Add assistant response to session history
        chat_sessions[session_id].append({
            "role": "assistant",
            "content": assistant_response,
            "timestamp": datetime.now().isoformat()
        })
        
        return ChatResponse(response=assistant_response, session_id=session_id)
        
    except requests.exceptions.Timeout:
        print("Request timeout")  # Debug log
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        error_msg = str(e)
        print(f"Error in chat endpoint: {error_msg}")  # Debug log
        print(f"Error type: {type(e).__name__}")  # Debug log
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")  # Debug log
        raise HTTPException(status_code=500, detail=f"Error processing request: {error_msg}")

@app.get("/chat/{session_id}/history")
async def get_chat_history(session_id: str):
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "history": chat_sessions[session_id]}

@app.delete("/chat/{session_id}")
async def delete_session(session_id: str):
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    del chat_sessions[session_id]
    return {"message": f"Session {session_id} deleted successfully"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "sessions_count": len(chat_sessions)}

@app.get("/debug")
async def debug_info():
    return {
        "api_key_configured": bool(OPENROUTER_API_KEY),
        "api_key_length": len(OPENROUTER_API_KEY) if OPENROUTER_API_KEY else 0,
        "api_key_starts_with": OPENROUTER_API_KEY[:10] + "..." if OPENROUTER_API_KEY else "None",
        "model": MODEL_NAME,
        "url": OPENROUTER_URL
    }

@app.get("/test-openrouter")
async def test_openrouter():
    """Test OpenRouter API directly"""
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="API key not configured")
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY.strip()}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://educational-tutor-chatbot.onrender.com",
            "X-Title": "Educational Tutor Chatbot"
        }
        
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say hello"}
                ],
                "max_tokens": 50
            },
            timeout=30.0
        )
        
        return {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text
        }
        
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

@app.options("/chat")
async def chat_options():
    return {"message": "CORS preflight"}

@app.options("/chat/new")
async def new_session_options():
    return {"message": "CORS preflight"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)