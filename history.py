# history.py
import os
import json
from datetime import datetime

HISTORY_DIR = "chat_histories"

def ensure_history_dir():
    os.makedirs(HISTORY_DIR, exist_ok=True)

def get_all_histories():
    ensure_history_dir()
    histories = []
    for fname in os.listdir(HISTORY_DIR):
        if fname.endswith(".json"):
            time_str = fname.replace(".json", "")
            histories.append((time_str, os.path.join(HISTORY_DIR, fname)))
    histories.sort(key=lambda x: x[0], reverse=True)
    return histories

def load_history(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []   # 文件损坏时返回空列表

def save_history(messages, first_question_time_str=None):
    ensure_history_dir()
    if first_question_time_str is None:
        first_question_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filepath = os.path.join(HISTORY_DIR, f"{first_question_time_str}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    return first_question_time_str, filepath

def delete_history(time_str):
    filepath = os.path.join(HISTORY_DIR, f"{time_str}.json")
    if os.path.exists(filepath):
        os.remove(filepath)