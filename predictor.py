
from nicegui import ui
import mysql.connector
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression

@ui.page('/previsao')
def previsao_page():
    with ui.row().classes('items-center justify-between w-full p-2'):
      ui.label('Previsão de Comportamento das VMs').classes('text-2xl p-2 text-white')
      ui.button('Return to Dashboard', on_click=lambda: ui.navigate.to('/')).props('outline')

    stats = get_vm_names()

    for vm in stats:
        df = get_data(vm)
        if len(df) < 10:
            ui.label(f'VM {vm}: Dados insuficientes para previsão.').classes('text-red-500')
            continue

        for metric in ['cpu', 'ram']:
            X = np.arange(len(df)).reshape(-1, 1)
            y = df[metric].values
            model = LinearRegression().fit(X, y)

            future_X = np.arange(len(df), len(df) + 6).reshape(-1, 1)
            future_y = model.predict(future_X)

            labels = [t.strftime('%H:%M') for t in df['timestamp']]
            labels += [(df['timestamp'].iloc[-1] + timedelta(minutes=5*i)).strftime('%H:%M') for i in range(1, 7)]

            chart = {
                'title': {'text': f'VM: {vm} - Previsão de {metric.upper()}', 'textStyle': {'color': 'white'}},
                'tooltip': {},
                'xAxis': {'type': 'category', 'data': labels, 'axisLabel': {'color': 'white'}},
                'yAxis': {'type': 'value', 'axisLabel': {'color': 'white'}},
                'backgroundColor': 'transparent',
                'series': [{
                    'data': list(y) + list(future_y),
                    'type': 'line',
                    'smooth': True,
                    'lineStyle': {'color': '#00ffff' if metric == 'cpu' else '#ffa500'}
                }]
            }
            ui.echart(options=chart).classes('w-full h-64')

def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='yakarais',
        database='kvm_manager'
    )

def get_vm_names():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT vm_name FROM usage_history")
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result

def get_data(vm_name):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, cpu, ram FROM usage_history WHERE vm_name = %s ORDER BY timestamp DESC LIMIT 30", (vm_name,))
    rows = cursor.fetchall()
    conn.close()
    df = pd.DataFrame(rows, columns=['timestamp', 'cpu', 'ram'])
    df = df.sort_values('timestamp')
    return df
