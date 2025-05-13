import libvirt
import threading
from nicegui import ui

@ui.page('/snapshots')
def page_snapshots():
    with ui.row().classes("w-full justify-between items-center bg-gray-200 p-3 shadow-md text-blue"):
        with ui.row().classes('items-center justify-between w-full p-2'):
            ui.label("📸 Virtuno - Snapshots das VMs").classes("text-lg font-bold")
            ui.button('Return to Dashboard', on_click=lambda: ui.navigate.to('/')).props('outline')

    ui.label('🧬 Criar Snapshot com libvirt').classes('text-xl text-blue-700')

    try:
        conn = libvirt.open("qemu:///system")
        nomes = [dom.name() for dom in conn.listAllDomains()]
        conn.close()
    except Exception as e:
        nomes = []
        ui.label(f'Erro ao obter VMs: {str(e)}').classes('text-red')

    origem = ui.select(nomes, label='Selecionar VM').classes('w-full')
    nome_snapshot = ui.input('Nome do Snapshot').classes('w-full')

    ui.label('📂 Snapshots existentes:').classes('text-md mt-4')
    lista_snapshots = ui.column().classes('w-full gap-1 p-2 border border-gray-300 rounded-md bg-white')

    resultado = ui.label('')
    progresso = ui.label('')
    barra = ui.linear_progress(show_value=False).classes('w-full my-2')
    barra.visible = False

    botao_voltar = ui.button('🔙 Voltar à Dashboard', on_click=lambda: ui.navigate.to('/')).props('color=secondary').classes('mt-4')
    botao_voltar.visible = False

    def restaurar_snapshot(vm_name, snapshot_name):
        try:
            conn = libvirt.open("qemu:///system")
            dom = conn.lookupByName(vm_name)
            snap = dom.snapshotLookupByName(snapshot_name)
            dom.revertToSnapshot(snap)
            conn.close()
            ui.notify(f'✅ Snapshot "{snapshot_name}" restaurado com sucesso.')
        except Exception as e:
            ui.notify(f'❌ Erro ao restaurar: {str(e)}', type='negative')

    def apagar_snapshot(vm_name, snapshot_name):
        try:
            conn = libvirt.open("qemu:///system")
            dom = conn.lookupByName(vm_name)
            snap = dom.snapshotLookupByName(snapshot_name)
            snap.delete()
            conn.close()
            ui.notify(f'🗑️ Snapshot "{snapshot_name}" apagado.')
            ui.timer(0.5, lambda: atualizar_lista_snapshots(vm_name), once=True)
        except Exception as e:
            ui.notify(f'❌ Erro ao apagar: {str(e)}', type='negative')

    def atualizar_lista_snapshots(vm_name):
        lista_snapshots.clear()
        try:
            conn = libvirt.open("qemu:///system")
            dom = conn.lookupByName(vm_name)
            snaps = dom.snapshotListNames()
            conn.close()
            for snap in snaps:
                with lista_snapshots:
                    with ui.row().classes('items-center gap-3'):
                        ui.icon('photo_camera').classes('text-blue-600')
                        ui.label(snap).classes('text-sm text-blue-900')
                        ui.button('🔁 Restaurar', on_click=lambda s=snap: restaurar_snapshot(vm_name, s)).props('dense flat').classes('text-xs text-green-800')
                        ui.button('🗑️ Apagar', on_click=lambda s=snap: apagar_snapshot(vm_name, s)).props('dense flat').classes('text-xs text-red')
        except Exception as e:
            with lista_snapshots:
                ui.label(f'⚠️ Erro: {str(e)}').classes('text-sm text-red')

    def criar_snapshot_thread(vm, nome):
        def tarefa():
            progresso.text = '⏳ A criar snapshot...'
            barra.set_visibility(True)
            barra.set_value(0.2)
            try:
                conn = libvirt.open("qemu:///system")
                dom = conn.lookupByName(vm)
                xml = f"<domainsnapshot><name>{nome}</name></domainsnapshot>"
                dom.snapshotCreateXML(xml, 0)
                barra.set_value(1.0)
                resultado.text = f'✅ Snapshot "{nome}" criado com sucesso.'
                progresso.text = '✅ Finalizado'
                conn.close()
                ui.timer(0.5, lambda: atualizar_lista_snapshots(vm), once=True)
                botao_voltar.visible = True
            except libvirt.libvirtError as e:
                resultado.text = f'❌ Erro Libvirt: {str(e)}'
                progresso.text = '❌ Falha'
                barra.set_value(0)

        threading.Thread(target=tarefa, daemon=True).start()

    def iniciar():
        criar_snapshot_thread(origem.value, nome_snapshot.value)

    origem.on('update:model-value', lambda _: atualizar_lista_snapshots(origem.value))

    ui.button('📸 Criar Snapshot Agora', on_click=iniciar).props('color=primary')
