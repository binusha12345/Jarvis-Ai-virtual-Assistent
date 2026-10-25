import threading
import time
import datetime
from engines.tts_engine import speak

_tasks = []

def add_reminder(message, minutes=None, time_str=None):
    if minutes:
        trigger = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
    elif time_str:
        try:
            today = datetime.datetime.now().date()
            t = datetime.datetime.strptime(time_str, "%H:%M").time()
            trigger = datetime.datetime.combine(today, t)
            if trigger < datetime.datetime.now():
                trigger += datetime.timedelta(days=1)
        except Exception:
            return "Invalid time format."
    else:
        return "No time specified."
    _tasks.append({"message": message, "trigger": trigger})
    return f"Reminder set for {trigger.strftime('%I:%M %p')}."

def _scheduler_loop():
    while True:
        now = datetime.datetime.now()
        for task in list(_tasks):
            if now >= task["trigger"]:
                speak(f"Reminder: {task['message']}")
                _tasks.remove(task)
        time.sleep(10)

def start_scheduler():
    t = threading.Thread(target=_scheduler_loop, daemon=True)
    t.start()