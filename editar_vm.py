
from nicegui import ui
import libvirt
import xml.etree.ElementTree as ET

def get_vm_names():
    conn = libvirt.open('qemu:///system')
    return [dom.name() for dom in conn.listAllDomains()]

def get_vm_xml(name):
    conn = libvirt.open('qemu:///system')
    dom = conn.lookupByName(name)
    return dom.XMLDesc()

@ui.page('/editar_vm')
def editar_vm():
    with ui.row().classes('items-center justify-between w-full p-2'):
      ui.label('VM Machine Editor').classes('text-2xl text-white p-2')
      ui.button('Return to Dashboard', on_click=lambda: ui.navigate.to('/')).props('outline')

    vm_list = get_vm_names()
    selected = ui.select(vm_list, label='Select the VM').classes('w-full')

    nome_input = ui.input('Name da VM').classes('w-full')
    cpu_input = ui.number('CPUs').classes('w-full')
    ram_input = ui.number('Memory RAM (MB)').classes('w-full')
    disk_path_input = ui.input('Path to VM Disk (qcow2)').classes('w-full')
    iso_path_input = ui.input('Path to CD-ROM (CD-ROM)').classes('w-full')
    remove_cdrom = ui.checkbox('Remove CD-ROM drive').classes('mt-2')

    net_type_input = ui.select(['bridge', 'nat'], label='Tipo de rede').classes('w-full')
    net_name_input = ui.input('Name of the interface (ex: virbr0, br0)').classes('w-full')
    ui.label('Autostart').classes('text-white mt-4')
    autostart_toggle = ui.toggle({True: 'Yes', False: 'No'}, value=False).classes('w-full')
    ui.label('Boot Option on Start').classes('mt-4 text-white text-lg')
    boot_order = ui.select(['hd', 'cdrom', 'network'], label='1º dispositivo').classes('w-full')
    boot_order2 = ui.select(['nothing', 'hd', 'cdrom', 'network'], label='2º Device').classes('w-full')

    resultado = ui.label().classes('text-green-500 mt-2')

    def carregar_dados(e):
        xml = get_vm_xml(selected.value)
        root = ET.fromstring(xml)

        nome_input.value = selected.value
        cpu_input.value = int(root.find('./vcpu').text)
        ram_input.value = int(root.find('./memory').text) // 1024

        autostart = libvirt.open('qemu:///system').lookupByName(selected.value).autostart()
        autostart_toggle.value = autostart

        disk = root.find("./devices/disk[@device='disk']/source")
        disk_path_input.value = disk.attrib.get('file', '')

        cdrom = root.find("./devices/disk[@device='cdrom']/source")
        iso_path_input.value = cdrom.attrib.get('file', '') if cdrom is not None else ''
        remove_cdrom.value = cdrom is None

        iface = root.find("./devices/interface/source")
        net_name_input.value = iface.attrib.get('bridge', iface.attrib.get('network', ''))
        net_type_input.value = 'bridge' if 'bridge' in iface.attrib else 'nat'

        os_elem = root.find('./os')
        boots = os_elem.findall('boot')
        boot1 = boots[0].attrib.get('dev') if len(boots) > 0 else 'hd'
        boot2 = boots[1].attrib.get('dev') if len(boots) > 1 else 'nenhum'
        boot_order.value = boot1
        boot_order2.value = boot2

    selected.on('update:model-value', carregar_dados)

    def guardar_alteracoes():
        try:
            conn = libvirt.open('qemu:///system')
            dom = conn.lookupByName(selected.value)
            if dom.isActive():
                resultado.text = 'VM needs to be stopped in order to be edited'
                return

            with open(f'/tmp/{selected.value}.xml.bak', 'w') as f:
                f.write(dom.XMLDesc())

            xml = dom.XMLDesc()
            root = ET.fromstring(xml)

            root.find('./vcpu').text = str(int(cpu_input.value))
            root.find('./memory').text = str(int(ram_input.value) * 1024)
            root.find('./name').text = nome_input.value

            disk = root.find("./devices/disk[@device='disk']/source")
            if disk is not None:
                disk.set('file', disk_path_input.value)

            if remove_cdrom.value:
                cdrom = root.find("./devices/disk[@device='cdrom']")
                if cdrom is not None:
                    root.find('./devices').remove(cdrom)
            else:
                cdrom = root.find("./devices/disk[@device='cdrom']")
                if cdrom is None:
                    cdrom = ET.SubElement(root.find('./devices'), 'disk', {'type': 'file', 'device': 'cdrom'})
                    ET.SubElement(cdrom, 'target', {'dev': 'sata0-0-0', 'bus': 'sata'})
                    ET.SubElement(cdrom, 'readonly')
                    ET.SubElement(cdrom, 'source', {'file': iso_path_input.value})
                else:
                    cdrom_source = cdrom.find('source')
                    if cdrom_source is None:
                        cdrom_source = ET.SubElement(cdrom, 'source')
                    cdrom_source.set('file', iso_path_input.value)
                    target = cdrom.find('target')
                    if target is not None:
                        target.set('bus', 'sata')
                        target.set('dev', 'sata0-0-0')

            iface = root.find('./devices/interface')
            iface_source = iface.find('source')
            iface_source.attrib.clear()
            if net_type_input.value == 'bridge':
                iface_source.set('bridge', net_name_input.value)
            else:
                iface_source.set('network', net_name_input.value)

            os_elem = root.find('./os')
            for boot in os_elem.findall('boot'):
                os_elem.remove(boot)
            ET.SubElement(os_elem, 'boot', {'dev': boot_order.value})
            if boot_order2.value != 'Nothing' and boot_order2.value != boot_order.value:
                ET.SubElement(os_elem, 'boot', {'dev': boot_order2.value})

            nova_xml = ET.tostring(root, encoding='unicode')

            try:
                conn.defineXML(nova_xml)
            except libvirt.libvirtError as e:
                resultado.text = f'Error on the new Defenition : {e}'
                return

            dom.undefine()
            conn.defineXML(nova_xml)
            dom = conn.lookupByName(nome_input.value)
            dom.setAutostart(autostart_toggle.value)

            resultado.text = 'Changes Saved Successfull.'

        except Exception as e:
            resultado.text = f'Error: {e}'

    ui.button('💾 Save changes', on_click=guardar_alteracoes).classes('mt-4 bg-green-700 text-white')
