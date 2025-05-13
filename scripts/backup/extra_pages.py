
from nicegui import ui, app
from database import get_log_history, get_vm_stats
from datetime import datetime
import json
from vm_control import get_connection

# Returns a list of all VMs
def get_vms():
    conn = get_connection()
    return conn.listAllDomains()

# Displays the action history page
@ui.page('/logs')
def show_logs():
    with ui.row().classes('items-center justify-between w-full p-2'):
      ui.label('Action History').classes('text-2xl p-2 text-white')
      ui.button('Return to Dashboard', on_click=lambda: ui.navigate.to('/')).props('outline')


    logs = get_log_history()

    for username, vm_name, action, timestamp in logs:
        action_color = 'green' if action == 'start' else 'red' if action == 'stop' else 'orange' if action == 'reboot' else 'blue'

        with ui.card().classes('m-2 bg-slate-800 text-white'):
            with ui.row().classes('justify-between items-center'):
                ui.label(f'👤 {username}')
                ui.label(f'💻 {vm_name}')
                ui.label(f'🕒 {timestamp.strftime("%Y-%m-%d %H:%M:%S")}')
                ui.label(f'⚙️ {action.upper()}').style(f'color:{action_color}; font-weight:bold')

# Displays statistics per virtual machine
@ui.page('/estatisticas')
def show_stats():
    with ui.row().classes('items-center justify-between w-full p-2'):
      ui.label('VM Statistics').classes('text-2xl p-2')
      ui.button('Return to Dashboard', on_click=lambda: ui.navigate.to('/')).props('outline')
    stats = get_vm_stats()
    data = {}
    for vm_name, action, count in stats:
        if vm_name not in data:
            data[vm_name] = {}
        data[vm_name][action] = count

    for vm, actions in data.items():
        chart = {
            'title': {'text': f'VM Statistics: {vm}'},
            'tooltip': {},
            'xAxis': {'type': 'category', 'data': list(actions.keys())},
            'yAxis': {'type': 'value'},
            'series': [{
                'data': list(actions.values()),
                'type': 'bar'
            }]
        }
        ui.echart(options=chart).classes('w-full h-64')

# VM clone page interface
@ui.page('/clonar')
def clone_vm_page():
    from vm_control import get_vms, clone_vm

    ui.label('VM Cloning').classes('text-2xl p-2')
    vm_names = [d.name() for d in get_vms()]
    selected = ui.select(vm_names, label='Select VM to clone')
    new_name = ui.input('New name for the cloned VM')
    progress_bar = ui.linear_progress().classes('w-full hidden')

    def do_clone():
        result = clone_vm(selected.value, new_name.value, progress_bar)
        ui.notify(result)

    ui.button('Clone', on_click=do_clone)
