
from nicegui import ui, app
import mysql.connector
import bcrypt
from functools import wraps

# User authentication
def check_credentials(username, password):
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='iserdb',
            password='userpass',
            database='kvm_manager'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=%s", (username,))
        result = cursor.fetchone()
        if result and bcrypt.checkpw(password.encode(), result[0].encode()):
            app.storage.user['username'] = username
            app.storage.user['authenticated'] = True
            ui.navigate.to('/')
            return True
    except Exception as e:
        print("MySQL Error:", e)
    return False

# Login page
@ui.page('/login')
def login_screen():
    with ui.row().classes('items-center justify-between w-full p-2'):
      ui.label('VIRTUNO - KVM Manager and Monitor Sofware v1.2').classes('text-2xl p-2 text-blue')
    with ui.row().classes('w-full justify-center items-center text-center mt-8'):
        ui.label('Copyrigth for Softelabs, PT').classes('text-sm text-yellow')
        ui.label('Contact us at support@softelabs.pt').classes('text-sm text-red')

    with ui.card().classes('absolute-center'):
        ui.label('Login').classes('text-xl')
        username = ui.input('Username')
        password = ui.input('Password', password=True)
        message = ui.label()

        def try_login():
            if not check_credentials(username.value, password.value):
                message.text = 'Invalid credentials!'

        ui.button('Sign in', on_click=try_login)

# Decorator that requires login
def require_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not app.storage.user.get('authenticated', False):
            ui.navigate.to('/login')
            return lambda: None
        return func(*args, **kwargs)
    return wrapper
