
import libvirt
import time
import mysql.connector
from datetime import datetime

def get_connection():
    return libvirt.open('qemu:///system')

def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='userdb',
        password='userpass',
        database='kvm_manager'
    )

def get_vms():
    conn = get_connection()
    return [d for d in conn.listAllDomains() if d.isActive()]

def get_cpu_usage(domain):
    t1 = domain.getCPUStats(True)[0]['cpu_time']
    time.sleep(0.1)
    t2 = domain.getCPUStats(True)[0]['cpu_time']
    delta = t2 - t1
    return delta / 1e9 * 100  # %

def get_ram_usage(domain):
    mem = domain.memoryStats()
    return mem.get('rss', 0) / 1024  # MB

def collect_and_store():
    conn = get_db()
    cursor = conn.cursor()
    for domain in get_vms():
        name = domain.name()
        cpu = get_cpu_usage(domain)
        ram = get_ram_usage(domain)
        now = datetime.now()
        cursor.execute("INSERT INTO usage_history (vm_name, timestamp, cpu, ram) VALUES (%s, %s, %s, %s)",
                       (name, now, cpu, ram))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    collect_and_store()
