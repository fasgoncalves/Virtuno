
import os
import shutil
from datetime import datetime
import requests

BACKUP_DIR = '/var/backups/kvm'
VM_IMG_DIR = '/var/lib/libvirt/images'
NTFY_URL = 'http://softelabs.pt:9000/Alertas'

def perform_backup():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest_dir = os.path.join(BACKUP_DIR, timestamp)
    os.makedirs(dest_dir, exist_ok=True)

    try:
        for file in os.listdir(VM_IMG_DIR):
            if file.endswith('.qcow2'):
                src = os.path.join(VM_IMG_DIR, file)
                dst = os.path.join(dest_dir, file)
                shutil.copy2(src, dst)
        notify(f'Backup automático concluído com sucesso às {timestamp}')
    except Exception as e:
        notify(f'Erro no backup automático: {e}')

def notify(message):
    try:
        requests.post(NTFY_URL, data=message.encode('utf-8'))
    except:
        pass

if __name__ == '__main__':
    perform_backup()
