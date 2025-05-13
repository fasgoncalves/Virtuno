import libvirt
import os
import threading
from nicegui import ui
from xml.etree import ElementTree as ET

@ui.page('/remover_vm')
def remover_vm_page():
    with ui.row().classes("w-full justify-between items-center bg-red-50 p-3 shadow-md text-red-800"):
        with ui.row().classes('items-center justify-between w-full p-2'):
            ui.label("🗑️ Virtuno - Remover Máquinas Virtuais").classes("text-lg font-bold")
            ui.button('Voltar ao Dashboard', on_click=lambda: ui.navigate.to('/')).props('outline')

    ui.label('⚠️ Esta operação irá apagar a VM e o seu disco!').classes('text-md text-red')

    progresso = ui.linear_progress(show_value=False).classes('w-full my-2')
    progresso.visible = False
    mensagem = ui.label('')

    try:
        conn = libvirt.open("qemu:///system")
        nomes = [dom.name() for dom in conn.listAllDomains()]
        conn.close()
    except Exception as e:
        nomes = []
        ui.label(f'Erro ao obter VMs: {str(e)}').classes('text-red')

    vm_select = ui.select(nomes, label='Selecionar VM para apagar').classes('w-full')

    def apagar_vm(vm_name):
        def tarefa():
            progresso.visible = True
            progresso.set_value(0.1)
            try:
                conn = libvirt.open("qemu:///system")
                dom = conn.lookupByName(vm_name)

                if dom.isActive():
                    dom.destroy()
                    progresso.set_value(0.3)

                xml = dom.XMLDesc()
                tree = ET.fromstring(xml)
                path_disk = None
                for disk in tree.findall("./devices/disk"):
                    source = disk.find("source")
                    if source is not None and "file" in source.attrib:
                        path_disk = source.get("file")

                dom.undefine()
                progresso.set_value(0.6)

                if path_disk and os.path.exists(path_disk):
                    os.remove(path_disk)
                    progresso.set_value(1.0)
                    ui.notify(f'✅ VM "{vm_name}" removida com sucesso.')
                    mensagem.text = f'✅ VM "{vm_name}" removida com sucesso.'
                else:
                    mensagem.text = f'⚠️ VM removida, mas disco não encontrado.'
                conn.close()
            except Exception as e:
                mensagem.text = f'❌ Erro: {str(e)}'
        threading.Thread(target=tarefa, daemon=True).start()

    def confirmar_remocao():
        if not vm_select.value:
            mensagem.text = '⚠️ Selecione uma VM!'
            return

        dialog = ui.dialog()
        with dialog:
            with ui.card():
                ui.label(f'⚠️ Tem a certeza que deseja apagar a VM "{vm_select.value}"?')
                with ui.row():
                    ui.button('Sim', on_click=lambda: (dialog.close(), apagar_vm(vm_select.value))).props('color=negative')
                    ui.button('Não', on_click=dialog.close)
        dialog.open()

    ui.button('🗑️ Remover VM', on_click=confirmar_remocao).props('color=negative')
