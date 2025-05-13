# -*- coding: utf-8 -*-
import os
import hashlib
import json
import time
from datetime import datetime
import subprocess

# Ficheiros a monitorizar
FILES_TO_MONITOR = [
    '/etc/ssh/sshd_config',
    '/etc/sudoers',
]

# Caminho para ficheiro de hashes
BASELINE_FILE = '/var/lib/virtuno_configguard_hashes.json'
LOG_FILE = '/var/log/virtuno_configguard.log'
NTFY_TOPIC = 'Alertas'
CHECK_INTERVAL = 60  # segundos

def calculate_hash(path):
    try:
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        log_event(f"Erro ao calcular hash de {path}: {e}")
        return None

def load_baseline():
    if os.path.exists(BASELINE_FILE):
        with open(BASELINE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_baseline(hashes):
    os.makedirs(os.path.dirname(BASELINE_FILE), exist_ok=True)
    with open(BASELINE_FILE, 'w') as f:
        json.dump(hashes, f, indent=2)

def log_event(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {message}"
    with open(LOG_FILE, "a") as f:
        f.write(line + '\n')
    subprocess.run(['curl', '-d', line, f'https://ntfy.sh/{NTFY_TOPIC}'], stdout=subprocess.DEVNULL)

def check_files():
    current_hashes = {path: calculate_hash(path) for path in FILES_TO_MONITOR}
    baseline = load_baseline()

    for path, current_hash in current_hashes.items():
        if path in baseline:
            if current_hash != baseline[path]:
                log_event(f"Alteração detectada em {path}!")
        else:
            log_event(f"Novo ficheiro monitorizado: {path}")
    save_baseline(current_hashes)

def main():
    log_event("Virtuno ConfigGuard iniciado.")
    while True:
        check_files()
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()