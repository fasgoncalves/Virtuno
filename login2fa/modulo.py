
# -*- coding: utf-8 -*-
from nicegui import ui
import mysql.connector
import bcrypt
import random
import string
import time
import os
import requests
import logging
from fastapi import Request
from fastapi.responses import RedirectResponse, HTMLResponse
from urllib.parse import parse_qs, urlparse

# Logger global
logging.basicConfig(
    filename='/var/log/Virtuno/login2fa.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

ulogging = logging.getLogger("Login2fa")

auth_tokens = {}
config = {}

MAX_TENTATIVAS = 5
TEMPO_BLOQUEIO = 300  # segundos
auth_tokens = {}  # username -> (token, timestamp)
tentativas_login = {}
#

def configurar_login_2fa(opcoes: dict):
    global config
    config = opcoes
    #
    ui.page('/')(pagina_login)
    ui.page('/token')(pagina_token)
    ui.page('/validar_token')(pagina_validar_token)
    ui.page('/logout')(pagina_logout)
    #
    #
def escrever_log(mensagem, nivel='info'):
    global ulogging
    if nivel == 'info':
        ulogging.info(mensagem)
    elif nivel == 'warning':
        ulogging.warning(mensagem)
    elif nivel == 'error':
        ulogging.error(mensagem)
    elif nivel == 'debug':
        ulogging.debug(mensagem)
    elif nivel == 'critical':
        ulogging.critical(mensagem)

def obter_ip_real(request: Request):
    x_forwarded_for = request.headers.get('x-forwarded-for')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.client.host
    return ip

def get_user(username):
    conn = mysql.connector.connect(**config['db'])
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def generate_token(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def send_token_ntfy(topic, token):
    logging.info ( "params : " + str(topic) + " - " + str(token))
    url = f"{config['ntfy']['url'].rstrip('/')}/{topic}"
    headers = {"Title": "Token de Acesso", "Priority": "high"}
    try:
        message = f"O seu código é: {token}"
        requests.post(url, headers=headers, data=message.encode("utf-8"),
                      auth=(config['ntfy']['user'], config['ntfy']['pass']))
        if ulogging:
          ulogging.info(f'Token Enviado com Sucesso')
    except Exception as e:
        if ulogging:
          ulogging.info(f'Erro no envio do Token!')
        print(f"Erro ao enviar notificação: {e}")

def send_msg_ntfy(topic, token, msg):
    url = f"{config['ntfy']['url'].rstrip('/')}/{topic}"
    headers = {"Title": "Warning Acess", "Priority": "high"}
    try:
        message = f"Mensagem Aviso: {msg}"
        requests.post(url, headers=headers, data=message.encode("utf-8"),
                      auth=(config['ntfy']['user'], config['ntfy']['pass']))
        ulogging.info(f'Mensagem Warning Enviada com Sucesso')
    except Exception as e:
        ulogging.info(f'Erro no envio de Mensage Warning:{e}')
        print(f"Erro ao enviar notificação: {e}")

def is_token_valid(username, token):
    if username in auth_tokens:
        stored_token, timestamp = auth_tokens[username]
        if stored_token == token and time.time() - timestamp <= 120:
            return True
    return False

def pagina_login(request: Request):
    user = request.cookies.get('user')
    ip = obter_ip_real(request)
    if user:
        return RedirectResponse(url=config['rota_sucesso'], status_code=303)

    escrever_log(f'Acesso para login o com IP : {ip}')
    tema = config.get('tema', {})
    cor_primaria = tema.get('cor_primaria', '#3b82f6')
    cor_secundaria = tema.get('cor_secundaria', '#9333ea')
    titulo = config.get('titulo_login', 'Bem-vindo! Inicie sessão')
    MAX_TENTATIVAS = config.get('max_tentativas', 5)
    TEMPO_BLOQUEIO = 300

    ui.query('body').style(f'''
        background: {cor_primaria};
        font-family: 'Segoe UI', sans-serif;
    ''')

    with ui.column().classes('absolute-center items-center justify-center').style('height: 100vh;'):
        with ui.card().style(f'''
            background-color: #000;
            border: 1px solid {cor_secundaria};
            border-radius: 12px;
            width: 400px;
            box-shadow: 0 0 12px {cor_secundaria};
        '''):
            ui.label(titulo).classes('text-xl text-white text-center')
            username_input = ui.input('Utilizador').classes('w-full mt-2 text-white').style('background-color: #1f1f1f; color: white;')
            password_input = ui.input('Palavra-passe', password=True).classes('w-full mt-2 text-white').style('background-color: #1f1f1f; color: white;')

            def login():
                user = get_user(username_input.value)
                agora = time.time()
                tentativas, timestamp, aviso_enviado  = tentativas_login.get(username_input.value, (0, 0, False))
                if user and bcrypt.checkpw(password_input.value.encode(), user['password_hash'].encode()):
                    token = generate_token()
                    auth_tokens[user['username']] = (token, time.time())
                    send_token_ntfy(user['ntfy_topic'], token)
                    ui.notify('Token enviado!')
                    ui.navigate.to(f'/token?user={user["username"]}')
                    escrever_log(f'Token send to user :  {user}')
                    tentativas_login.pop(username_input.value, None)
                else:
                    agora = time.time()
                    tentativas += 1  # <-- Aqui incrementamos
                    tentativas_login[username_input.value] = (tentativas, agora, aviso_enviado) 
                    ui.notify('Credenciais inválidas', type='negative')
                    if tentativas >= MAX_TENTATIVAS and agora - timestamp < TEMPO_BLOQUEIO:
                        ui.notify('Conta bloqueada! Aguarde 5 minutos.', type='negative')
                        escrever_log(f'USER BLOQUEADO POR 5 MINUTOS : {user} - IP: {ip}')
                        if not aviso_enviado:
                           send_msg_ntfy(user['ntfy_topic'], user, f'Conta bloqueada para {user}')
                           aviso_enviado = True
                    else:
                        escrever_log(f'TENTATIVA FALHADA: MaxTry : {MAX_TENTATIVAS}, User :  {user} - IP: {ip}')
                    tentativas_login[username_input.value] = (tentativas, agora, aviso_enviado)
            ui.button('Entrar', on_click=login).classes('w-full mt-4').style(f'background-color: {cor_secundaria}; color: white')

def pagina_token(request: Request):
    query = parse_qs(urlparse(str(request.url)).query)
    username = query.get('user', [None])[0]
    if not username:
        ui.label('Utilizador não especificado').classes('text-red-600')
        return

    with ui.card().classes('w-96 shadow-xl mx-auto mt-20'):
        ui.label('Introduza o código').classes('text-lg')
        token_input = ui.input('Código').classes('w-full')

        def validar():
            ui.navigate.to(f'/validar_token?user={username}&token={token_input.value}')

        ui.button('Validar', on_click=validar).classes('w-full mt-4')

def pagina_validar_token(request: Request):
    query = parse_qs(urlparse(str(request.url)).query)
    username = query.get('user', [None])[0]
    token = query.get('token', [None])[0]
    if not username or not token:
        escrever_log(f'Não introduziu nada no campo Token.  User: {username}')
        return HTMLResponse('<h3>Dados em falta</h3>')

    if is_token_valid(username, token):
        response = RedirectResponse(url=config['rota_sucesso'], status_code=303)
        response.set_cookie('user', username, max_age=43200, path='/', samesite='Lax')
        escrever_log(f'Token Check bem Sucedido.  User: {username}')
        return response
    else:
        escrever_log(f'Token Check Failed!  User: {username}')
        return HTMLResponse('<h3>Token inválido ou expirado</h3><a href="/">Voltar</a>')

def pagina_logout(request: Request):
    from urllib.parse import parse_qs, urlparse
    query = parse_qs(urlparse(str(request.url)).query)
    user = query.get('user', [None])[0]
    auth_tokens.pop(user, None)
    response = RedirectResponse(url='/')
    response.delete_cookie('user')
    return response
