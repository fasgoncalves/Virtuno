import libvirt
import shutil
import os
import threading
import xml.etree.ElementTree as ET
from nicegui import ui

def setPermissions(new_path):
    uid = pwd.getpwnam('libvirt-qemu').pw_uid
    gid = grp.getgrnam('kvm').gr_gid
    os.chown(new_path, uid, gid)
    os.chmod(new_path, 0o660)

def copiar_ficheiro_com_barra(origem, destino, barra, progresso_label):
    tamanho_total = os.path.getsize(origem)
    lido = 0
    bloco = 1024 * 1024 * 10  # 10MB

    with open(origem, 'rb') as src, open(destino, 'wb') as dst:
        while True:
            dados = src.read(bloco)
            if not dados:
                break
            dst.write(dados)
            lido += len(dados)
            progresso = min(lido / tamanho_total, 1.0)
            barra.set_value(progresso)
            progresso_label.text = f'📁 A copiar: {os.path.basename(origem)} ({progresso:.0%})'

def clonar_vm_python_thread(origem, destino, resultado_label, progresso_label, barra, botao_voltar):
    def tarefa():
        with resultado_label, progresso_label, barra, botao_voltar:
            progresso_label.text = '⏳ Clonagem em curso...'
            barra.visible = True
            barra.set_value(0.1)
            try:
                conn = libvirt.open("qemu:///system")
                if not conn:
                    resultado_label.text = '❌ Falha ao ligar à libvirt'
                    return

                dom = conn.lookupByName(origem)
                xml = dom.XMLDesc()
                tree = ET.fromstring(xml)

                name_elem = tree.find('name')
                name_elem.text = destino

                uuid_elem = tree.find('uuid')
                if uuid_elem is not None:
                    tree.remove(uuid_elem)

                disk_paths = []
                progress_step = 0.7  # Ajustável para simular progresso

                for i, disk in enumerate(tree.findall(".//disk[@device='disk']")):
                    source = disk.find('source')
                    if source is not None and 'file' in source.attrib:
                        original_path = source.attrib['file']
                        dir_path, filename = os.path.split(original_path)
                        new_path = os.path.join(dir_path, f"{destino}-{filename}")
                        progresso_label.text = f'📁 A copiar disco: {filename}...'
                        barra.set_value((i + 1) * (progress_step / len(tree.findall(".//disk[@device='disk']"))))

                        copiar_ficheiro_com_barra(original_path, new_path, barra, progresso_label)
                        source.set('file', new_path)
                        disk_paths.append((original_path, new_path))

                new_xml = ET.tostring(tree, encoding='unicode')
                conn.defineXML(new_xml)
                barra.set_value(1.0)
                resultado_label.text = f'✅ VM clonada com sucesso! Discos copiados: {disk_paths}'
                progresso_label.text = '✅ Finalizado'
                botao_voltar.visible = True

            except libvirt.libvirtError as e:
                resultado_label.text = f'❌ Erro Libvirt: {str(e)}'
                progresso_label.text = '❌ Erro'
                barra.set_value(0)
            except Exception as e:
                resultado_label.text = f'⚠️ Erro geral: {str(e)}'
                progresso_label.text = '⚠️ Interrompido'
                barra.set_value(0)
            finally:
                if conn:
                    conn.close()

    threading.Thread(target=tarefa, daemon=True).start()

@ui.page('/clonar')
def page_clone():
    with ui.row().classes("w-full justify-between items-center bg-gray-200 p-3 shadow-md text-blue"):
        with ui.row().classes('items-center justify-between w-full p-2'):
           ui.label("📊 Virtuno (c) - Clone KVM Guests").classes("text-lg font-bold")
           ui.button('Return to Dashboard', on_click=lambda: ui.navigate.to('/')).props('outline')


    ui.label('🧬 Clonagem Direta com libvirt (com progresso)').classes('text-xl text-blue-700')

    try:
        conn = libvirt.open("qemu:///system")
        nomes = [dom.name() for dom in conn.listAllDomains()]
        conn.close()
    except Exception as e:
        nomes = []
        ui.label(f'Erro ao obter VMs: {str(e)}').classes('text-red')

    origem = ui.select(nomes, label='VM de origem').classes('w-full')
    destino = ui.input('Nome da nova VM').classes('w-full')

    progresso = ui.label('')
    resultado = ui.label('')
    barra = ui.linear_progress(show_value=False).classes('w-full my-2')
    barra.visible = False

    botao_voltar = ui.button('🔙 Voltar à Dashboard', on_click=lambda: ui.navigate.to('/')).props('color=secondary').classes('mt-4')
    botao_voltar.visible = False

    def iniciar():
        clonar_vm_python_thread(origem.value, destino.value, resultado, progresso, barra, botao_voltar)

    ui.button('🚀 Clonar Agora', on_click=iniciar).props('color=primary')
