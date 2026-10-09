import os
import sys
import re
import io
import time
import json
import datetime
import asyncio
import subprocess
import webbrowser
import ctypes
from urllib.parse import quote
import numpy as np
import sounddevice as sd
import speech_recognition as sr
import edge_tts
import ollama
import pygame

# Hardware & System Automation Libraries
import psutil
import pyautogui

try:
    import pywhatkit
    HAS_PYWHATKIT = True
except ImportError:
    HAS_PYWHATKIT = False

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

# ──────────────────────────────────────────────
# UTF-8 TERMINAL DISPLAY FIX
# ──────────────────────────────────────────────
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# ──────────────────────────────────────────────
# PATHS & CONFIGURATION
# ──────────────────────────────────────────────
BASE_DIR = r"D:\JARVIS"
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
MEMORY_FILE = os.path.join(BASE_DIR, "memory.json")
AUDIO_INPUT = os.path.join(BASE_DIR, "input.wav")

LOCAL_MODEL = "qwen2.5:1.5b"
SAMPLE_RATE = 16000
CONVERSATION_TIMEOUT = 14

CHUNK_SIZE = 1600
ENERGY_THRESHOLD = 350
SILENCE_CHUNKS_LIMIT = 5

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

recognizer = sr.Recognizer()
pygame.mixer.init(frequency=24000, size=-16, channels=1)

# ──────────────────────────────────────────────
# ⚙️ DYNAMIC SYSTEM CONFIG & IDENTITY STATE
# ──────────────────────────────────────────────
DEFAULT_CONFIG = {
    "assistant_name": "JARVIS",
    "user_title": "Sir",
    "wake_words": ["jarvis", "jarvice", "javis", "javi", "travis", "hello", "hi", "binusha"],
    "voice_rate": "+10%",
    "groq_api_key": ""
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                # Merge defaults for any missing keys
                for k, v in DEFAULT_CONFIG.items():
                    cfg.setdefault(k, v)
                return cfg
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

SYS_CONFIG = load_config()

# ──────────────────────────────────────────────
# 🧠 PERMANENT KNOWLEDGE GRAPH & MEMORY
# ──────────────────────────────────────────────
def load_memories():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_memory(key, value):
    memories = load_memories()
    memories[key] = value
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)

def delete_memory(key):
    memories = load_memories()
    if key in memories:
        del memories[key]
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(memories, f, ensure_ascii=False, indent=2)

def build_system_prompt():
    memories = load_memories()
    mem_context = ""
    if memories:
        mem_context = "STORED USER FACTS & PREFERENCES:\n" + "\n".join([f"- {k}: {v}" for k, v in memories.items()])
    else:
        mem_context = "No stored user memories yet."

    name = SYS_CONFIG["assistant_name"]
    title = SYS_CONFIG["user_title"]

    return (
        f"You are {name}, an industrial-grade AI assistant inspired by Iron Man's JARVIS. "
        f"1. Address the user as '{title}'. "
        f"2. Keep responses concise, intelligent, and under 15 words. "
        f"3. Speak in crisp, polite British English. "
        f"4. Never use markdown, asterisks (*), emojis, or thinking tags.\n\n"
        f"{mem_context}"
    )

# ──────────────────────────────────────────────
# 🧹 COMMAND SANITIZER
# ──────────────────────────────────────────────
def sanitize_command(raw_text):
    cmd = raw_text.lower().strip()
    
    # Strip wake words
    for w in SYS_CONFIG["wake_words"]:
        cmd = re.sub(r'\b' + re.escape(w) + r'\b', '', cmd)

    # Strip conversational courtesy fillers
    fillers = [
        "please", "can you", "could you", "would you", "kindly",
        "i want you to", "i want to", "go ahead and", "for me", "app", "application"
    ]
    for f in fillers:
        cmd = cmd.replace(f, "")

    return cmd.strip(" ,.?!:;")

# ──────────────────────────────────────────────
# 💻 OS CONTROL & AUTOMATION ENGINE
# ──────────────────────────────────────────────
def do_change_identity(new_name):
    SYS_CONFIG["assistant_name"] = new_name.capitalize()
    # Add new name to wake words if not present
    new_wake = new_name.lower()
    if new_wake not in SYS_CONFIG["wake_words"]:
        SYS_CONFIG["wake_words"].append(new_wake)
    save_config(SYS_CONFIG)
    return f"My name has been updated to {SYS_CONFIG['assistant_name']}, {SYS_CONFIG['user_title']}."

def do_change_user_title(new_title):
    SYS_CONFIG["user_title"] = new_title.capitalize()
    save_config(SYS_CONFIG)
    return f"I will address you as {SYS_CONFIG['user_title']} from now on."

def do_open_app(raw_target):
    target = raw_target.lower().strip()
    try:
        if "camera" in target:
            os.system("start microsoft.windows.camera:")
            return f"Camera opened, {SYS_CONFIG['user_title']}."
        elif "calculator" in target or "calc" in target:
            subprocess.Popen("calc.exe")
            return f"Calculator opened, {SYS_CONFIG['user_title']}."
        elif "notepad" in target:
            subprocess.Popen("notepad.exe")
            return f"Notepad opened, {SYS_CONFIG['user_title']}."
        elif "settings" in target:
            os.system("start ms-settings:")
            return f"Windows Settings opened, {SYS_CONFIG['user_title']}."
        elif "task manager" in target:
            subprocess.Popen("taskmgr.exe")
            return f"Task Manager opened, {SYS_CONFIG['user_title']}."
        elif "explorer" in target or "file explorer" in target:
            subprocess.Popen("explorer.exe")
            return f"File Explorer opened, {SYS_CONFIG['user_title']}."
        elif "youtube" in target:
            webbrowser.open("https://www.youtube.com")
            return f"YouTube opened, {SYS_CONFIG['user_title']}."
        elif "chrome" in target or "browser" in target:
            webbrowser.open("https://www.google.com")
            return f"Browser opened, {SYS_CONFIG['user_title']}."
        else:
            pyautogui.press('win')
            time.sleep(0.3)
            pyautogui.write(target, interval=0.03)
            time.sleep(0.4)
            pyautogui.press('enter')
            return f"Launching {raw_target}, {SYS_CONFIG['user_title']}."
    except Exception:
        return f"Failed to launch {raw_target}, {SYS_CONFIG['user_title']}."

def do_kill_process(proc_name):
    killed = False
    clean_p = proc_name.lower().strip()
    for proc in psutil.process_iter(['name']):
        try:
            if clean_p in proc.info['name'].lower():
                proc.kill()
                killed = True
        except Exception:
            pass
    if killed:
        return f"Terminated process {proc_name}, {SYS_CONFIG['user_title']}."
    return f"Could not find running process {proc_name}, {SYS_CONFIG['user_title']}."

def do_camera_snap():
    try:
        os.system("start microsoft.windows.camera:")
        time.sleep(2.5)
        pyautogui.press('space')
        return f"Camera launched and photo captured, {SYS_CONFIG['user_title']}."
    except Exception:
        return f"Camera capture failed, {SYS_CONFIG['user_title']}."

def do_play_youtube(query):
    try:
        if HAS_PYWHATKIT:
            pywhatkit.playonyt(query)
            return f"Playing {query} on YouTube, {SYS_CONFIG['user_title']}."
        else:
            webbrowser.open(f"https://www.youtube.com/results?search_query={quote(query)}")
            return f"Searching YouTube for {query}, {SYS_CONFIG['user_title']}."
    except Exception:
        webbrowser.open(f"https://www.youtube.com/results?search_query={quote(query)}")
        return f"Opening YouTube for {query}, {SYS_CONFIG['user_title']}."

def do_type_text(text):
    try:
        pyautogui.write(text, interval=0.02)
        return f"Typed text, {SYS_CONFIG['user_title']}."
    except Exception:
        return f"Failed to type, {SYS_CONFIG['user_title']}."

def do_hotkey(k1, k2):
    try:
        pyautogui.hotkey(k1, k2)
        return f"Command executed, {SYS_CONFIG['user_title']}."
    except Exception:
        return f"Failed to execute command, {SYS_CONFIG['user_title']}."

def do_adjust_volume(action):
    try:
        if action == "up":
            for _ in range(5): pyautogui.press("volumeup")
            return f"Volume increased, {SYS_CONFIG['user_title']}."
        elif action == "down":
            for _ in range(5): pyautogui.press("volumedown")
            return f"Volume decreased, {SYS_CONFIG['user_title']}."
        elif action == "mute":
            pyautogui.press("volumemute")
            return f"Audio muted, {SYS_CONFIG['user_title']}."
    except Exception:
        return f"Volume control failed, {SYS_CONFIG['user_title']}."

def do_screenshot():
    try:
        shots_dir = os.path.join(BASE_DIR, "Screenshots")
        os.makedirs(shots_dir, exist_ok=True)
        filepath = os.path.join(shots_dir, f"screenshot_{int(time.time())}.png")
        pyautogui.screenshot(filepath)
        return f"Screenshot saved, {SYS_CONFIG['user_title']}."
    except Exception:
        return f"Screenshot failed, {SYS_CONFIG['user_title']}."

def get_real_time():
    now = datetime.datetime.now()
    return f"The time is {now.strftime('%I:%M %p')}, {SYS_CONFIG['user_title']}."

def get_real_date():
    now = datetime.datetime.now()
    return f"Today is {now.strftime('%A, %B %d, %Y')}, {SYS_CONFIG['user_title']}."

def get_sys_diagnostics():
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    bat_str = f"{battery.percent}%" if battery else "N/A"
    return f"CPU at {cpu} percent, RAM at {ram} percent, Battery at {bat_str}, {SYS_CONFIG['user_title']}."

# ──────────────────────────────────────────────
# 🎯 INTENT ROUTER & DISPATCHER
# ──────────────────────────────────────────────
def parse_and_execute_intent(raw_text):
    cmd_raw = raw_text.lower().strip()
    cmd_clean = sanitize_command(raw_text)

    # 1. Identity Mutation Commands
    if "your name is now " in cmd_raw or "change your name to " in cmd_raw or "call yourself " in cmd_raw:
        new_n = re.sub(r'.*(your name is now|change your name to|call yourself)\s+', '', cmd_raw).strip()
        if new_n:
            return do_change_identity(new_n)

    if "call me " in cmd_raw or "my title is " in cmd_raw:
        new_t = re.sub(r'.*(call me|my title is)\s+', '', cmd_raw).strip()
        if new_t:
            return do_change_user_title(new_t)

    # 2. Long-Term Memory Commands
    if "remember that " in cmd_raw or "remember " in cmd_clean:
        fact = cmd_raw.replace("remember that ", "").replace("remember ", "").strip()
        if fact:
            save_memory(f"fact_{int(time.time())}", fact)
            return f"I have saved that to memory, {SYS_CONFIG['user_title']}: '{fact}'"

    if "what do you remember" in cmd_clean or "list memories" in cmd_clean or "my memories" in cmd_clean:
        mems = load_memories()
        if not mems:
            return f"I have no stored memories, {SYS_CONFIG['user_title']}."
        return f"Here is what I remember: {', '.join(mems.values())}, {SYS_CONFIG['user_title']}."

    # 3. Real Time & Date
    if any(w in cmd_clean for w in ["time now", "what time", "current time", "what is the time"]):
        return get_real_time()

    if any(w in cmd_clean for w in ["today date", "what date", "current date", "what is the date", "today's date"]):
        return get_real_date()

    # 4. Multi-Step Camera Automation
    if "take a photo" in cmd_raw or "take photo" in cmd_raw or "capture photo" in cmd_raw or ("camera" in cmd_raw and "photo" in cmd_raw):
        return do_camera_snap()

    # 5. YouTube Song Automation
    if cmd_clean.startswith("play ") or "play " in cmd_raw:
        song = re.sub(r'.*play\s+', '', cmd_raw).replace("on youtube", "").strip()
        if song:
            return do_play_youtube(song)

    # 6. Process Termination / Killing
    if cmd_clean.startswith("close ") or cmd_clean.startswith("kill ") or cmd_clean.startswith("stop "):
        target_p = re.sub(r'^(close|kill|stop)\s+', '', cmd_clean).strip()
        if "window" in target_p or "this" in target_p:
            return do_hotkey('alt', 'f4')
        elif target_p:
            return do_kill_process(target_p)

    # 7. Open Installed Application
    if cmd_clean.startswith("open ") or "open " in cmd_raw:
        target_a = re.sub(r'.*open\s+', '', cmd_raw).strip()
        if target_a:
            return do_open_app(target_a)

    # 8. Keyboard & System Automation
    if cmd_clean.startswith("type ") or "type " in cmd_raw:
        txt = re.sub(r'.*type\s+', '', cmd_raw).strip()
        if txt:
            return do_type_text(txt)

    if "show desktop" in cmd_clean or "minimize all" in cmd_clean:
        return do_hotkey('win', 'd')

    if "switch window" in cmd_clean or "switch app" in cmd_clean:
        return do_hotkey('alt', 'tab')

    if "screenshot" in cmd_clean or "capture screen" in cmd_clean:
        return do_screenshot()

    if "volume up" in cmd_clean or "increase volume" in cmd_clean:
        return do_adjust_volume("up")

    if "volume down" in cmd_clean or "decrease volume" in cmd_clean:
        return do_adjust_volume("down")

    if "mute" in cmd_clean or "unmute" in cmd_clean:
        return do_adjust_volume("mute")

    if "lock pc" in cmd_clean or "lock laptop" in cmd_clean:
        ctypes.windll.user32.LockWorkStation()
        return f"System locked, {SYS_CONFIG['user_title']}."

    if "shutdown" in cmd_clean or "shut down" in cmd_clean:
        os.system("shutdown /s /t 5")
        return f"Shutting down in 5 seconds, {SYS_CONFIG['user_title']}."

    if "system status" in cmd_clean or "diagnostics" in cmd_clean or "battery" in cmd_clean:
        return get_sys_diagnostics()

    return None

# ──────────────────────────────────────────────
# BOOT SEQUENCE
# ──────────────────────────────────────────────
print("=" * 65)
print("  🤖 INDUSTRIAL JARVIS ENGINE (DYNAMIC IDENTITY & FULL OS CONTROL)")
print("=" * 65)

print(f"\n[1/2] Connecting to Local GPU Brain ({LOCAL_MODEL})...")
try:
    ollama.chat(
        model=LOCAL_MODEL,
        messages=[{"role": "user", "content": "hi"}],
        options={"num_predict": 2}
    )
    print(f"  ⚡ Local GPU Brain {LOCAL_MODEL} Online!")
except Exception:
    print(f"  ⚠️ Could not find '{LOCAL_MODEL}'. Using 'qwen2.5:3b'...")
    LOCAL_MODEL = "qwen2.5:3b"

print("[2/2] Loading System Registry & Configuration State...")
print(f"  ✅ Assistant Name: {SYS_CONFIG['assistant_name']}")
print(f"  ✅ User Title:     {SYS_CONFIG['user_title']}")

print("\n" + "=" * 65)
print(f"  🗣️  SYSTEM ONLINE! ({SYS_CONFIG['assistant_name']} Active)")
print("  Commands: 'open photoshop', 'your name is now Binusha', 'play believers on youtube'")
print("=" * 65 + "\n")

# ──────────────────────────────────────────────
# AUDIO & AI PIPELINE
# ──────────────────────────────────────────────
def listen_smart_vad():
    recorded_chunks = []
    has_started_speaking = False
    silence_chunks = 0
    max_duration_chunks = 80

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', blocksize=CHUNK_SIZE) as stream:
        for _ in range(max_duration_chunks):
            chunk, _ = stream.read(CHUNK_SIZE)
            audio_array = chunk.flatten()
            
            rms = np.sqrt(np.mean(np.square(audio_array, dtype=np.float32))) if len(audio_array) > 0 else 0

            if rms > ENERGY_THRESHOLD:
                has_started_speaking = True
                silence_chunks = 0
                recorded_chunks.append(chunk)
            elif has_started_speaking:
                recorded_chunks.append(chunk)
                silence_chunks += 1
                if silence_chunks >= SILENCE_CHUNKS_LIMIT:
                    break
            else:
                recorded_chunks.append(chunk)
                if len(recorded_chunks) > 3:
                    recorded_chunks.pop(0)

    if not has_started_speaking or len(recorded_chunks) < 4:
        return ""

    try:
        full_audio = np.concatenate(recorded_chunks, axis=0)
        raw_pcm = full_audio.tobytes()
        sr_audio = sr.AudioData(raw_pcm, SAMPLE_RATE, 2)
        text = recognizer.recognize_google(sr_audio, language="en-US").strip()
        return text
    except Exception:
        return ""

def check_wake_word(text):
    lower_text = text.lower().strip()
    for w in SYS_CONFIG["wake_words"]:
        if w in lower_text:
            return w
    return None

chat_history = []

def ask_ai(user_message):
    sys_prompt = build_system_prompt()
    if not chat_history:
        chat_history.append({"role": "system", "content": sys_prompt})
    else:
        chat_history[0] = {"role": "system", "content": sys_prompt}

    chat_history.append({"role": "user", "content": user_message})
    
    if len(chat_history) > 7:
        chat_history[:] = [chat_history[0]] + chat_history[-6:]

    try:
        response = ollama.chat(
            model=LOCAL_MODEL,
            messages=chat_history,
            options={
                "num_predict": 35,
                "temperature": 0.4,
                "num_ctx": 1024
            }
        )
        reply = response['message']['content'].strip()
        reply = re.sub(r'[*#_~`>-]', '', reply).strip()
        chat_history.append({"role": "assistant", "content": reply})
        return reply if reply else f"Pardon me {SYS_CONFIG['user_title']}, please repeat."

    except Exception as e:
        print(f"\n  ⚠️ AI Error: {e}")
        return f"Pardon me {SYS_CONFIG['user_title']}, an error occurred."

async def _generate_speech(text):
    rate_str = SYS_CONFIG.get("voice_rate", "+10%")
    communicate = edge_tts.Communicate(text=text, voice="en-GB-RyanNeural", rate=rate_str)
    audio_buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer.write(chunk["data"])
    audio_buffer.seek(0)
    return audio_buffer

def speak(text):
    try:
        audio_stream = asyncio.run(_generate_speech(text))
        pygame.mixer.music.load(audio_stream)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.wait(20)
            
        pygame.mixer.music.unload()
        time.sleep(0.15)
    except Exception as e:
        print(f"\n⚠️ Voice Output Error: {e}")

# ──────────────────────────────────────────────
# MAIN RUN LOOP
# ──────────────────────────────────────────────
def main():
    is_active = False
    last_interaction = 0

    while True:
        try:
            current_name = SYS_CONFIG["assistant_name"]
            
            if is_active:
                remaining = int(CONVERSATION_TIMEOUT - (time.time() - last_interaction))
                if remaining > 0:
                    print(f"\n🟢 [ACTIVE - {remaining}s left] 🎤 Listening...", end="", flush=True)
                else:
                    is_active = False
                    print(f"\n⚪ [STANDBY] 🎤 Listening for '{current_name}'...", end="", flush=True)
            else:
                print(f"\n⚪ [STANDBY] 🎤 Listening for '{current_name}'...", end="", flush=True)

            spoken_text = listen_smart_vad()

            if is_active and (time.time() - last_interaction > CONVERSATION_TIMEOUT):
                is_active = False

            if not spoken_text or len(spoken_text) < 2:
                continue

            print(f"\r👂 Heard: \"{spoken_text}\"")

            matched_wake = check_wake_word(spoken_text)
            command = None

            if matched_wake:
                is_active = True
                last_interaction = time.time()
                command = re.sub(re.escape(matched_wake), '', spoken_text, flags=re.IGNORECASE).strip(" ,.?!:;")
                if not command or len(command) < 2:
                    command = f"Hello {current_name}"
            elif is_active:
                last_interaction = time.time()
                command = spoken_text

            if command:
                print(f"👤 You: {command}")
                start_t = time.time()
                
                # 1. System Intent & Dynamic OS Automation (0.01s Execution)
                system_reply = parse_and_execute_intent(command)
                
                if system_reply:
                    answer = system_reply
                    elapsed = time.time() - start_t
                    print(f"⚙️ Direct Execution ({elapsed:.2f}s)")
                else:
                    # 2. ChatGPT-Level Intelligence Questions -> Local GPU Model
                    print("🧠 Thinking...", end="", flush=True)
                    answer = ask_ai(command)
                    elapsed = time.time() - start_t
                    print(f" ({elapsed:.2f}s)")

                print(f"🤖 {SYS_CONFIG['assistant_name']}: {answer}")
                
                speak(answer)
                last_interaction = time.time()

        except KeyboardInterrupt:
            print(f"\nShutting down {SYS_CONFIG['assistant_name']}. Goodbye {SYS_CONFIG['user_title']}!")
            break
        except Exception as e:
            print(f"\n⚠️ Loop error: {e}")
            continue

if __name__ == "__main__":
    main()