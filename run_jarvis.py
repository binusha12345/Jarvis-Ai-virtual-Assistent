import warnings
warnings.filterwarnings("ignore")

import sys
import re
import time
import datetime
import ollama

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from core.config import SYS_CONFIG, LOCAL_MODEL, CONVERSATION_TIMEOUT
from core.brain import ask_ai
from core.router import sanitize_command, classify_intent
from core.memory import save_memory, load_memories
from engines.vad_engine import listen_smart_vad
from engines.stt_engine import transcribe
from engines.tts_engine import speak, play_fx
from engines.vision_engine import see_screen, see_camera
from modules.web_search import web_search
from modules.clipboard_ai import transform_clipboard
from modules.file_manager import organize_folder, find_large_files
from modules.scheduler import add_reminder, start_scheduler
from modules import os_control
from ui.hud_overlay import start_hud, set_hud

print("=" * 65)
print("  🤖 JARVIS INDUSTRIAL ENGINE v2.4 (PRECISION SCREEN & STT ENGINE)")
print("=" * 65)

print(f"[1/3] Locking GPU Brain ({LOCAL_MODEL}) into VRAM...")
try:
    ollama.chat(
        model=LOCAL_MODEL, 
        messages=[{"role": "user", "content": "hi"}], 
        options={"num_predict": 2, "num_gpu": 99, "keep_alive": "60m"}
    )
    print("  ⚡ Local GPU Brain Online & VRAM Locked!")
except Exception:
    print("  ⚠️ LLM Connection Offline")

print("[2/3] Starting Background Scheduler & Sci-Fi HUD...")
start_scheduler()
start_hud()
time.sleep(0.3)

print("[3/3] System Fully Active & Ready")
print("=" * 65 + "\n")

def check_wake(text):
    lt = text.lower()
    for w in SYS_CONFIG["wake_words"]:
        if w in lt: return w
    return None

def execute_direct(text):
    cmd = sanitize_command(text)
    # 1. Clean STT speech homophone artifacts
    raw = text.lower().strip()
    raw = re.sub(r'\bts\b|\btis\b|\bdis\b', 'this', raw)

    # 2. PRIORITY 1: Explicit Structural Navigation Commands
    if any(w in raw for w in ["first link", "first result", "open first link", "click first link", "go to first link"]):
        return os_control.navigate_browser("click_first_link")

    if any(w in raw for w in ["go back", "previous page", "back page"]):
        return os_control.navigate_browser("back")

    if any(w in raw for w in ["go forward", "next page"]):
        return os_control.navigate_browser("forward")

    if any(w in raw for w in ["scroll down", "page down", "go down"]):
        return os_control.navigate_browser("scroll_down")

    if any(w in raw for w in ["scroll up", "page up", "go up"]):
        return os_control.navigate_browser("scroll_up")

    if any(w in raw for w in ["close tab", "close this tab"]):
        return os_control.navigate_browser("close_tab")

    if any(w in raw for w in ["new tab", "open new tab"]):
        return os_control.navigate_browser("new_tab")

    if any(w in raw for w in ["refresh page", "reload page"]):
        return os_control.navigate_browser("refresh")

    # 3. PRIORITY 2: Specific Text & Tab Clicker Agent
    click_match = re.search(r'(?:go to|click|open|select|press)(?:\s+the|\s+this|\s+page|\s+screen|\s+that)*\s+(.+)', raw)
    if click_match and not any(w in raw for w in ["browser", "chrome", "youtube", "camera", "notepad", "settings", "calculator", "file", "folder", "desktop"]):
        phrase = click_match.group(1).strip()
        result = os_control.click_screen_element(phrase)
        if result:
            return result

    # 4. PRIORITY 3: Compound Browser Search Commands
    if ("open chrome" in raw or "open browser" in raw or "google" in raw) and "search" in raw:
        query = re.sub(r'.*search\s+', '', raw).replace("on chrome", "").replace("on google", "").replace("in browser", "").strip()
        return os_control.open_and_search(query)

    if raw.startswith("search ") or "search for " in raw:
        query = raw.replace("search for ", "").replace("search ", "").strip()
        return os_control.open_and_search(query)

    # 5. PRIORITY 4: Application Launcher
    if cmd.startswith("open "):
        return os_control.open_app(cmd.replace("open ", ""))
    if cmd.startswith("close ") or cmd.startswith("kill "):
        return os_control.kill_process(cmd.split(" ", 1)[1])

    # 6. PRIORITY 5: YouTube Control
    if cmd.startswith("play "):
        song = cmd.replace("play ", "").replace("on youtube", "").strip()
        return os_control.play_youtube(song)

    # 7. PRIORITY 6: Memory System
    if "remember " in raw:
        fact = raw.replace("remember that ", "").replace("remember ", "").strip()
        if fact:
            save_memory(f"fact_{int(time.time())}", fact)
            return f"Committed to memory, {SYS_CONFIG['user_title']}."

    if "what do you remember" in cmd or "my memories" in cmd:
        m = load_memories()
        return f"I remember: {', '.join(m.values())}" if m else "No memories stored."

    # 8. PRIORITY 7: Real-Time Information & System Hardware
    if "time" in cmd and ("what" in cmd or "now" in cmd):
        return f"The time is {datetime.datetime.now().strftime('%I:%M %p')}, {SYS_CONFIG['user_title']}."
    if "date" in cmd and ("what" in cmd or "today" in cmd):
        return f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}."

    if "take photo" in raw or "capture photo" in raw:
        return see_camera("Describe this scene.")

    if "screenshot" in cmd: return os_control.screenshot()
    if "volume up" in cmd: return os_control.volume("up")
    if "volume down" in cmd: return os_control.volume("down")
    if "mute" in cmd: return os_control.volume("mute")
    if "lock pc" in cmd: return os_control.lock_pc()
    if "system status" in cmd or "diagnostics" in cmd: return os_control.system_stats()

    # 9. PRIORITY 8: File Management
    if "organize" in cmd and ("downloads" in cmd or "folder" in cmd):
        import os
        return organize_folder(os.path.join(os.path.expanduser("~"), "Downloads"))

    # 10. PRIORITY 9: Clipboard AI
    if "fix my clipboard" in raw: return transform_clipboard("Fix any bugs or errors")
    if "translate clipboard" in raw: return transform_clipboard("Rewrite as professional English")

    # 11. PRIORITY 10: Task Reminders
    if "remind me" in raw:
        m = re.search(r"in (\d+) minute", raw)
        if m: return add_reminder(raw.replace("remind me", "").strip(), minutes=int(m.group(1)))

    return None

def handle_command(cmd):
    set_hud("think")
    play_fx("process")

    # High-Speed Direct System Execution (< 0.02s)
    direct = execute_direct(cmd)
    if direct:
        return direct

    # Intent Classifier for Complex Brain Queries
    intent = classify_intent(cmd)

    if intent == "VISION_SCREEN":
        return see_screen(cmd)
    if intent == "VISION_CAMERA":
        return see_camera(cmd)
    if intent == "RAG":
        from modules.rag_engine import rag_query
        context = rag_query(cmd)
        return ask_ai(cmd, extra_context=f"\nKNOWLEDGE BASE:\n{context}")
    if intent == "WEB_SEARCH":
        results = web_search(cmd)
        return ask_ai(cmd, extra_context=f"\nWEB RESULTS:\n{results}")

    return ask_ai(cmd)

def main():
    is_active = False
    last_t = 0
    name = SYS_CONFIG["assistant_name"]

    while True:
        try:
            set_hud("idle")
            if is_active and (time.time() - last_t > CONVERSATION_TIMEOUT):
                is_active = False

            print(f"\n{'🟢 ACTIVE' if is_active else '⚪ STANDBY'} 🎤 Listening...", end="", flush=True)
            set_hud("listen")

            raw_audio = listen_smart_vad()
            text = transcribe(raw_audio)

            if not text or len(text) < 2: continue
            print(f"\r👂 Heard: \"{text}\"")

            wake = check_wake(text)
            command = None

            if wake:
                is_active = True; last_t = time.time()
                play_fx("wake")
                command = re.sub(re.escape(wake), '', text, flags=re.IGNORECASE).strip(" ,.?!:;")
                if not command or len(command) < 2:
                    command = f"Hello {name}"
            elif is_active:
                last_t = time.time()
                command = text

            if command:
                print(f"👤 You: {command}")
                start = time.time()
                reply = handle_command(command)
                print(f"🤖 {name} ({time.time()-start:.2f}s): {reply}")
                set_hud("speak")
                speak(reply)
                last_t = time.time()

        except KeyboardInterrupt:
            print(f"\nGoodbye {SYS_CONFIG['user_title']}!"); break
        except Exception as e:
            print(f"\n⚠️ Loop error: {e}")
            continue

if __name__ == "__main__":
    main()