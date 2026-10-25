import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Core JARVIS imports
from core.brain import ask_ai
from core.router import classify_intent
from modules.os_control import (
    open_app, kill_process, play_youtube, volume, screenshot,
    system_stats, lock_pc, open_and_search, navigate_browser, click_screen_element
)
from engines.stt_engine import transcribe_file  # Uses Whisper / SpeechRecognition

app = FastAPI(title="JARVIS Mobile API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

def process_jarvis_command(user_text: str) -> str:
    """Processes input text through intent router and OS controllers."""
    intent, data = classify_intent(user_text)
    
    if intent == "OPEN_APP":
        return open_app(data)
    elif intent == "KILL_PROCESS":
        return kill_process(data)
    elif intent == "PLAY_YOUTUBE":
        return play_youtube(data)
    elif intent == "VOLUME":
        return volume(data)
    elif intent == "SCREENSHOT":
        return screenshot()
    elif intent == "SYSTEM_STATS":
        return system_stats()
    elif intent == "LOCK_PC":
        return lock_pc()
    elif intent == "WEB_SEARCH":
        return open_and_search(data)
    elif intent == "NAVIGATE_BROWSER":
        return navigate_browser(data)
    elif intent == "CLICK_UI":
        return click_screen_element(data)
    else:
        # Pass to Brain (LLM)
        return ask_ai(user_text)

@app.get("/health")
def health_check():
    return {"status": "online", "message": "JARVIS API Server running smoothly."}

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    reply = process_jarvis_command(req.message)
    return {"reply": reply}

@app.post("/voice")
async def voice_endpoint(file: UploadFile = File(...)):
    """Receives recorded audio file from phone, transcribes it, and executes command."""
    temp_audio_path = os.path.join("D:\\JARVIS", "temp_remote_voice.m4a")
    try:
        with open(temp_audio_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Transcribe audio to text
        user_text = transcribe_file(temp_audio_path)
        if not user_text or not user_text.strip():
            return {"user_text": "", "reply": "I couldn't hear you clearly, Sir. Please try speaking again."}
        
        # Process command
        reply = process_jarvis_command(user_text)
        return {"user_text": user_text, "reply": reply}
        
    except Exception as e:
        print(f"[API ERROR] Voice processing failed: {e}")
        return {"user_text": "Error processing audio", "reply": "Sorry Sir, I encountered an issue processing your voice audio."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)