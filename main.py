#!/usr/bin/env python3
#
from nicegui import ui, app
from auth import login_screen, require_login
from vm_control import show_vm_dashboard
import extra_pages  # Import additional routes
import predictor
import monitor
import editar_vm
import criar_vm
import manage_host
import subprocess
import atexit
#
from fastapi import WebSocket
import clonar_ws
from clone_vm_ws import clone_vm_websocket
#
# Iniciar o proxy ao arrancar o kvm-manager
proxy_process = subprocess.Popen(
    ['python3', '/opt/kvm-manager/vm_Proxy.py'],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

# Garantir encerramento limpo ao sair
def encerrar_proxy():
    if proxy_process.poll() is None:
        print("🛑 A encerrar vm_proxy...")
        proxy_process.terminate()

atexit.register(encerrar_proxy)

@app.websocket('/ws/clone_vm')
async def handle_clone_vm(ws: WebSocket):
    source = ws.query_params['source']
    destino = ws.query_params['destino']
    await clone_vm_websocket(ws, source, destino)

def start_dash():
    show_vm_dashboard()

@ui.page('/')
@require_login
def index():
    with ui.header().classes('bg-slate-900 text-white'):
        with ui.row().classes('items-center justify-between w-full px-4'):
            ui.label('VIRTUNO  v1.21 - KVM Manager').classes('text-lg font-bold')
            ui.button('Return to Login', on_click=lambda: ui.navigate.to('/login')).props('outline')


            with ui.row().classes('gap-4'):
                ui.link('Host Monitor', '/Host_Monitor').classes('text-white')
                ui.link('Dashboard', '/').classes('text-white')
                ui.link('Logs', '/logs').classes('text-white')
                ui.link('Statistics', '/estatisticas').classes('text-white')
                ui.link('Monitoring', '/monitor').classes('text-white')
                ui.link('AI Forecast', '/previsao').classes('text-white')
                ui.link('Clone VM', '/clonar').classes('text-white')
                ui.link('Edit Virtual Entities', '/editar_vm').classes('text-white')
                ui.link('Create Virtual Entity', '/criar_vm').classes('text-white')
                #ui.link('Logout', '/login').classes('text-white')
#
    start_dash()
#
ui.run(title='VIRTUNO v1.21 - Easy KVM Manager Software', port=2000, dark=True, storage_secret='segredo_voltaire_123')
#
