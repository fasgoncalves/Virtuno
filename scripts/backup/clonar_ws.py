
from nicegui import ui
import asyncio
import json
import libvirt
import websockets

def get_vm_names():
    conn = libvirt.open('qemu:///system')
    return [dom.name() for dom in conn.listAllDomains()]

@ui.page('/clonar')
def clone_ws_page():
    with ui.row().classes('items-center justify-between w-full p-2'):
      ui.label('Virtual Machine Cloning with WebSocket Progress').classes('text-2xl text-white p-2')
      ui.button('Return to Dashboard', on_click=lambda: ui.navigate.to('/')).props('outline')

    ui.label('Virtual Machine Cloning with WebSocket Progress').classes('text-2xl text-white p-2')

    vm_names = get_vm_names()
    selected_vm = ui.select(vm_names, label='Choose the original VM').classes('w-full')
    destination = ui.input('New VM name').classes('w-full')

    progress = ui.linear_progress().classes('w-full mt-4 hidden')
    progress_label = ui.label('0%').classes('text-white text-right w-full')
    result = ui.label().classes('text-green-500 mt-2')

    async def start_cloning():
        progress.value = 0
        progress_label.text = '0%'
        progress.classes(remove='hidden')
        result.text = ''

        try:
            async with websockets.connect(f'ws://localhost:2000/ws/clone_vm?source={selected_vm.value}&destino={destination.value}') as ws:
                async for msg in ws:
                    data = json.loads(msg)
                    if data['status'] == 'progress':
                        progress.value = data['value']
                        progress_label.text = f'{int(data["value"] * 100)}%'
                    elif data['status'] == 'completed':
                        result.text = data['message']
                        progress.classes(add='hidden')
                        break
                    elif data['status'] == 'error':
                        result.text = f"Error: {data['message']}"
                        progress.classes(add='hidden')
                        break
        except Exception as e:
            result.text = f'Error connecting WebSocket: {e}'
            progress.classes(add='hidden')

    ui.button('Clone Machines', on_click=start_cloning).classes('mt-2')
