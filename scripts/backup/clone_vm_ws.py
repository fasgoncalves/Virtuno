
import os
import libvirt
import xml.etree.ElementTree as ET
import pwd
import grp
import uuid
import asyncio
import json
from fastapi import WebSocket

async def clone_vm_websocket(websocket: WebSocket, source_name: str, new_name: str):
    await websocket.accept()
    try:
        conn = libvirt.open('qemu:///system')
        dom = conn.lookupByName(source_name)
        was_active = dom.isActive()
        if was_active:
            dom.suspend()

        xml = dom.XMLDesc()
        xml_new = xml.replace(source_name, new_name)
        root = ET.fromstring(xml)

        source_elem = root.find('./devices/disk/source')
        if source_elem is None or 'file' not in source_elem.attrib:
            await websocket.send_text(json.dumps({
                "status": "erro",
                "mensagem": "Disk not Found! "
            }))
            return

        disk_path = source_elem.attrib['file']
        disk_dir, disk_file = os.path.split(disk_path)
        ext = os.path.splitext(disk_file)[-1]
        new_disk_path = os.path.join(disk_dir, f"{new_name}{ext}")
        xml_new = xml_new.replace(disk_path, new_disk_path)

        new_uuid = str(uuid.uuid4())
        xml_new = xml_new.replace(
            f"<uuid>{root.find('uuid').text}</uuid>",
            f"<uuid>{new_uuid}</uuid>"
        )

        total_size = os.path.getsize(disk_path)
        copied = 0
        chunk_size = 1024 * 1024

        with open(disk_path, 'rb') as src, open(new_disk_path, 'wb') as dst:
            while True:
                chunk = src.read(chunk_size)
                if not chunk:
                    break
                dst.write(chunk)
                copied += len(chunk)
                percent = copied / total_size
                await websocket.send_text(json.dumps({
                    "status": "progress",
                    "valor": round(percent, 4)
                }))
                await asyncio.sleep(0.01)

        uid = pwd.getpwnam('libvirt-qemu').pw_uid
        gid = grp.getgrnam('kvm').gr_gid
        os.chown(new_disk_path, uid, gid)
        os.chmod(new_disk_path, 0o660)

        conn.defineXML(xml_new)
        if was_active:
            dom.resume()

        await websocket.send_text(json.dumps({
            "status": "concluido",
            "mensagem": f'VM "{new_name}" clonada com sucesso!'
        }))
        await websocket.close()

    except Exception as e:
        await websocket.send_text(json.dumps({
            "status": "error",
            "message": str(e)
        }))
        await websocket.close()
