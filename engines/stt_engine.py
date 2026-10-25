import socket
import speech_recognition as sr
from core.config import SAMPLE_RATE

recognizer = sr.Recognizer()
_whisper_model = None

def transcribe(raw_pcm):
    if not raw_pcm:
        return ""
    
    # Fast cloud STT with tight socket timeout
    try:
        audio = sr.AudioData(raw_pcm, SAMPLE_RATE, 2)
        socket.setdefaulttimeout(2.5) # Prevents network hanging
        text = recognizer.recognize_google(audio, language="en-US").strip()
        return text
    except Exception:
        pass

    # Fast Local Whisper Fallback
    try:
        global _whisper_model
        if _whisper_model is None:
            from faster_whisper import WhisperModel
            _whisper_model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
            
        import tempfile, wave, os
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp.name, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(raw_pcm)
        tmp.close()
        
        segments, _ = _whisper_model.transcribe(tmp.name, language="en")
        text = " ".join([s.text for s in segments]).strip()
        os.unlink(tmp.name)
        return text
    except Exception:
        return ""