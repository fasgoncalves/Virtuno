
import mysql.connector
from datetime import datetime

def get_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='yakarais',
        database='kvm_manager'
    )

def log_action(user, vm_name, action):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (username, vm_name, action, timestamp) VALUES (%s, %s, %s, %s)", (user, vm_name, action, datetime.now()))
    conn.commit()
    conn.close()

def update_stats(vm_name, action):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stats (vm_name, action, count) VALUES (%s, %s, 1) "
                   "ON DUPLICATE KEY UPDATE count = count + 1", (vm_name, action))
    conn.commit()
    conn.close()

def get_log_history():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, vm_name, action, timestamp FROM logs ORDER BY timestamp DESC")
    logs = cursor.fetchall()
    conn.close()
    return logs

def get_vm_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT vm_name, action, count FROM stats")
    stats = cursor.fetchall()
    conn.close()
    return stats
