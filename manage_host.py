# -*- coding: utf-8 -*-
from nicegui import ui 
import sys
import time
import uuid
import random
import socket
import string
import requests
import psutil
import subprocess
import re
# Uitlizadores Table em dict

process_limit = 50
port_limit = 20
last_iops_data = {}

def send_alarm():
    #
    # Send to mobile
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"alarm_{current_time}.jpg"
    logging.info("Starting Message Sent to Mobile")
    TOPIC="Alertas"
    MESSAGE = "⚠️ Alerta : erro fatal " 
    URL = f"http://localhost.pt:9000/{TOPIC}"
    USER = "admin"
    PASSWORD = "admin"

    headers = {
    "Title": "Alerta de Seguranca",
    "Priority": "high"
    }
    logging.info("Preparing Message to Send to Mobile")

    response = requests.post(URL, headers=headers, data=MESSAGE.encode("utf-8"), auth=(USER, PASSWORD) )
    return response
#
# **Função para Atualizar Tabela de Portas**
def update_ports_table():
    global port_limit
    ports_table.rows = [
        {'Porta': conn.laddr.port, 'Protocolo': "TCP" if conn.type == socket.SOCK_STREAM else "UDP", 'PID': str(conn.pid) if conn.pid else "N/A", 'Programa': psutil.Process(conn.pid).name() if conn.pid else "Desconhecido"}
        for conn in psutil.net_connections(kind='inet') if conn.status == "LISTEN"
    ][:port_limit]

# **Função para Encerrar um Processo**
def kill_process(pid, name):
    try:
        psutil.Process(int(pid)).terminate()
        ui.notify(f"Processo {name} (PID {pid}) encerrado!", type="warning")
        process_table.rows = [p for p in process_table.rows if p['PID'] != pid]
    except psutil.NoSuchProcess:
        ui.notify("O processo já não existe.", type="negative")

# **Popup de Confirmação para Processos**
def confirmar_remocao_processo(event):
    print("Evento recebido:", event.args)  # Debug para verificar estrutura dos argumentos

    if isinstance(event.args, list) and len(event.args) > 1:
        row_data = event.args[1]  # ✅ Obtém o segundo item da lista (onde os dados da linha estão)
    else:
        ui.notify("Erro ao obter os dados do processo!", type="negative")
        return

    pid = row_data.get('PID', 'N/A')
    name = row_data.get('Nome', 'Desconhecido')

    with ui.dialog() as dialog:
        with ui.card():
            ui.label(f"Tem certeza que deseja encerrar {name} (PID {pid})?")
            with ui.row():
                ui.button("Sim", on_click=lambda: [kill_process(pid, name), dialog.close()]).classes("bg-red-500 text-white")
                ui.button("Cancelar", on_click=dialog.close)

    dialog.open()

# **Popup de Confirmação para Portas**
def confirmar_remocao_porta(event):
    print("Evento recebido:", event.args)  # Debug para verificar estrutura dos argumentos

    if isinstance(event.args, list) and len(event.args) > 1:
        row_data = event.args[1]  # ✅ Obtém o segundo item da lista (onde os dados da linha estão)
    else:
        ui.notify("Erro ao obter os dados da porta!", type="negative")
        return

    port = row_data.get('Porta', 'N/A')
    pid = row_data.get('PID', 'N/A')
    program = row_data.get('Programa', 'Desconhecido')

    with ui.dialog() as dialog:
        with ui.card():
            ui.label(f"Tem certeza que deseja remover a porta {port} usada pelo programa {program}?")
            with ui.row():
                ui.button("Sim", on_click=lambda: [remove_port_from_table(port), dialog.close()]).classes("bg-red-500 text-white")
                ui.button("Cancelar", on_click=dialog.close)

    dialog.open()
 
 
def update_temp1_chart():
    """Updates the temperature chart for temp1 sensor."""
    temp_value = get_temp1_temperature()
    itemp_chart.options['xAxis']['data'] = ["Temp Interna"]  # Single data point
    itemp_chart.options['series'][0]['data'] = [temp_value]  # Assign temperature value
    itemp_chart.update()
#
def get_temp1_temperature():
    """Obtém a temperatura do sensor temp1 via comando sensors"""
    try:
        output = subprocess.check_output("sensors", shell=True, text=True)
        match = re.search(r'temp1:\s+\+([\d.]+)', output)  # Captura temp1
        if match:
            return float(match.group(1))  # Retorna a temperatura como número
    except Exception as e:
        print(f"Erro ao obter temp1: {e}")
    return 0
#
# **Função para Atualizar CPU e Memória**
#
def update_system_usage():
    cpu_percent = psutil.cpu_percent()
    mem_percent = psutil.virtual_memory().percent
    cpu_chart.set_value(cpu_percent / 100)
    cpu_label.set_text(f"{cpu_percent:.1f}%")
    mem_chart.set_value(mem_percent / 100)
    mem_label.set_text(f"{mem_percent:.1f}%")
    memval = str(mem_percent)
    cpuval = str(cpu_percent)
    #print ("data " + str(mem_percent) + " - " + str(cpu_percent))
    if  mem_percent > 75:
        send_alarm_mobile("Alarme: A Memória do sistema Voltaire está ocupada a " + memval)
    if  cpu_percent > 85:
        send_alarm_mobile("Alarme: A Memória do sistema Voltaire está ocupada a " + cpuval)
#
def get_iops():
    """Obtém IOPS apenas para /dev/sda3, /dev/sdb1, /dev/sdc1 e /dev/sdd1."""
    global last_iops_data
    current_iops = psutil.disk_io_counters(perdisk=True)

    # Mapeamento correto para os nomes dos discos (psutil usa apenas a letra do dispositivo)
    disks_of_interest = ["sda3", "sdb1", "sdc1", "sdd1"]

    iops_result = []
    timestamp = time.time()

    for disk, stats in current_iops.items():
        if disk in disks_of_interest:
            if disk in last_iops_data:
                delta_time = timestamp - last_iops_data[disk]["timestamp"]
                read_iops = (stats.read_count - last_iops_data[disk]["read"]) / delta_time
                write_iops = (stats.write_count - last_iops_data[disk]["write"]) / delta_time
                iops_result.append((disk, max(read_iops, 0), max(write_iops, 0)))  # Evita valores negativos

            # Atualiza os dados antigos
            last_iops_data[disk] = {"read": stats.read_count, "write": stats.write_count, "timestamp": timestamp}

    return iops_result if iops_result else [("Sem Dados", 0, 0)]
#
def update_iops_chart():
    """Atualiza o gráfico de IOPS para os discos de interesse."""
    iops_stats = get_iops()

    disks = [f"{disk}" for disk, _, _ in iops_stats]  # Adiciona prefixo /dev/
    read_ops = [read for _, read, _ in iops_stats]
    write_ops = [write for _, _, write in iops_stats]

    iops_chart.options['xAxis']['data'] = disks  # Atualiza os rótulos dos discos
    iops_chart.options['series'][0]['data'] = read_ops
    iops_chart.options['series'][1]['data'] = write_ops
    iops_chart.update()
#
#
def get_temperatures():
    """ Obtém as temperaturas dos núcleos do processador """
    temps = psutil.sensors_temperatures()
    if "coretemp" in temps:
        return [t.current for t in temps["coretemp"]]
    return []

def get_disk_usage():
    """ Obtém o uso do disco em percentagem apenas para /dev/sda3, /dev/sdb1, /dev/sdc1 e /dev/sdd1 """
    selected_disks = {"/dev/sda3", "/dev/sdb1", "/dev/sdc1", "/dev/sdd1"}
    return [(dp.device, dp.mountpoint, psutil.disk_usage(dp.mountpoint).percent) 
            for dp in psutil.disk_partitions(all=False) if dp.device in selected_disks]
#
def update_disk_usage_chart():
    """ Atualiza o gráfico de uso de disco """
    disk_stats = get_disk_usage()
    disks = [f"{dp[0]} ({dp[1]})" for dp in disk_stats]  # Rótulo com nome do disco + ponto de montagem
    usage = [dp[2] for dp in disk_stats]

    disk_chart.options['xAxis']['data'] = disks
    disk_chart.options['series'][0]['data'] = usage
    disk_chart.update()
#
def get_network_usage():
    """Obtém o tráfego de rede (Upload e Download) apenas para as interfaces br0 e br1."""
    net_stats = psutil.net_io_counters(pernic=True)
    interfaces_of_interest = ["eno1", "eno2"]

    net_result = []

    for iface in interfaces_of_interest:
        if iface in net_stats:
            stats = net_stats[iface]
            upload_kb = int(round(stats.bytes_sent / (1024), 0) / 100000000)    # Convertendo bytes para MB
            download_kb = int(round(stats.bytes_recv / (1024), 0) / 100000000)    # Convertendo bytes para MB
            net_result.append((iface, upload_kb, download_kb))

    return net_result if net_result else [("eno1", 0, 0), ("eno2", 0, 0)]  # Evita erro caso as interfaces não existam
#
def get_disk_iops():
    """ Obtém as operações de entrada/saída (IOPS) do disco """
    iops_stats = psutil.disk_io_counters(perdisk=True)
    return [(disk, stats.read_count, stats.write_count) for disk, stats in iops_stats.items()]

def update_temperature_chart():
    """ Atualiza o gráfico de temperatura da CPU """
    temps = get_temperatures()
    
    if temps:
        temp_chart.options['xAxis']['data'] = [f"Core {i}" for i in range(len(temps))]  # Atualiza os rótulos dos núcleos
        temp_chart.options['series'][0]['data'] = temps  # Atualiza os valores
        temp_chart.update()
    else:
        print("❌ Nenhum dado de temperatura disponível!")

def update_network_chart():
    net_stats = get_network_usage()

    if not net_stats:
        ui.notify("Nenhuma interface br0 ou br1 encontrada!", type="warning")
        return

    interfaces = [iface for iface, _, _ in net_stats]
    upload_data = [up for _, up, _ in net_stats]
    download_data = [down for _, _, down in net_stats]

    net_chart.options['xAxis']['data'] = interfaces  # Atualiza os rótulos dos eixos com os nomes das interfaces
    net_chart.options['series'][0]['data'] = upload_data  # Atualiza os valores de upload
    net_chart.options['series'][1]['data'] = download_data  # Atualiza os valores de download
    net_chart.update()
#
# **Função para Atualizar Tabela de Processos**
def update_process_table():
        process_data = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if proc.info['name'] is None:
                    continue
                if proc.info['name'].startswith(("kworker", "rcu_", "migration", "watchdog", "idle")):
                    continue

                process_data.append({
                    'PID': proc.info['pid'],
                    'Nome': proc.info['name'],
                    'CPU (%)': f"{proc.info['cpu_percent']:.1f}",
                    'Memória (%)': f"{proc.info['memory_percent']:.1f}",
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        process_table.rows = process_data

# **Função para Atualizar Tabela de Portas**
def update_ports_table():
    global port_limit
    ports_table.rows = [
        {'Porta': conn.laddr.port, 'Protocolo': "TCP" if conn.type == socket.SOCK_STREAM else "UDP", 'PID': str(conn.pid) if conn.pid else "N/A", 'Programa': psutil.Process(conn.pid).name() if conn.pid else "Desconhecido"}
        for conn in psutil.net_connections(kind='inet') if conn.status == "LISTEN"
    ][:port_limit]

def obter_uso_memoria():
    """Obtém a quantidade de memória usada pelo processo atual (NiceGUI)"""
    processo = psutil.Process()  # Obtém o processo atual
    memoria_mb = processo.memory_info().rss / (1024 * 1024)  # Converte bytes para MB
    return round(memoria_mb, 2)

def atualizar_memoria():
    """Atualiza a exibição da memória usada"""
    memoria_usada = obter_uso_memoria()
    return memoria_usada

@ui.page("/Host_Monitor")
def monitor_page():

    global process_table, ports_table, cpu_chart, cpu_label, mem_chart, mem_label
    global temp_chart, net_chart, disk_chart, iops_chart, itemp_chart

    # **Header com Botão de Logout**
    with ui.row().classes("w-full justify-between items-center bg-gray-200 p-3 shadow-md text-blue"):
        with ui.row().classes('items-center justify-between w-full p-2'):
           ui.label("📊 Virtuso - KVM HOST MONITOR").classes("text-lg font-bold")
           ui.button('Return to Dashboard', on_click=lambda: ui.navigate.to('/')).props('outline')

    ui.label(f'Memória utilizada: {obter_uso_memoria()} MB').classes("text-md font-bold mt-4 text-center")

    ui.label("📈 Uso de CPU e Memória").classes("text-md font-bold mt-4 text-center")

    with ui.card().classes("w-full max-w-2xl p-4"):
        with ui.row().classes("w-full justify-around"):
            with ui.column():
                ui.label("CPU (%)").classes("text-sm font-bold text-center")
                cpu_chart = ui.linear_progress(value=0, show_value=False).classes('w-40 h-4')
                cpu_label = ui.label("0%").classes("text-sm text-center")

            with ui.column():
                ui.label("Memória (%)").classes("text-sm font-bold text-center")
                mem_chart = ui.linear_progress(value=0, show_value=False).classes("w-40 h-4")
                mem_label = ui.label("0%").classes("text-sm text-center")

    ui.label("🔥 Temperatura Interna do Servidor (°C)").classes("text-md font-bold mt-4 text-center")
    itemp_chart = ui.echart({
    'title': {'text': ""},
    'tooltip': {'trigger': 'axis'},
    'xAxis': {'type': 'category', 'data': []},  # Dynamically updated
    'yAxis': {'type': 'value', 'min': 20, 'max': 80},  # Adjust based on CPU temp range
    'series': [{'type': "bar", 'data': []}]
    })
   
    ui.label("🔥 Temperatura dos cores do CPU").classes("text-md font-bold mt-4 text-center")
    temp_chart = ui.echart({
        'title': {'text': "Temperatura (°C)"},
        'tooltip': {'trigger': 'axis'},
        'xAxis': {'type': 'category', 'data': []},  # Atualizado dinamicamente
        'yAxis': {'type': 'value', 'min': 30, 'max': 100},
        'series': [{'type': "bar", 'data': []}]
    })
    
    ui.label("🌐 Tráfego de Rede (MB)").classes("text-md font-bold mt-4 text-center")
    #
    net_chart = ui.echart({
    'title': {'text': "(MB)"},
    'tooltip': {'trigger': 'axis'},
    'legend': {'data': ["Upload", "Download"]},
    'grid': {'left': '50px', 'right': '10px', 'top': '50px', 'bottom': '50px'},  # Move o gráfico mais à direita
    'xAxis': {'type': 'category', 'data': ["br0", "br1"]},  
    'yAxis': {
        'type': 'value',
        'axisLabel': {'formatter': '{value} MB' },  # Formata os valores corretamente
        'min': 0,  
    },
    'series': [
        {'name': "Upload", 'type': "bar", 'data': [0, 0]},  
        {'name': "Download", 'type': "bar", 'data': [0, 0]}  
    ]
    })
    #
    ui.label("💾 Espaço em Disco (%)").classes("text-md font-bold mt-4 text-center")
    disk_chart = ui.echart({
        'title': {'text': "Uso do Disco"},
        'tooltip': {'trigger': 'axis'},
        'xAxis': {'type': 'category', 'data': []},  # Atualizado dinamicamente
        'yAxis': {'type': 'value', 'min': 0, 'max': 100},
        'series': [{'type': "bar", 'data': []}]
    })

    ui.label("📊 IOPS (Operações por Segundo)").classes("text-md font-bold mt-4 text-center")
    iops_chart = ui.echart({
        'title': {'text': "IOPS"},
        'tooltip': {'trigger': 'axis'},
        'legend': {'data': ["Leituras", "Escritas"]},
        'xAxis': {'type': 'category', 'data': ["Loading..."]},  # Atualiza com nomes reais dos discos
        'yAxis': {'type': 'value'},
        'series': [
            {'name': "Leituras", 'type': "bar", 'data': [0]},
            {'name': "Escritas", 'type': "bar", 'data': [0]}
        ]
    })

    # **Tabela de Processos**
    ui.label("📋 Processos Ativos").classes("text-md font-bold mt-4 text-center")
    with ui.card().classes("w-full max-w-6xl"):
        with ui.scroll_area().classes("h-[300px] overflow-auto border-t border-gray-200 overflow-x-auto"):
            process_table = ui.table(
                columns=[
                    {'name': 'PID', 'label': 'PID', 'field': 'PID'},
                    {'name': 'Nome', 'label': 'Nome', 'field': 'Nome'},
                    {'name': 'CPU (%)', 'label': 'CPU', 'field': 'CPU (%)'},
                    {'name': 'Memória (%)', 'label': 'Mem', 'field': 'Memória (%)'},
                ],
                rows=[],
                row_key="PID"
            ).on("row-dblclick", confirmar_remocao_processo)

        # **Tabela de Portas Abertas**
    ui.label("🌐 Portas Abertas").classes("text-md font-bold mt-6 text-center")

    with ui.card().classes("w-full max-w-full sm:max-w-6xl"):  # Se adapta ao ecrã
        with ui.scroll_area().classes("h-[300px] overflow-auto border-t border-gray-200 overflow-x-auto"):  # Permite scroll lateral em mobile
            ports_table = ui.table(
                columns=[
                    {'name': 'Porta', 'label': 'Porta', 'field': 'Porta'},
                    {'name': 'Protocolo', 'label': 'Prot.', 'field': 'Protocolo'},
                    {'name': 'PID', 'label': 'PID', 'field': 'PID'},
                    {'name': 'Programa', 'label': 'Programa', 'field': 'Programa'},
                ],
                rows=[],
                row_key="Porta"
            ).on("row-dblclick", confirmar_remocao_porta)
    # **Timers**
    time.sleep(1)
    ui.timer(1, update_system_usage)  
    ui.timer(8, update_process_table)
    ui.timer(15, update_ports_table)
    ui.timer(20, update_temp1_chart)
    ui.timer(8, update_temperature_chart)
    ui.timer(5, update_network_chart)
    ui.timer(15, update_disk_usage_chart)
    ui.timer(5, update_iops_chart)
    ui.timer(3.0, atualizar_memoria)
#
