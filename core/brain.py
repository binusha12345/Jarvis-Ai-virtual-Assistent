import re
import datetime
import ollama
from core.config import SYS_CONFIG, LOCAL_MODEL
from core.memory import load_memories, load_persistent_history, save_persistent_history

chat_history = load_persistent_history()

def build_system_prompt(extra_context=""):
    memories = load_memories()
    mem_str = "\n".join([f"- {k}: {v}" for k, v in memories.items()]) if memories else "None."
    name = SYS_CONFIG["assistant_name"]
    title = SYS_CONFIG["user_title"]
    now_str = datetime.datetime.now().strftime("%A, %B %d, %Y - %I:%M %p")

    return (
        f"You are {name}, an advanced AI assistant for {title}.\n"
        f"CURRENT TIME: {now_str}\n"
        f"USER MEMORIES:\n{mem_str}\n\n"
        f"CRITICAL INSTRUCTIONS:\n"
        f"1. NEVER tell the user to 'do it yourself' or 'visit a website manually'. Always answer directly.\n"
        f"2. Speak in polished, concise British English.\n"
        f"3. Always address user as '{title}'.\n"
        f"4. Keep responses direct and short (1 to 2 sentences max).\n"
        f"5. No markdown, asterisks, or emojis.\n"
        f"{extra_context}"
    )

def ask_ai(user_message, extra_context=""):
    global chat_history
    sys_prompt = build_system_prompt(extra_context)
    messages = [{"role": "system", "content": sys_prompt}] + chat_history
    messages.append({"role": "user", "content": user_message})

    try:
        # keep_alive: "60m" forces model to stay locked in GPU VRAM
        response = ollama.chat(
            model=LOCAL_MODEL,
            messages=messages,
            options={
                "num_predict": 80,
                "temperature": 0.4,
                "num_ctx": 2048,
                "num_gpu": 99,
                "keep_alive": "60m"
            }
        )
        reply = response['message']['content'].strip()
        reply = re.sub(r'[*#_~`>-]', '', reply).strip()

        if "can't assist" not in reply.lower() and "do it yourself" not in reply.lower():
            chat_history.append({"role": "user", "content": user_message})
            chat_history.append({"role": "assistant", "content": reply})
            if len(chat_history) > 12:
                chat_history = chat_history[-12:]
            save_persistent_history(chat_history)
        else:
            reply = f"Understood {SYS_CONFIG['user_title']}, processing your request directly."

        return reply if reply else f"Pardon me {SYS_CONFIG['user_title']}, please repeat."
    except Exception:
        return f"Pardon me {SYS_CONFIG['user_title']}, my local brain encountered an error."