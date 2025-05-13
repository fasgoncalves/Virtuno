# -*- coding: utf-8 -*-
import subprocess
import requests
import time
from datetime import datetime

LOG_FILE = "/var/log/virtuno_geofence.log"
NTFY_TOPIC = "Alertas"
INTERVAL = 60  # segundos
ALLOWED_COUNTRIES = ['PT', 'FR', 'ES']  # Países permitidos
WHITELIST_IPS = []  # IPs a ignorar

def log_event(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {message}"
    with open(LOG_FILE, "a") as f:
        f.write(line + '\n')
    subprocess.run(['curl', '-d', line, f'https://ntfy.sh/{NTFY_TOPIC}'], stdout=subprocess.DEVNULL)

def get_established_ips():
    result = subprocess.run(['ss', '-tunap'], stdout=subprocess.PIPE, text=True)
    lines = result.stdout.strip().split('\n')[1:]
    ips = set()
    for line in lines:
        if 'ESTAB' in line and '127.0.0.1' not in line:
            parts = line.split()
            if len(parts) >= 5:
                remote = parts[4]
                ip = remote.split(':')[0]
                if ip and ip not in WHITELIST_IPS:
                    ips.add(ip)
    return list(ips)

def get_country(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        data = res.json()
        return data.get('countryCode'), data.get('isp')
    except:
        return None, None

def block_ip(ip):
    subprocess.run(['iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'])
    log_event(f"IP {ip} bloqueado por geofencing.")

def main():
    log_event("Virtuno GeoFence iniciado.")
    while True:
        ips = get_established_ips()
        for ip in ips:
            country, isp = get_country(ip)
            if not country:
                continue
            if country not in ALLOWED_COUNTRIES:
                log_event(f"IP {ip} de país {country} ({isp}) não autorizado.")
                block_ip(ip)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()