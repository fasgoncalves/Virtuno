from nicegui import ui
import libvirt
import time
import threading

@ui.page('/monitor')
def monitor_page():
    with ui.row().classes('items-center justify-between w-full p-2'):
      ui.label('Monitorização em Tempo Real').classes('text-2xl p-2 text-white')
      ui.button('Return to Dashboard', on_click=lambda: ui.navigate.to('/')).props('outline')
    domains = get_vms()

    for domain in domains:
        name = domain.name()
        with ui.card().classes('m-2 bg-slate-900'):
            ui.label(f'VM: {name}').classes('text-lg text-white')
            
            cpu_options = {
                'title': {'text': 'Uso de CPU (%)', 'textStyle': {'color': 'white'}},
                'tooltip': {},
                'xAxis': {'type': 'category', 'data': [], 'axisLabel': {'color': 'white'}},
'yAxis': {'type': 'value', 'axisLabel': {'color': 'white', 'formatter': '{value}'}},
                'backgroundColor': 'transparent',
                'series': [{
                    'data': [],
                    'type': 'line',
                    'smooth': True,
                    'lineStyle': {'color': '#00ff00'}
                }]
            }

            ram_options = {
                'title': {'text': 'Uso de RAM (MB)', 'textStyle': {'color': 'white'}},
                'tooltip': {},
                'xAxis': {'type': 'category', 'data': [], 'axisLabel': {'color': 'white'}},
'yAxis': {'type': 'value', 'axisLabel': {'color': 'white', 'formatter': '{value}'}},
                'backgroundColor': 'transparent',
                'series': [{
                    'data': [],
                    'type': 'line',
                    'smooth': True,
                    'lineStyle': {'color': '#1e90ff'}
                }]
            }

            net_options = {
                'title': {'text': 'Tráfego de Rede (MB/s)', 'textStyle': {'color': 'white'}},
                'tooltip': {},
                'xAxis': {'type': 'category', 'data': [], 'axisLabel': {'color': 'white'}},
'yAxis': {'type': 'value', 'axisLabel': {'color': 'white', 'formatter': '{value}'}},
                'backgroundColor': 'transparent',
                'series': [
                    {'data': [], 'type': 'line', 'smooth': True, 'name': 'Recebido', 'lineStyle': {'color': '#ffff00'}},
                    {'data': [], 'type': 'line', 'smooth': True, 'name': 'Enviado', 'lineStyle': {'color': '#ff00ff'}}
                ]
            }

            cpu_chart = ui.echart(options=cpu_options).style('margin-left: 20px;').classes('w-[95vw] max-w-full h-64')
            ram_chart = ui.echart(options=ram_options).style('margin-left: 20px;').classes('w-[95vw] max-w-full h-64')
            net_chart = ui.echart(options=net_options).style('margin-left: 20px;').classes('w-[95vw] max-w-full h-64')

            def update_charts(cpu_chart=cpu_chart, ram_chart=ram_chart, net_chart=net_chart, name=name):
                conn = get_connection()
                dom = conn.lookupByName(name)
                interval = 5

                last_net_rx, last_net_tx = get_network_stats(dom)
                while True:
                    time.sleep(interval)
                    now = time.strftime('%H:%M:%S')

                    cpu = get_cpu_usage(dom)
                    ram = get_ram_usage(dom)
                    net_rx, net_tx = get_network_stats(dom)

                    rx_rate = max((net_rx - last_net_rx) / interval / 1024 / 1024, 0)
                    tx_rate = max((net_tx - last_net_tx) / interval / 1024 / 1024, 0)
                    last_net_rx, last_net_tx = net_rx, net_tx

                    cpu_chart.options['xAxis']['data'].append(now)
                    cpu_chart.options['series'][0]['data'].append(round(cpu, 2))
                    cpu_chart.update()

                    ram_chart.options['xAxis']['data'].append(now)
                    ram_chart.options['series'][0]['data'].append(round(ram, 2))
                    ram_chart.update()

                    net_chart.options['xAxis']['data'].append(now)
                    net_chart.options['series'][0]['data'].append(round(rx_rate, 2))
                    net_chart.options['series'][1]['data'].append(round(tx_rate, 2))
                    net_chart.update()

            threading.Thread(target=update_charts, daemon=True).start()

def get_connection():
    return libvirt.open('qemu:///system')

def get_vms():
    conn = get_connection()
    return [d for d in conn.listAllDomains() if d.isActive()]

def get_cpu_usage(domain):
    t1 = domain.getCPUStats(True)[0]['cpu_time']
    time.sleep(0.1)
    t2 = domain.getCPUStats(True)[0]['cpu_time']
    delta = t2 - t1
    return delta / 1e9 * 100

def get_ram_usage(domain):
    mem = domain.memoryStats()
    return mem.get('rss', 0) / 1024

def get_network_stats(domain):
    try:
        tree = domain.XMLDesc()
        import xml.etree.ElementTree as ET
        root = ET.fromstring(tree)
        iface = root.find('./devices/interface/target').attrib['dev']
        stats = domain.interfaceStats(iface)
        return stats[0], stats[4]
    except:
        return 0, 0
