# -*- coding: utf-8 -*-
import subprocess
import requests
import time
from datetime import datetime

LOG_FILE = "/var/log/virtuno_sentinel.log"
NTFY_TOPIC = "Alertas"
INTERVAL = 60  # segundos

CPU_THRESHOLD = 50.0
SUSPECT_COMMANDS = ['wget', 'curl', 'nc', 'ncat', 'python3 -c', 'perl', 'base64', 'openssl enc']
ALLOWED_COUNTRIES = ['PT', 'FR', 'ES']
WHITELIST_IPS = []

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
    ext_ips = set()
    for line in lines:
        if 'ESTAB' in line and '127.0.0.1' not in line and '::1' not in line:
            log_event(f"Conexão externa: {line}")
            parts = line.split()
            if len(parts) >= 5:
                remote = parts[4]
                ip = remote.split(':')[0]
                if ip and ip not in WHITELIST_IPS:
                    ext_ips.add(ip)
    return ext_ips

def check_suspicious_processes():
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
                pid_info = parts[6]
                remote = parts[4]
                log_event(f"PID/IP associado: {pid_info} ligado a {remote}")

def get_country(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        data = res.json()
        return data.get('countryCode'), data.get('isp')
    except:
        return None, None

def block_ip(ip):
    subprocess.run(['iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'])
    log_event(f"IP {ip} bloqueado por origem geográfica.")

def geo_check_ips(ips):
    for ip in ips:
        country, isp = get_country(ip)
        if not country:
            continue
        if country not in ALLOWED_COUNTRIES:
            log_event(f"IP {ip} ({isp}) de país {country} não autorizado.")
            block_ip(ip)

def main():
    log_event("Virtuno Sentinel v2 + GeoFence iniciado.")
    while True:
        get_ssh_sessions()
        ext_ips = get_external_connections()
        check_suspicious_processes()
        link_ip_to_pid()
        geo_check_ips(ext_ips)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()