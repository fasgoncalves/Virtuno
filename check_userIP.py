from starlette.requests import Request
from nicegui import ui
import requests

@ui.page('/verifica_rede')
async def verifica_rede(request: Request):
    ip_forwarded = request.headers.get('x-forwarded-for', request.client.host)
    ip_publico = requests.get('https://api.ipify.org').text

    with ui.column().classes('p-4'):
        ui.label(f'🌐 IP Detetado do Cliente: {ip_forwarded}')
        ui.label(f'🛰️  IP Público do Servidor: {ip_publico}')

        if ip_forwarded == ip_publico:
            ui.label('🔓 Acesso Externo via IP Público').classes('text-green text-lg')
        else:
            ui.label('🔒 Acesso Local ou Interno').classes('text-orange text-lg')

        ui.button('🔙 Voltar à Dashboard', on_click=lambda: ui.navigate.to('/'))
~                                                                                    
~                                              
