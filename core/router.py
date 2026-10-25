import re
from core.config import SYS_CONFIG

def sanitize_command(raw_text):
    cmd = raw_text.lower().strip()
    for w in SYS_CONFIG["wake_words"]:
        cmd = re.sub(r'\b' + re.escape(w) + r'\b', '', cmd)
    fillers = ["please", "can you", "could you", "kindly", "for me", "app", "application"]
    for f in fillers:
        cmd = cmd.replace(f, "")
    return cmd.strip(" ,.?!:;")

def classify_intent(text):
    """Return intent category."""
    t = text.lower()

    if any(w in t for w in ["look at screen", "see my screen", "what's on screen", "analyze screen", "read screen"]):
        return "VISION_SCREEN"
    if any(w in t for w in ["look at camera", "webcam", "who is in front"]):
        return "VISION_CAMERA"
    if any(w in t for w in ["my notes", "search my files", "my documents", "knowledge base", "my pdf"]):
        return "RAG"
    if any(w in t for w in ["organize", "clean up folder", "sort files", "find files larger"]):
        return "FILE_MANAGER"
    if any(w in t for w in ["fix my clipboard", "clipboard code", "translate clipboard"]):
        return "CLIPBOARD_AI"
    if any(w in t for w in ["remind me", "schedule", "every day at", "every morning"]):
        return "SCHEDULER"
    if any(w in t for w in ["search", "who is", "what is", "latest news", "weather", "tell me about"]):
        return "WEB_SEARCH"
    
    return "GENERAL"