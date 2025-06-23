from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Optional
import requests
import uuid
import os
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file if it exists
def load_env_file():
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env_file()

app = FastAPI(title="Educational Tutor Chatbot", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

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

async def demo_chat_response(request: ChatRequest):
    """Demo mode responses when API key is not configured"""
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
    
    # Generate demo responses based on message content
    message_lower = request.message.lower()
    
    if any(word in message_lower for word in ['math', 'calculate', '×', '*', '+', '-', '/', 'multiply', 'divide', 'add', 'subtract']):
        if '15' in message_lower and ('×' in message_lower or '*' in message_lower or 'multiply' in message_lower) and '8' in message_lower:
            demo_response = "Great math question! Let me help you with 15 × 8.\n\n15 × 8 = 120\n\nHere's how I calculated it:\n- 15 × 8 = (10 + 5) × 8\n- = (10 × 8) + (5 × 8)\n- = 80 + 40\n- = 120\n\nRemember, multiplication is repeated addition!"
        else:
            demo_response = "I'd love to help you with math! I can explain arithmetic, fractions, algebra, geometry, and more. What specific math topic would you like to explore?"
    
    elif any(word in message_lower for word in ['science', 'photosynthesis', 'biology', 'chemistry', 'physics']):
        if 'photosynthesis' in message_lower:
            demo_response = "Photosynthesis is how plants make their own food! 🌱\n\n**Simple explanation:**\n- Plants use sunlight, water, and carbon dioxide\n- They combine these to make glucose (sugar) for energy\n- Oxygen is released as a bonus for us to breathe!\n\n**The equation:** 6CO₂ + 6H₂O + sunlight → C₆H₁₂O₆ + 6O₂\n\nChloroplasts in plant leaves contain chlorophyll, which captures sunlight and makes this amazing process possible!"
        else:
            demo_response = "Science is fascinating! I can help explain concepts in biology, chemistry, physics, earth science, and more. What would you like to learn about?"
    
    elif any(word in message_lower for word in ['english', 'grammar', 'noun', 'verb', 'writing']):
        if 'noun' in message_lower:
            demo_response = "A noun is a word that names a person, place, thing, or idea! 📝\n\n**Examples:**\n- **Person:** teacher, student, doctor\n- **Place:** school, park, library\n- **Thing:** book, pencil, computer\n- **Ideas:** happiness, friendship, courage\n\n**Types of nouns:**\n- Proper nouns (names): Sarah, London, Monday\n- Common nouns: dog, city, day\n- Plural nouns: cats, books, children\n\nNouns are the building blocks of sentences!"
        else:
            demo_response = "I'm here to help with English! Whether it's grammar, vocabulary, writing, reading comprehension, or literature analysis - just ask!"
    
    elif any(word in message_lower for word in ['history', 'egypt', 'ancient', 'war', 'past']):
        if 'egypt' in message_lower:
            demo_response = "Ancient Egypt is one of the most fascinating civilizations! 🏺\n\n**Key Facts:**\n- Lasted over 3,000 years (3100 BCE - 30 BCE)\n- Built amazing pyramids and the Sphinx\n- Developed hieroglyphics for writing\n- The Nile River was crucial for farming\n\n**Famous rulers:**\n- Pharaoh Tutankhamun (King Tut)\n- Cleopatra VII\n- Ramesses II\n\n**Achievements:**\n- Medicine and surgery\n- Mathematics and engineering\n- Art and architecture\n- Mummification process"
        else:
            demo_response = "History helps us understand how we got to where we are today! I can discuss ancient civilizations, wars, important events, and historical figures. What period interests you?"
    
    elif any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
        demo_response = "Hello! 👋 I'm your educational tutor, here to help you learn and understand concepts from Class 1 to Class 12.\n\nI can help with:\n- 📚 **Math** - arithmetic, algebra, geometry\n- 🔬 **Science** - biology, chemistry, physics\n- 📝 **English** - grammar, writing, literature\n- 🏛️ **History** - world events, civilizations\n- And much more!\n\nWhat would you like to learn about today?"
    
    else:
        demo_response = f"Thank you for your question: \"{request.message}\"\n\n🤖 **Demo Mode Active**\n\nI'm running in demo mode since the OpenRouter API key isn't configured. In full mode, I would provide detailed, personalized tutoring responses using advanced AI.\n\nTo unlock full functionality:\n1. Get a free API key from https://openrouter.ai\n2. Set the OPENROUTER_API_KEY environment variable\n3. Restart the server\n\nTry asking about math, science, English, or history to see sample responses!"
    
    # Add assistant response to session history
    chat_sessions[session_id].append({
        "role": "assistant",
        "content": demo_response,
        "timestamp": datetime.now().isoformat()
    })
    
    return ChatResponse(response=demo_response, session_id=session_id)

@app.get("/")
async def root():
    return FileResponse('static/index.html')

@app.get("/api")
async def api_root():
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
    
    # Demo mode when API key is not configured
    if not OPENROUTER_API_KEY:
        return await demo_chat_response(request)
    
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
            print("OpenRouter API failed, falling back to demo mode")
            return await demo_chat_response(request)
        
        try:
            result = response.json()
        except Exception as json_error:
            print(f"JSON parsing error: {json_error}")
            print(f"Raw response: {response.text}")
            print("JSON parsing failed, falling back to demo mode")
            return await demo_chat_response(request)
        
        if "choices" not in result or not result["choices"]:
            print(f"No choices in response: {result}")
            print("Invalid response structure, falling back to demo mode")
            return await demo_chat_response(request)
        
        try:
            assistant_response = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as content_error:
            print(f"Content extraction error: {content_error}")
            print(f"Response structure: {result}")
            print("Content extraction failed, falling back to demo mode")
            return await demo_chat_response(request)
        
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
    except HTTPException:
        # Re-raise HTTPException without modification
        raise
    except Exception as e:
        error_msg = str(e) if str(e) else f"Unknown {type(e).__name__} error"
        print(f"Error in chat endpoint: {error_msg}")  # Debug log
        print(f"Error type: {type(e).__name__}")  # Debug log
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")  # Debug log
        
        # Always fallback to demo mode for any unexpected error
        print("Unexpected error occurred, falling back to demo mode")
        return await demo_chat_response(request)

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