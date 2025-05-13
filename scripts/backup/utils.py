
from datetime import datetime
import os

LOG_FILE = "logs.txt"

def log_action(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = f"[{timestamp}] {message}\n"
    log_path = os.path.join(os.path.dirname(__file__), LOG_FILE)
    with open(log_path, 'a') as f:
        f.write(entry)
