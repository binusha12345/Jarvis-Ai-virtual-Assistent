import os
import json

BASE_DIR = r"D:\JARVIS"
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "KnowledgeBase")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "Screenshots")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
PIPER_DIR = os.path.join(BASE_DIR, "piper_models")
VECTOR_DIR = os.path.join(DATA_DIR, "vector_db")

CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
HISTORY_FILE = os.path.join(DATA_DIR, "chat_history.json")

LOCAL_MODEL = "qwen2.5:1.5b"
VISION_MODEL = "moondream"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

SAMPLE_RATE = 16000
CHUNK_SIZE = 1600
ENERGY_THRESHOLD = 300
SILENCE_CHUNKS_LIMIT = 12
CONVERSATION_TIMEOUT = 18

DEFAULT_CONFIG = {
    "assistant_name": "JARVIS",
    "user_title": "Sir",
    "wake_words": ["jarvis", "jarvice", "javis", "javi", "hello", "hi"],
    "voice_rate": "+10%",
    "offline_mode": False
}

for d in [DATA_DIR, ASSETS_DIR, KNOWLEDGE_DIR, SCREENSHOT_DIR, LOGS_DIR, PIPER_DIR, VECTOR_DIR]:
    os.makedirs(d, exist_ok=True)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    cfg.setdefault(k, v)
                return cfg
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

# EXPORT GLOBAL SYS_CONFIG
SYS_CONFIG = load_config()