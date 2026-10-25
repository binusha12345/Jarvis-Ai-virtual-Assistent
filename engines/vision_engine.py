import os
import time
import base64
import ollama
import mss
from core.config import SCREENSHOT_DIR, VISION_MODEL, SYS_CONFIG

def capture_screen():
    try:
        filepath = os.path.join(SCREENSHOT_DIR, f"scr_{int(time.time())}.png")
        with mss.mss() as sct:
            sct.shot(output=filepath)
        return filepath
    except Exception:
        return None

def capture_webcam():
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        time.sleep(0.5)
        ret, frame = cap.read()
        cap.release()
        if ret:
            filepath = os.path.join(SCREENSHOT_DIR, f"cam_{int(time.time())}.png")
            cv2.imwrite(filepath, frame)
            return filepath
    except Exception:
        pass
    return None

def analyze_image(image_path, question="What do you see?"):
    try:
        with open(image_path, 'rb') as f:
            img_b64 = base64.b64encode(f.read()).decode('utf-8')
        response = ollama.chat(
            model=VISION_MODEL,
            messages=[{
                "role": "user",
                "content": question,
                "images": [img_b64]
            }],
            options={"num_predict": 150}
        )
        return response['message']['content'].strip()
    except Exception as e:
        return f"Vision analysis failed, {SYS_CONFIG['user_title']}: {str(e)[:60]}"

def see_screen(question="Describe what is on my screen"):
    path = capture_screen()
    if not path:
        return "Screen capture failed."
    return analyze_image(path, question)

def see_camera(question="What or who do you see?"):
    path = capture_webcam()
    if not path:
        return "Webcam capture failed."
    return analyze_image(path, question)