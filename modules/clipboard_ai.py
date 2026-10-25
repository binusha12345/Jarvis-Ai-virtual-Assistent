import pyperclip
from core.brain import ask_ai

def transform_clipboard(instruction):
    try:
        content = pyperclip.paste()
        if not content:
            return "Clipboard is empty."
        prompt = f"{instruction}:\n\n{content}\n\nReturn only the transformed result."
        result = ask_ai(prompt)
        pyperclip.copy(result)
        return "Clipboard updated with transformed content."
    except Exception as e:
        return f"Clipboard error: {str(e)}"