# -*- coding: utf-8 -*-
from nicegui import ui
import os
import csv
from datetime import datetime
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import io
import base64
import subprocess

# Caminhos dos logs dos módulos
LOG_PATHS = {
    'Watchdog': '/var/log/virtuno_watchdog.log',
    'Sentinel': '/var/log/virtuno_sentinel.log',
    'ConfigGuard': '/var/log/virtuno_configguard.log',
}

SERVICE_NAMES = {
    'Watchdog': 'virtuno_watchdog',
    'Sentinel': 'virtuno_sentinel',
    'ConfigGuard': 'virtuno_configguard',
}

log_buffers = {mod: [] for mod in LOG_PATHS}

def read_last_lines(path, max_lines=20):
    if not os.path.exists(path):
        return ["(log não encontrado)"]
    with open(path, 'r') as f:
        lines = f.readlines()[-max_lines:]
    return [line.strip() for line in lines]

def parse_timestamps(lines):
    hours = [line[1:14] for line in lines if line.startswith('[')]
    counter = Counter(hours)
    return counter

def plot_events(counter, title):
    fig, ax = plt.subplots(figsize=(8, 3))
    labels, values = zip(*sorted(counter.items()))
    ax.bar(labels, values)
    ax.set_title(title)
    ax.set_ylabel('Eventos')
    ax.set_xlabel('Hora')
    ax.tick_params(axis='x', rotation=45)
    fig.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close(fig)
    return f'data:image/png;base64,{encoded}'

def export_csv(module):
    lines = log_buffers[module]
    filename = f'{module.lower()}_export.csv'
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Timestamp', 'Mensagem'])
        for line in lines:
            if line.startswith('['):
                timestamp, msg = line.split(']', 1)
                writer.writerow([timestamp.strip('[]'), msg.strip()])
            else:
                writer.writerow(['', line.strip()])
    return filename

def control_service(module, action):
    service = SERVICE_NAMES[module]
    result = subprocess.run(['systemctl', action, service], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout.strip() + result.stderr.strip()

with ui.header().classes('bg-slate-900 text-white'):
    ui.label('Painel Virtuno - Segurança Integrada').classes('text-2xl')

with ui.tabs().classes('w-full') as tabs:
    tab_watchdog = ui.tab('Watchdog')
    tab_sentinel = ui.tab('Sentinel')
    tab_configguard = ui.tab('ConfigGuard')

with ui.tab_panels(tabs, value=tab_watchdog).classes('w-full') as panels:
    panels_dict = {}
    for tab, module in zip([tab_watchdog, tab_sentinel, tab_configguard], ['Watchdog', 'Sentinel', 'ConfigGuard']):
        with ui.tab_panel(tab) as panel:
            panels_dict[module] = {
                'container': ui.column().classes('p-4 bg-gray-100 rounded shadow'),
                'chart': ui.image().style('max-width:100%'),
                'logs': ui.column(),
                'buttons': ui.row()
            }
            ui.label(f'Módulo {module}').classes('text-xl font-bold text-blue-900')
            with panels_dict[module]['buttons']:
                ui.button(f'Restart {module}', on_click=lambda m=module: ui.notify(control_service(m, 'restart')))
                ui.button(f'Stop {module}', on_click=lambda m=module: ui.notify(control_service(m, 'stop')))
                ui.button(f'Start {module}', on_click=lambda m=module: ui.notify(control_service(m, 'start')))
                ui.button(f'Exportar CSV', on_click=lambda m=module: ui.download(export_csv(m)))

def update_all():
    for module, path in LOG_PATHS.items():
        lines = read_last_lines(path, 100)
        log_buffers[module] = lines

        panels_dict[module]['logs'].clear()
        for line in reversed(lines[-20:]):
            ui.label(line).classes('text-sm text-gray-800').bind_to(panels_dict[module]['logs'])

        counter = parse_timestamps(lines)
        chart_data = plot_events(counter, f'Eventos por Hora - {module}')
        panels_dict[module]['chart'].set_source(chart_data)

ui.timer(10.0, update_all)

ui.run(title='Virtuno Painel Avançado', dark=True)