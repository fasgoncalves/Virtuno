
from nicegui import ui
import libvirt
import os
import subprocess
from lxml import etree
from utils import log_action
from datetime import datetime

ISO_DIR = "/var/lib/libvirt/images/isos"
VM_STORAGE_DIR = "/var/lib/libvirt/images"

def get_connection():
    return libvirt.open("qemu:///system")

def listar_isos():
    if not os.path.isdir(ISO_DIR):
        return []
    return [f for f in os.listdir(ISO_DIR) if f.endswith(".iso")]

@ui.page('/criar_vm')
def criar_vm_form():
    ui.label("Create a New Virtual Machine").classes("text-2xl text-white")

    nome = ui.input("VM Name").classes("w-full")
    cpu = ui.input("CPUs", value="2").classes("w-full").props("type=number")
    ram = ui.input("RAM (MB)", value="2048").classes("w-full").props("type=number")
    disk = ui.input("Disk Size (GB)", value="20").classes("w-full").props("type=number")

    iso_file = ui.select(listar_isos(), label="Choose ISO").classes("w-full")
    autostart = ui.checkbox("Autostart").classes("mt-4")

    ui.button("Create VM", on_click=lambda: criar_vm(
        nome.value, int(cpu.value), int(ram.value), int(disk.value),
        iso_file.value, autostart.value
    )).classes("mt-4 bg-green-600 text-white")

def criar_vm(name, vcpus, ram_mb, disk_gb, iso_filename, autostart=False):
    try:
        conn = get_connection()

        ram_kb = ram_mb * 1024
        disk_path = os.path.join(VM_STORAGE_DIR, f"{name}.qcow2")
        subprocess.run([
            "qemu-img", "create", "-f", "qcow2", disk_path, f"{disk_gb}G"
        ], check=True)

        iso_path = os.path.join(ISO_DIR, iso_filename)

        xml = f"""
        <domain type='kvm'>
          <name>{name}</name>
          <memory unit='KiB'>{ram_kb}</memory>
          <vcpu>{vcpus}</vcpu>
          <os>
            <type arch='x86_64'>hvm</type>
            <boot dev='cdrom'/>
          </os>
          <devices>
            <disk type='file' device='disk'>
              <driver name='qemu' type='qcow2'/>
              <source file='{disk_path}'/>
              <target dev='vda' bus='virtio'/>
            </disk>
            <disk type='file' device='cdrom'>
              <driver name='qemu' type='raw'/>
              <source file='{iso_path}'/>
              <target dev='hdc' bus='ide'/>
              <readonly/>
            </disk>
            <interface type='network'>
              <source network='default'/>
              <model type='virtio'/>
            </interface>
               <graphics type='spice' port='-1' autoport='yes' listen='0.0.0.0'>
                 <listen type='address' address='0.0.0.0'/>
              </graphics>

          </devices>
        </domain>
        """

        domain = conn.defineXML(xml)
        if autostart:
            domain.setAutostart(1)
        domain.create()

        log_action(f"Created VM {name} with ISO {iso_filename}")
        ui.notify(f"VM '{name}' created successfully & Starting...!", type='positive')
        ui.navigate.to("/") 
    except Exception as e:
        ui.notify(f"Error: {e}", type='negative')
        log_action(f"Error creating VM {name}: {e}")
