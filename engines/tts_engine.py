import os
import io
import time
import asyncio
import subprocess
import edge_tts
import pygame
from core.config import SYS_CONFIG, PIPER_DIR

pygame.mixer.init(frequency=24000, size=-16, channels=1)

PIPER_VOICE = os.path.join(PIPER_DIR, "en_GB-northern_english_male-medium.onnx")

async def _edge_speech(text):
    rate = SYS_CONFIG.get("voice_rate", "+10%")
    comm = edge_tts.Communicate(text=text, voice="en-GB-RyanNeural", rate=rate)
    buf = io.BytesIO()
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    buf.seek(0)
    return buf

def _piper_speech(text):
    try:
        out_file = os.path.join(PIPER_DIR, "temp_out.wav")
        proc = subprocess.run(
            ["piper", "--model", PIPER_VOICE, "--output_file", out_file],
            input=text.encode('utf-8'), capture_output=True, timeout=15
        )
        return out_file if os.path.exists(out_file) else None
    except Exception:
        return None

def speak(text):
    try:
        audio_stream = asyncio.run(_edge_speech(text))
        pygame.mixer.music.load(audio_stream)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(20)
        pygame.mixer.music.unload()
        time.sleep(0.1)
        return
    except Exception:
        pass

    wav = _piper_speech(text)
    if wav:
        try:
            pygame.mixer.music.load(wav)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.wait(20)
            pygame.mixer.music.unload()
        except Exception:
            pass

def play_fx(fx_name):
    from core.config import ASSETS_DIR
    fx_file = os.path.join(ASSETS_DIR, f"{fx_name}.wav")
    if os.path.exists(fx_file):
        try:
            sound = pygame.mixer.Sound(fx_file)
            sound.set_volume(0.4)
            sound.play()
        except Exception:
            pass