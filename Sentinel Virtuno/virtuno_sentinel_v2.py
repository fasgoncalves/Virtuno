# -*- coding: utf-8 -*-
import subprocess
import time
from datetime import datetime

LOG_FILE = "/var/log/virtuno_sentinel.log"
NTFY_TOPIC = "Alertas"
INTERVAL = 30  # segundos
CPU_THRESHOLD = 50.0
SUSPECT_COMMANDS = ['wget', 'curl', 'nc', 'ncat', 'python3 -c', 'perl', 'base64', 'openssl enc']

def log_event(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {message}"
    with open(LOG_FILE, "a") as f:
        f.write(line + '\n')
    subprocess.run(['curl', '-d', line, f'https://ntfy.sh/{NTFY_TOPIC}'], stdout=subprocess.DEVNULL)

def get_ssh_sessions():
    result = subprocess.run(['who'], stdout=subprocess.PIPE, text=True)
    sessions = result.stdout.strip().split('\n')
    for session in sessions:
        if session:
            log_event(f"SSH ativa: {session}")

def get_external_connections():
    result = subprocess.run(['ss', '-tunap'], stdout=subprocess.PIPE, text=True)
    lines = result.stdout.strip().split('\n')[1:]
    for line in lines:
        if 'ESTAB' in line and '127.0.0.1' not in line and '::1' not in line:
            log_event(f"Conexão externa: {line}")

def get_processes_info():
    result = subprocess.run(['ps', 'axo', 'pid,uid,pcpu,comm,args'], stdout=subprocess.PIPE, text=True)
    lines = result.stdout.strip().split('\n')[1:]
    for line in lines:
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        pid, uid, cpu, comm, args = parts
        try:
            cpu = float(cpu)
        except ValueError:
            continue
        if cpu > CPU_THRESHOLD:
            log_event(f"Uso elevado de CPU: PID {pid}, UID {uid}, {cpu}%, CMD: {args}")
        for s in SUSPECT_COMMANDS:
            if s in args:
                log_event(f"Comando suspeito: PID {pid}, UID {uid}, CMD: {args}")
                break

def link_ip_to_pid():
    result = subprocess.run(['ss', '-tupn'], stdout=subprocess.PIPE, text=True)
    lines = result.stdout.strip().split('\n')[1:]
    for line in lines:
        if 'ESTAB' in line and '127.0.0.1' not in line:
            parts = line.split()
            if len(parts) > 6:
                state, recvq, sendq, local, remote, _, pid_info = parts[:7]
                log_event(f"PID/IP associado: {pid_info} ligado a {remote}")

def main():
    log_event("Virtuno Sentinel v2 iniciado.")
    while True:
        get_ssh_sessions()
        get_external_connections()
        get_processes_info()
        link_ip_to_pid()
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()