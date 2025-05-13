
import os
import libvirt
import xml.etree.ElementTree as ET
import pwd
import grp
import uuid
import subprocess
import platform
from typing import Optional
from nicegui import ui
import threading
import time

gl_device = False
estado_consola = {'terminou': False, 'vm': ''}
#
async def detect_Mobile():
        global gl_device
        gl_device = await ui.run_javascript('/iPhone|iPad|iPod|Android/i.test(navigator.userAgent);')
        print(" Is Device : " + str(gl_device))
#
def get_connection():
    return libvirt.open('qemu:///system')

def get_vms():
    conn = get_connection()
    return conn.listAllDomains()

def get_vm_state_color(state):
    return {
        1: 'green',   # running
        3: 'yellow',  # paused
        5: 'red'      # shut off
    }.get(state, 'gray')

def show_vm_dashboard():
    #
    global gl_device
    ui.label('Bem-vindo ao KVM Manager')
    ui.timer(1, detect_Mobile, once=True)

    conn = get_connection()
    domains = conn.listAllDomains()

    ui.label('Virtual Machine Dashboard').classes('text-2xl text-white p-2')

    for domain in domains:
        name = domain.name()
        state, _ = domain.state()

        with ui.card().classes('bg-gray-900 text-white p-4 mb-4'):
            # Primeira linha: nome e semáforo
            with ui.row().classes('items-center gap-4'):
                ui.icon('circle').style(f'color: {get_vm_state_color(state)}')
                ui.label(name).classes('text-lg')

            # Segunda linha: botões
            with ui.row().classes('gap-2 mt-2'):
                ui.button('Start', on_click=lambda n=name: start_vm(n)).props('outline color=green')
                ui.button('Stop', on_click=lambda n=name: stop_vm(n)).props('outline color=red')
                ui.button('Reboot', on_click=lambda n=name: reboot_vm(n)).props('outline color=orange')
                ui.button('Shutdown', on_click=lambda n=name: shutdown_vm(n)).props('outline color=gray')
                ui.button('Consola', on_click=lambda n=name: start_console(n)).props('outline')
#
def start_console(vm_name):
    global gl_device

    if not vm_esta_ativa(vm_name):
        print(f"⚠️ A VM '{vm_name}' não está ativa.")
        ui.notify(f'⚠️ A VM "{vm_name}" não está ativa.', type='warning')
        return

    print (" Is Mobile : " + str(gl_device))
    if gl_device:
        painel_background(vm_name)
    else:
        open_console_vm(vm_name)

def painel_background(vm_name):

    ui.label('🖥️  Painel de Consola de VMs')

    def exec_console_background(vm):
        print(f"🧪 A iniciar subprocesso para: {vm}")
        try:
            resultado = subprocess.check_output(
                ['/opt/kvm-manager/scripts/browser_console.sh', vm],
                stderr=subprocess.STDOUT
            )
            output = resultado.decode().strip()
            print(output)

            # Marca como concluído para a UI principal notificar
            estado_consola['terminou'] = True
            estado_consola['vm'] = vm
        except subprocess.CalledProcessError as e:
            print("Erro ao executar o script:", e.output.decode())

    def abrir_console(vm):
        ui.notify(f'🎬 A iniciar consola para: {vm}')
        threading.Thread(target=exec_console_background, args=(vm,), daemon=True).start()

    # Botão
    ui.button('Abrir Consola para Terminal Unix', on_click=lambda: abrir_console(vm_name))

    # Timer para verificar estado e interagir com UI
    def verificar_estado():
        if estado_consola['terminou']:
            vm = estado_consola['vm']
            ui.notify(f'✅ Consola iniciada para: {vm}')
            ui.run_javascript(f"window.open('http://mgr.fragmentoscaos.eu', '_blank')")
            estado_consola['terminou'] = False

    ui.timer(1.0, verificar_estado)
#
def start_vm(name):
    conn = get_connection()
    dom = conn.lookupByName(name)
    if not dom.isActive():
        dom.create()

def stop_vm(name):
    conn = get_connection()
    dom = conn.lookupByName(name)
    if dom.isActive():
        dom.destroy()

def reboot_vm(name):
    conn = get_connection()
    dom = conn.lookupByName(name)
    if dom.isActive():
        dom.reboot()

def shutdown_vm(name):
    conn = get_connection()
    dom = conn.lookupByName(name)
    if dom.isActive():
        dom.shutdown()

def clone_vm(source_name, new_name, progress_bar):
    try:
        conn = get_connection()
        dom = conn.lookupByName(source_name)
        was_active = dom.isActive()

        if was_active:
            dom.suspend()

        xml = dom.XMLDesc()
        xml_new = xml.replace(source_name, new_name)

        root = ET.fromstring(xml)
        new_uuid = str(uuid.uuid4())
        xml_new = xml_new.replace(
           f"<uuid>{root.find('uuid').text}</uuid>",
           f"<uuid>{new_uuid}</uuid>"
        )

        source_elem = root.find('./devices/disk/source')
        if source_elem is None or 'file' not in source_elem.attrib:
            return 'Error: Path not Found in the original XML.'
        disk_path = source_elem.attrib['file']

        disk_dir, disk_file = os.path.split(disk_path)
        ext = os.path.splitext(disk_file)[-1]
        new_disk_path = os.path.join(disk_dir, f"{new_name}{ext}")
        xml_new = xml_new.replace(disk_path, new_disk_path)

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
                progress_bar.value = copied / total_size

        uid = pwd.getpwnam('libvirt-qemu').pw_uid
        gid = grp.getgrnam('kvm').gr_gid
        os.chown(new_disk_path, uid, gid)
        os.chmod(new_disk_path, 0o660)

        conn.defineXML(xml_new)

        if was_active:
            dom.resume()

        return f'VM "{new_name}"VM Cloned with Success !'
    except Exception as e:
        return f'Error on cloning VM: {e}'

def open_console_vm(nome_vm):
    print (" VM = " + nome_vm)
    if not vm_esta_ativa(nome_vm):
            print(f"⚠️ A VM '{nome_vm}' não está ativa.")
            return
    else:
        port = obter_spice_porta(nome_vm)
        if not port:
            ui.notify(f'❌ Erro: Não foi possível obter a porta SPICE da VM {nome_vm}', type='negative')
            return

        vv_content = f"""[virt-viewer]
         type=spice
         host=localhost
         port={port}
         title=SPICE Console - {nome_vm}
         """
        caminho_vv = f"/tmp/{nome_vm}.vv"
        with open(caminho_vv, "w") as f:
            f.write(vv_content)

        # Verifica se é ambiente com GUI (Linux + DISPLAY definido)
        is_gui = platform.system() == "Linux" and os.environ.get("DISPLAY")

        if is_gui:
            try:
                # Garante que estamos na sessão gráfica correta
                env = os.environ.copy()
                os.environ["DISPLAY"] = ":1"
                env["NO_AT_BRIDGE"] = "1"
                env["DISPLAY"] = os.environ.get("DISPLAY", ":1")
                url = f"spice://localhost:{port}"
                print(f"[DEBUG] Lançando remote-viewer com URL: {url}")
                subprocess.Popen(
                ["sudo", "-u", "admin", "remote-viewer", url],
                 env=env,
                 stdout=subprocess.DEVNULL,
                 stderr=subprocess.DEVNULL
                )
                ui.notify(f'🖥️  A abrir remote-viewer para {nome_vm}...', type='positive')
            except Exception as e:
                ui.notify(f'⚠️ Erro ao abrir remote-viewer: {e}', type='warning')
        else:
            ui.download(caminho_vv, filename=f'{nome_vm}.vv')
            ui.notify(f'💾 Ficheiro {nome_vm}.vv disponível para download.', type='info')
#
def obter_spice_porta(nome_vm):
    try:
        xml = subprocess.check_output(['virsh', 'dumpxml', nome_vm], stderr=subprocess.STDOUT).decode()

        if not xml.strip():
            print(f"[obter_spice_porta] XML vazio para VM: {nome_vm}")
            return None

        root = ET.fromstring(xml)
        graphics_elements = root.findall(".//graphics[@type='spice']")

        for graphics in graphics_elements:
            porta = graphics.get('port')
            if porta and porta.isdigit():
                print(f"[obter_spice_porta] Porta SPICE obtida para {nome_vm}: {porta}")
                return int(porta)

        print(f"[obter_spice_porta] Elemento <graphics type='spice'> não encontrado na VM {nome_vm}")
        return None

    except subprocess.CalledProcessError as e:
        print(f"[obter_spice_porta] Erro ao obter XML da VM {nome_vm}: {e.output.decode()}")
        return None
    except ET.ParseError as e:
        print(f"[obter_spice_porta] Erro ao fazer parsing do XML: {e}")
        return None

def vm_esta_ativa(nome_vm):
    try:
        estado = subprocess.check_output(['virsh', 'domstate', nome_vm]).decode().strip()
        print("O ESTADO DA MAQUINA É " + estado)
        return estado == 'running'
    except Exception as e:
        print(f"[vm_esta_ativa] Erro: {e}")
        return False
# vm_control.py (adicionar ao final do ficheiro ou integrar na secção de botões e consola)


def abrir_shell_remota(nome_vm):
    try:
        ui.label(f'A shell remota está aberta para {vm}.').classes('text-orange')
        print ("VM____ " + nome_vm)
        resultado = subprocess.check_output(["/opt/kvm-manager/scripts/browser_console.sh", nome_vm], stderr=subprocess.STDOUT)
        output = resultado.decode().strip()
        print(output)
        # Abrir a shell remota via browser
        time.sleep (3)
        ui.run_javascript(f"window.open('http://mgr.fragmentoscaos.eu', '_blank')")
    except subprocess.CalledProcessError as e:
        print("Erro ao executar o script:", e.output.decode())
#
gl_device = detect_Mobile()
#
