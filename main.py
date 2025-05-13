#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#from auth import login_screen, require_login

from nicegui import ui, app
from vm_control import show_vm_dashboard
import extra_pages  # Import additional routes
import predictor
import monitor
import editar_vm
import criar_vm
import manage_host
from clone_libvirt import page_clone
from snapshots_vm import page_snapshots
from remover_vm import remover_vm_page
import subprocess
import atexit
import requests
#
#from starlette.requests import Request
from login2fa import configurar_login_2fa
from fastapi import Request
from fastapi.responses import RedirectResponse
import config

#  functions
# Iniciar o proxy ao arrancar o kvm-manager
proxy_process = subprocess.Popen(
    ['python3', '/opt/Virtuno/vm_Proxy.py'],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
# Garantir encerramento limpo ao sair
def encerrar_proxy():
    if proxy_process.poll() is None:
        print("🛑 A encerrar vm_proxy...")
        proxy_process.terminate()

atexit.register(encerrar_proxy)
#
# Indicar o domínio público quando estiveres atrás de um proxy
app.base_url = 'https://whats.softelabs.pt/'
tipo_IP = False
#
# Configuração do sistema de login 2FA
configurar_login_2fa({
    'db': {
        'host': 'localhost',
        'user': 'root',
        'password': 'passwdDb',
        'database': 'authusers'
    },
    'ntfy': {
        'url': 'ntfy-server.com',
        'user': 'username',
        'pass': 'passwd'
    },
    'rota_sucesso': '/mainPanel',
    'titulo_login': 'Acesso Seguro 2FA Virtuno V1.21',
    'tema': {
       'cor_primaria': '#3b82f6',   # Azul
       'cor_secundaria': '#9333ea',  # Magenta
    },
    'caminho_log': '/opt/Virtuno/logs/login2fa.log',
    'max_tentativa': 5
})

@ui.page('/mainPanel')
def painel(request: Request):
  try:
    user = request.cookies.get('user')
    ip_forwarded = request.headers.get('x-forwarded-for', request.client.host)
    ip_publico = requests.get('https://api.ipify.org').text
    global tipo_IP
    if ip_forwarded == ip_publico:
      config.tipo_IP = True
      tipo_IP = True
    else:
      config.tipo_IP = False
      tipo_IP = False
    print(f'REMOTE : {tipo_IP}')  # DEBUG
    print(f'COOKIES: {request.cookies}')  # DEBUG
    if user:
        return RedirectResponse(url='/dash', status_code=303)
  except Exception as e:
    print ("Erro ao obter informações da sessão : " + str(e))

@ui.page('/clonar')
def show_clonagem():
    page_clone()

@ui.page('/snapshots')
def mostrar_snapshots():
    page_snapshots()

@ui.page('/deletevm')
def removervms():
    remover_vm_page()

def start_dash():
    show_vm_dashboard()

@ui.page('/dash')
def page_main(request: Request):

    user = request.cookies.get('user')
    print(f'COOKIES: {request.cookies}')  # DEBUG

    with ui.header().classes('bg-slate-900 text-white'):
        with ui.row().classes('items-center justify-between w-full px-4'):
            ui.label('VIRTUNO  v1.21 - KVM Manager').classes('text-lg font-bold')
            ui.button('Return to Login', on_click=lambda: ui.navigate.to('/logout'))

            with ui.row().classes('gap-4'):
                ui.link('Host Monitor', '/Host_Monitor').classes('text-white')
                ui.link('Dashboard', '/').classes('text-white')
                ui.link('Logs', '/logs').classes('text-white')
                ui.link('Statistics', '/estatisticas').classes('text-white')
                ui.link('Monitoring', '/monitor').classes('text-white')
                ui.link('AI Forecast', '/previsao').classes('text-white')
                ui.link('Gestão Snapshots VM', '/snapshots').classes('text-white')
                ui.link('Clone VM', '/clonar').classes('text-white')
                ui.link('Edit Virtual Entities', '/editar_vm').classes('text-white')
                ui.link('Create Virtual Entity', '/criar_vm').classes('text-white')
                ui.link('Remove Virtual Entity', '/deletevm').classes('text-white')
#
    start_dash()
#
ui.run(title='VIRTUNO v1.21 - Easy KVM Manager Software', port=2000, dark=True, storage_secret='segredo_voltaire_123')
#
