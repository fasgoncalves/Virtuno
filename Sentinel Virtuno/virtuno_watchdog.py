# -*- coding: utf-8 -*-
import os
import time
import subprocess
import threading
from collections import defaultdict
from datetime import datetime
from inotify_simple import INotify, flags

# Diretórios a monitorizar
WATCH_DIRS = ['/home', '/var/www', '/srv']
# Extensões suspeitas
SUSPICIOUS_EXTENSIONS = ['.locked', '.encrypted', '.enc', '.ezz', '.cry']

# Parâmetros de detecção
MAX_EVENTS_PER_SECOND = 50
EVENT_WINDOW_SECONDS = 5

# Alertas via ntfy
NTFY_TOPIC = "Alertas"

# Logs
LOG_FILE = "/var/log/virtuno_watchdog.log"

event_counter = defaultdict(int)

def log_event(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')
    print(line)
    subprocess.run(['curl', '-d', line, f'https://ntfy.sh/{NTFY_TOPIC}'], stdout=subprocess.DEVNULL)

def monitor():
    inotify = INotify()
    watch_flags = flags.CREATE | flags.MODIFY | flags.MOVED_TO

    wd_map = {}
    for d in WATCH_DIRS:
        if os.path.exists(d):
            wd = inotify.add_watch(d, watch_flags, auto_add=True, recursive=True)
            wd_map[wd] = d

    while True:
        for event in inotify.read(timeout=1000):
            filename = event.name
            full_path = os.path.join(wd_map.get(event.wd, ''), filename)

            # Contagem de eventos
            ts = int(time.time())
            event_counter[ts] += 1

            # Verificar extensões suspeitas
            if any(filename.endswith(ext) for ext in SUSPICIOUS_EXTENSIONS):
                log_event(f"Ficheiro suspeito detectado: {full_path}")

def check_rate():
    while True:
        now = int(time.time())
        total = sum(event_counter[t] for t in range(now - EVENT_WINDOW_SECONDS + 1, now + 1))
        if total > MAX_EVENTS_PER_SECOND * EVENT_WINDOW_SECONDS:
            log_event(f"Alerta: {total} eventos em {EVENT_WINDOW_SECONDS}s — possível ataque tipo ransomware")
        time.sleep(1)

if __name__ == "__main__":
    log_event("Virtuno Watchdog iniciado.")
    threading.Thread(target=check_rate, daemon=True).start()
    monitor()