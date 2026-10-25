import os
import time
import subprocess
import webbrowser
import ctypes
from urllib.parse import quote
import psutil
import pyautogui
from core.config import SYS_CONFIG, SCREENSHOT_DIR

try:
    import pywhatkit
    HAS_PYWHATKIT = True
except Exception:
    HAS_PYWHATKIT = False

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

STOP_WORDS = {
    "this", "ts", "tis", "dis", "that", "the", "a", "an", "it", "here", "there", 
    "page", "link", "tab", "screen", "first", "second", "third", "one", 
    "button", "website", "webpage", "site", "to", "go", "open", "click", "select"
}

def click_screen_element(target_phrase):
    """Locates and clicks specific text or headings on your screen."""
    words = [w for w in target_phrase.lower().split() if w not in STOP_WORDS]
    clean_target = " ".join(words).strip()

    if not clean_target or len(clean_target) < 2:
        return None  # Let it fall through cleanly

    try:
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.08)
        pyautogui.write(clean_target, interval=0.01)
        time.sleep(0.15)
        pyautogui.press('escape')
        time.sleep(0.05)
        pyautogui.press('enter')
        return f"Navigated to '{clean_target}', {SYS_CONFIG['user_title']}."
    except Exception:
        return f"Failed to click '{clean_target}', {SYS_CONFIG['user_title']}."

def navigate_browser(action):
    try:
        if action == "click_first_link":
            # On search engines, pressing Tab once or twice highlights the first search result
            pyautogui.press('tab')
            time.sleep(0.08)
            pyautogui.press('enter')
            return f"Opening link, {SYS_CONFIG['user_title']}."
        elif action == "scroll_down":
            pyautogui.scroll(-600)
            return f"Scrolling down, {SYS_CONFIG['user_title']}."
        elif action == "scroll_up":
            pyautogui.scroll(600)
            return f"Scrolling up, {SYS_CONFIG['user_title']}."
        elif action == "back":
            pyautogui.hotkey('alt', 'left')
            return f"Going back, {SYS_CONFIG['user_title']}."
        elif action == "forward":
            pyautogui.hotkey('alt', 'right')
            return f"Going forward, {SYS_CONFIG['user_title']}."
        elif action == "refresh":
            pyautogui.hotkey('ctrl', 'r')
            return f"Refreshing page, {SYS_CONFIG['user_title']}."
        elif action == "close_tab":
            pyautogui.hotkey('ctrl', 'w')
            return f"Tab closed, {SYS_CONFIG['user_title']}."
        elif action == "new_tab":
            pyautogui.hotkey('ctrl', 't')
            return f"New tab opened, {SYS_CONFIG['user_title']}."
        elif action == "press_enter":
            pyautogui.press('enter')
            return f"Selected, {SYS_CONFIG['user_title']}."
    except Exception:
        return f"Navigation failed, {SYS_CONFIG['user_title']}."

def open_and_search(query, engine="google"):
    clean_q = query.replace("search for", "").replace("search", "").replace("open chrome and", "").replace("open browser and", "").strip()
    url = f"https://www.google.com/search?q={quote(clean_q)}"
    webbrowser.open(url)
    return f"Searching for '{clean_q}', {SYS_CONFIG['user_title']}."

def open_app(target):
    t = target.lower().strip()
    try:
        if "camera" in t:
            os.system("start microsoft.windows.camera:"); return "Camera opened."
        elif "calc" in t:
            subprocess.Popen("calc.exe"); return "Calculator opened."
        elif "notepad" in t:
            subprocess.Popen("notepad.exe"); return "Notepad opened."
        elif "settings" in t:
            os.system("start ms-settings:"); return "Settings opened."
        elif "task manager" in t:
            subprocess.Popen("taskmgr.exe"); return "Task Manager opened."
        elif "explorer" in t:
            subprocess.Popen("explorer.exe"); return "File Explorer opened."
        elif "youtube" in t:
            webbrowser.open("https://www.youtube.com"); return "YouTube opened."
        elif "chrome" in t or "browser" in t:
            webbrowser.open("https://www.google.com"); return "Browser opened."
        else:
            pyautogui.press('win'); time.sleep(0.2)
            pyautogui.write(target, interval=0.02); time.sleep(0.3)
            pyautogui.press('enter')
            return f"Launching {target}."
    except Exception:
        return f"Failed to open {target}."

def kill_process(name):
    killed = False
    for p in psutil.process_iter(['name']):
        try:
            if name.lower() in p.info['name'].lower():
                p.kill(); killed = True
        except Exception: pass
    return "Process terminated." if killed else "Process not found."

def play_youtube(query):
    try:
        if HAS_PYWHATKIT:
            pywhatkit.playonyt(query)
        else:
            webbrowser.open(f"https://youtube.com/results?search_query={quote(query)}")
        return f"Playing {query} on YouTube."
    except Exception:
        return "Playback failed."

def hotkey(k1, k2):
    try:
        pyautogui.hotkey(k1, k2); return "Done."
    except Exception: return "Failed."

def volume(action):
    try:
        if action == "up":
            for _ in range(5): pyautogui.press("volumeup")
        elif action == "down":
            for _ in range(5): pyautogui.press("volumedown")
        elif action == "mute":
            pyautogui.press("volumemute")
        return "Volume adjusted."
    except Exception: return "Volume failed."

def screenshot():
    try:
        fp = os.path.join(SCREENSHOT_DIR, f"screenshot_{int(time.time())}.png")
        pyautogui.screenshot(fp); return "Screenshot saved."
    except Exception: return "Screenshot failed."

def system_stats():
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    bat = psutil.sensors_battery()
    bs = f"{bat.percent}%" if bat else "N/A"
    return f"CPU {cpu}%, RAM {ram}%, Battery {bs}."

def lock_pc():
    ctypes.windll.user32.LockWorkStation()
    return "System locked."