##memory.py file is here to handle the memory of the bot. It will store the data in a json file and will be able to retrieve it when needed. It will also be able to delete the data when needed.
import os
import json
from core.config import MEMORY_FILE, HISTORY_FILE

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
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)

def load_persistent_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                hist = json.load(f)
                clean = [m for m in hist if "can't assist" not in m.get("content", "").lower()]
                return clean[-10:]
        except Exception:
            return []
    return []

def save_persistent_history(history):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)