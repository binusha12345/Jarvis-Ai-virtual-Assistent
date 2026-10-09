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
import numpy as np
import sounddevice as sd
import speech_recognition as sr
import edge_tts
import ollama
import pygame

# PC Control Libraries
import psutil
import pyautogui

# ──────────────────────────────────────────────
# UTF-8 DISPLAY FIX
# ──────────────────────────────────────────────
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# ──────────────────────────────────────────────
# CONFIGURATION & CONSTANTS
# ──────────────────────────────────────────────
BASE_DIR = r"D:\JARVIS"
MEMORY_FILE = os.path.join(BASE_DIR, "memory.json")
LOCAL_MODEL = "qwen2.5:1.5b"

SAMPLE_RATE = 16000
WAKE_WORDS = ["jarvis", "jarvice", "javis", "javi", "travis", "hello", "hi"]
CONVERSATION_TIMEOUT = 12

CHUNK_SIZE = 1600             # 100ms
ENERGY_THRESHOLD = 350
SILENCE_CHUNKS_LIMIT = 5      # 0.5s cutoff

# 🔑 GLOBAL SYSTEM PROMPT (Defined First)
SYSTEM_PROMPT = (
    "You are JARVIS, Tony Stark's personal AI assistant from Iron Man. "
    "1. Speak in crisp, polite British English. "
    "2. Always address the user as 'Sir'. "
    "3. Keep responses under 10 words (1 short sentence). "
    "4. Never use markdown, asterisks (*), emojis, or thinking tags."
)

recognizer = sr.Recognizer()
pygame.mixer.init(frequency=24000, size=-16, channels=1)

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

# ──────────────────────────────────────────────
# 🧠 PERSISTENT MEMORY ENGINE (`memory.json`)
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

def clear_memories():
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)
    return "All memories cleared from disk, Sir."

def get_memory_context():
    memories = load_memories()
    if not memories:
        return "No saved user memories yet."
    mem_str = "USER MEMORIES & FACTS:\n"
    for k, v in memories.items():
        mem_str += f"- {k}: {v}\n"
    return mem_str

def build_dynamic_system_prompt():
    mem_ctx = get_memory_context()
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"DYNAMIC SYSTEM CONTEXT:\n"
        f"{mem_ctx}"
    )

# ──────────────────────────────────────────────
# 🛡️ UNIVERSAL 2-STEP CONFIRMATION PROTOCOL
# ──────────────────────────────────────────────
pending_action_func = None
pending_action_desc = ""
pending_action_expiry = 0

def register_pending_action(action_func, description):
    global pending_action_func, pending_action_desc, pending_action_expiry
    pending_action_func = action_func
    pending_action_desc = description
    pending_action_expiry = time.time() + 14  # 14-second confirmation window
    return f"Are you sure you want me to {description}, Sir? Say 'Confirm' or 'Yes' to proceed."

# ──────────────────────────────────────────────
# 🧹 SENTENCE CLEANER (Strips Filler Words)
# ──────────────────────────────────────────────
def clean_sentence(text):
    cmd = text.lower().strip()
    
    # Remove wake word
    for w in WAKE_WORDS:
        cmd = re.sub(r'\b' + re.escape(w) + r'\b', '', cmd)
        
    # Remove courtesy/filler words
    fillers = [
        "please", "can you", "could you", "would you", "kindly",
        "i want you to", "i want to", "go ahead and", "tell me",
        "for me", "app", "application"
    ]
    for f in fillers:
        cmd = cmd.replace(f, "")
        
    return cmd.strip(" ,.?!:;")

# ──────────────────────────────────────────────
# ⏱️ REAL SYSTEM TIME & DATE
# ──────────────────────────────────────────────
def get_real_time():
    now = datetime.datetime.now()
    return f"The time is currently {now.strftime('%I:%M %p')}, Sir."

def get_real_date():
    now = datetime.datetime.now()
    return f"Today is {now.strftime('%A, %B %d, %Y')}, Sir."

# ──────────────────────────────────────────────
# 🦾 UNIVERSAL APP & PC LAUNCHER
# ──────────────────────────────────────────────
def do_open_app(raw_app_name):
    """Launches UWP Apps, Desktop Executables, and Photoshop/Installed Apps"""
    app = raw_app_name.lower().strip()
    
    try:
        if "camera" in app:
            os.system("start microsoft.windows.camera:")
            return "Camera is now open, Sir."
        elif "calculator" in app or "calc" in app:
            subprocess.Popen("calc.exe")
            return "Calculator is now open, Sir."
        elif "notepad" in app:
            subprocess.Popen("notepad.exe")
            return "Notepad is now open, Sir."
        elif "settings" in app:
            os.system("start ms-settings:")
            return "Windows Settings opened, Sir."
        elif "task manager" in app:
            subprocess.Popen("taskmgr.exe")
            return "Task Manager opened, Sir."
        elif "file explorer" in app or "explorer" in app or "my computer" in app:
            subprocess.Popen("explorer.exe")
            return "File Explorer opened, Sir."
        elif "youtube" in app:
            webbrowser.open("https://www.youtube.com")
            return "YouTube opened in browser, Sir."
        elif "chrome" in app or "browser" in app or "google" in app:
            webbrowser.open("https://www.google.com")
            return "Browser opened, Sir."
        elif "cmd" in app or "terminal" in app or "command prompt" in app:
            subprocess.Popen("cmd.exe")
            return "Command Prompt opened, Sir."
        else:
            # Universal Windows Start Search for Photoshop, WhatsApp, Spotify, Premiere, Games, etc.
            pyautogui.press('win')
            time.sleep(0.3)
            pyautogui.write(app, interval=0.03)
            time.sleep(0.4)
            pyautogui.press('enter')
            return f"Launching {raw_app_name}, Sir."
    except Exception as e:
        return f"Failed to open {raw_app_name}, Sir."

def do_type_text(text_to_type):
    try:
        pyautogui.write(text_to_type, interval=0.02)
        return "Typed the text, Sir."
    except Exception:
        return "Failed to type text, Sir."

def do_press_key(key_name):
    try:
        pyautogui.press(key_name)
        return f"Pressed {key_name}, Sir."
    except Exception:
        return f"Failed to press {key_name}, Sir."

def do_hotkey(key1, key2):
    try:
        pyautogui.hotkey(key1, key2)
        return "Command executed, Sir."
    except Exception:
        return "Failed to execute command, Sir."

def do_scroll(direction):
    try:
        amount = -600 if direction == "down" else 600
        pyautogui.scroll(amount)
        return f"Scrolled {direction}, Sir."
    except Exception:
        return "Scroll failed, Sir."

def do_screenshot():
    try:
        shots_dir = os.path.join(BASE_DIR, "Screenshots")
        os.makedirs(shots_dir, exist_ok=True)
        filepath = os.path.join(shots_dir, f"screenshot_{int(time.time())}.png")
        pyautogui.screenshot(filepath)
        return "Screenshot saved to your Jarvis folder, Sir."
    except Exception:
        return "Screenshot failed, Sir."

def do_adjust_volume(action):
    try:
        if action == "up":
            for _ in range(5): pyautogui.press("volumeup")
            return "Volume increased, Sir."
        elif action == "down":
            for _ in range(5): pyautogui.press("volumedown")
            return "Volume decreased, Sir."
        elif action == "mute":
            pyautogui.press("volumemute")
            return "Audio toggled, Sir."
    except Exception:
        return "Audio adjustment failed, Sir."

def do_shutdown():
    os.system("shutdown /s /t 5")
    return "Shutting down system in 5 seconds, Sir."

def do_restart():
    os.system("shutdown /r /t 5")
    return "Restarting system in 5 seconds, Sir."

def do_lock_pc():
    ctypes.windll.user32.LockWorkStation()
    return "System locked, Sir."

def get_battery():
    battery = psutil.sensors_battery()
    if battery:
        plug = "plugged in" if battery.power_plugged else "on battery"
        return f"Battery is at {battery.percent} percent and {plug}, Sir."
    return "Battery details unavailable, Sir."

def get_sys_stats():
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    return f"CPU is at {cpu} percent, RAM is at {ram} percent, Sir."

# ──────────────────────────────────────────────
# 🎯 SYSTEM INTENT & MEMORY PARSER
# ──────────────────────────────────────────────
def parse_system_intent(raw_spoken_text):
    global pending_action_func, pending_action_desc, pending_action_expiry
    
    cmd_raw = raw_spoken_text.lower().strip()
    cmd_clean = clean_sentence(raw_spoken_text)

    # 1. STEP 2: USER CONFIRMATION CHECK (Runs first)
    if pending_action_func and time.time() < pending_action_expiry:
        affirmative_words = ["yes", "yeah", "sure", "confirm", "do it", "proceed", "go ahead", "okay", "ok", "yep"]
        negative_words = ["no", "nop", "cancel", "stop", "dont", "don't", "nevermind"]

        if any(word in cmd_raw.split() for word in affirmative_words) or cmd_raw in affirmative_words:
            func_to_run = pending_action_func
            pending_action_func = None
            pending_action_desc = ""
            return func_to_run()

        elif any(word in cmd_raw.split() for word in negative_words) or cmd_raw in negative_words:
            pending_action_func = None
            pending_action_desc = ""
            return "Action cancelled, Sir."

    # Clear expired confirmation
    if pending_action_func and time.time() >= pending_action_expiry:
        pending_action_func = None
        pending_action_desc = ""

    # 2. EXPLICIT MEMORY COMMANDS
    if cmd_raw.startswith("remember that ") or cmd_clean.startswith("remember that "):
        fact_to_save = cmd_raw.replace("remember that ", "").replace("remember ", "").strip()
        if ":" in fact_to_save:
            k, v = fact_to_save.split(":", 1)
            save_memory(k.strip(), v.strip())
        else:
            save_memory(f"memory_{int(time.time())}", fact_to_save)
        return f"I have committed that to memory, Sir: '{fact_to_save}'"

    if "forget everything" in cmd_clean or "clear memory" in cmd_clean:
        return register_pending_action(
            clear_memories,
            "delete all saved memories from disk"
        )

    if "what do you remember" in cmd_clean or "list memories" in cmd_clean:
        mems = load_memories()
        if not mems:
            return "I currently have no stored memories, Sir."
        m_list = ", ".join([f"{v}" for v in mems.values()])
        return f"Here is what I remember: {m_list}, Sir."

    # 3. REAL TIME & DATE
    if any(w in cmd_clean for w in ["time now", "what time", "current time", "what is the time"]):
        return get_real_time()

    if any(w in cmd_clean for w in ["today date", "what date", "current date", "what is the date", "today's date"]):
        return get_real_date()

    # 4. APP LAUNCHING & PC CONTROL INTENTS
    if cmd_clean.startswith("open ") or "open " in cmd_raw:
        app_target = re.sub(r'.*open\s+', '', cmd_raw).strip()
        if app_target:
            return register_pending_action(
                lambda: do_open_app(app_target),
                f"open {app_target}"
            )

    if cmd_clean.startswith("type ") or "type " in cmd_raw:
        text_target = re.sub(r'.*type\s+', '', cmd_raw).strip()
        if text_target:
            return register_pending_action(
                lambda: do_type_text(text_target),
                f"type '{text_target}'"
            )

    if "close window" in cmd_clean or "close this" in cmd_clean:
        return register_pending_action(
            lambda: do_hotkey('alt', 'f4'),
            "close the active window"
        )

    if "show desktop" in cmd_clean or "minimize all" in cmd_clean:
        return register_pending_action(
            lambda: do_hotkey('win', 'd'),
            "show the desktop"
        )

    if "switch window" in cmd_clean or "switch app" in cmd_clean:
        return register_pending_action(
            lambda: do_hotkey('alt', 'tab'),
            "switch windows"
        )

    if "press enter" in cmd_clean:
        return register_pending_action(
            lambda: do_press_key('enter'),
            "press Enter"
        )

    if "press space" in cmd_clean or "spacebar" in cmd_clean:
        return register_pending_action(
            lambda: do_press_key('space'),
            "press Spacebar"
        )

    if "copy" in cmd_clean and len(cmd_clean) < 10:
        return register_pending_action(
            lambda: do_hotkey('ctrl', 'c'),
            "copy selected items"
        )

    if "paste" in cmd_clean and len(cmd_clean) < 10:
        return register_pending_action(
            lambda: do_hotkey('ctrl', 'v'),
            "paste from clipboard"
        )

    if "select all" in cmd_clean:
        return register_pending_action(
            lambda: do_hotkey('ctrl', 'a'),
            "select all items"
        )

    if "scroll down" in cmd_clean:
        return register_pending_action(
            lambda: do_scroll("down"),
            "scroll down"
        )

    if "scroll up" in cmd_clean:
        return register_pending_action(
            lambda: do_scroll("up"),
            "scroll up"
        )

    if "screenshot" in cmd_clean or "capture screen" in cmd_clean:
        return register_pending_action(
            do_screenshot,
            "take a screenshot"
        )

    if "volume up" in cmd_clean or "increase volume" in cmd_clean:
        return register_pending_action(
            lambda: do_adjust_volume("up"),
            "increase volume"
        )

    if "volume down" in cmd_clean or "decrease volume" in cmd_clean:
        return register_pending_action(
            lambda: do_adjust_volume("down"),
            "decrease volume"
        )

    if "mute" in cmd_clean or "unmute" in cmd_clean:
        return register_pending_action(
            lambda: do_adjust_volume("mute"),
            "toggle audio mute"
        )

    if "lock pc" in cmd_clean or "lock laptop" in cmd_clean or "lock screen" in cmd_clean:
        return register_pending_action(
            do_lock_pc,
            "lock the system"
        )

    if "shutdown" in cmd_clean or "shut down" in cmd_clean:
        return register_pending_action(
            do_shutdown,
            "shut down the computer"
        )

    if "restart" in cmd_clean or "reboot" in cmd_clean:
        return register_pending_action(
            do_restart,
            "restart the computer"
        )

    if "battery" in cmd_clean:
        return get_battery()

    if "system status" in cmd_clean or "cpu" in cmd_clean or "ram" in cmd_clean or "performance" in cmd_clean:
        return get_sys_stats()

    return None

# ──────────────────────────────────────────────
# BOOT SEQUENCE
# ──────────────────────────────────────────────
print("=" * 60)
print("  🤖 JARVIS (UNIVERSAL CONTROL & PERSISTENT MEMORY)")
print("=" * 60)

print(f"\n[1/2] Connecting to Local GPU Brain ({LOCAL_MODEL})...")
try:
    ollama.chat(
        model=LOCAL_MODEL,
        messages=[{"role": "user", "content": "hi"}],
        options={"num_predict": 2}
    )
    print(f"  ⚡ Local GPU Brain {LOCAL_MODEL} Ready!")
except Exception:
    print(f"  ⚠️ Could not find '{LOCAL_MODEL}'. Fallback to 'qwen2.5:3b'...")
    LOCAL_MODEL = "qwen2.5:3b"

print("[2/2] Loading Persistent Memory Engine & Safety Shield...")
try:
    mems = load_memories()
    print(f"  ✅ Memory File Loaded ({len(mems)} stored facts).")
except Exception as e:
    print(f"  ⚠️ Memory init error: {e}")

print("\n" + "=" * 60)
print("  🗣️  JARVIS FULL PC CONTROL & MEMORY ONLINE")
print("  Try: 'open photoshop', 'remember that my project is AI', 'what time is it'")
print("=" * 60 + "\n")

chat_history = [{"role": "system", "content": build_dynamic_system_prompt()}]

# ──────────────────────────────────────────────
# INSTANT VOICE ACTIVITY DETECTOR
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
    for w in WAKE_WORDS:
        if w in lower_text:
            return w
    return None

def ask_ai(user_message):
    chat_history[0] = {"role": "system", "content": build_dynamic_system_prompt()}
    chat_history.append({"role": "user", "content": user_message})
    
    if len(chat_history) > 7:
        chat_history[:] = [chat_history[0]] + chat_history[-6:]

    try:
        response = ollama.chat(
            model=LOCAL_MODEL,
            messages=chat_history,
            options={
                "num_predict": 30,
                "temperature": 0.4,
                "num_ctx": 1024
            }
        )
        reply = response['message']['content'].strip()
        reply = re.sub(r'[*#_~`>-]', '', reply).strip()
        chat_history.append({"role": "assistant", "content": reply})
        return reply if reply else "Pardon me Sir, please repeat."

    except Exception as e:
        print(f"\n  ⚠️ Ollama Error: {e}")
        return "Pardon me Sir, an error occurred."

async def _generate_speech(text):
    communicate = edge_tts.Communicate(text=text, voice="en-GB-RyanNeural", rate="+10%")
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
# MAIN LOOP
# ──────────────────────────────────────────────
def main():
    is_active = False
    last_interaction = 0

    while True:
        try:
            if is_active:
                remaining = int(CONVERSATION_TIMEOUT - (time.time() - last_interaction))
                if remaining > 0:
                    print(f"\n🟢 [ACTIVE - {remaining}s left] 🎤 Listening...")
                else:
                    is_active = False
                    print("\n⚪ [STANDBY] 🎤 Listening for 'Jarvis'...")
            else:
                print("\n⚪ [STANDBY] 🎤 Listening for 'Jarvis'...")

            spoken_text = listen_smart_vad()

            if is_active and (time.time() - last_interaction > CONVERSATION_TIMEOUT):
                is_active = False

            if not spoken_text or len(spoken_text) < 2:
                continue

            print(f"👂 Heard: \"{spoken_text}\"")

            matched_wake = check_wake_word(spoken_text)
            command = None

            if matched_wake:
                is_active = True
                last_interaction = time.time()
                command = re.sub(re.escape(matched_wake), '', spoken_text, flags=re.IGNORECASE).strip(" ,.?!:;")
                if not command or len(command) < 2:
                    command = "Hello Jarvis"
            elif is_active:
                last_interaction = time.time()
                command = spoken_text

            if command:
                print(f"👤 You: {command}")
                
                start_t = time.time()
                
                # 1. System Intent & Memory Check
                system_reply = parse_system_intent(command)
                
                if system_reply:
                    answer = system_reply
                    elapsed = time.time() - start_t
                    print(f"⚙️ System/Memory Action ({elapsed:.2f}s)")
                else:
                    # 2. Conversational Questions -> LLM AI (with Memory context)
                    print("🧠 Thinking...", end="", flush=True)
                    answer = ask_ai(command)
                    elapsed = time.time() - start_t
                    print(f" ({elapsed:.2f}s)")

                print(f"🤖 JARVIS: {answer}")
                
                speak(answer)
                last_interaction = time.time()

        except KeyboardInterrupt:
            print("\nShutting down JARVIS. Goodbye Sir!")
            break
        except Exception as e:
            print(f"\n⚠️ Loop error: {e}")
            continue

if __name__ == "__main__":
    main()