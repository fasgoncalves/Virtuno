#!/bin/bash
# Define a porta da shell
VM_NAME=$1
LOGFILE = ""
echo "📡  NOME DA VM : " $1
# Discover IP maquina Virtual
MAC=$(virsh dumpxml $VM_NAME | xmllint --xpath "//interface[source/@bridge='br0']/mac/@address" - 2>/dev/null | cut -d'"' -f2
)
echo "MAC ADDR " + $MAC

if [ -z "$MAC" ]; then
  echo "❌ Erro ao obter o MAC da VM $VM_NAME"
  exit 1
fi

echo "🔍 MAC address da VM: $MAC"

# Verifica a tabela ARP e extrai o IP correspondente
IP=$(arp -e | grep -i "$MAC" | awk '{print $1}')

echo "IP DESCOBERTO É : $IP"

if [ -z "$IP" ]; then
  echo "❌ IP não encontrado para o MAC $MAC. A VM pode não ter enviado tráfego."
  exit 1
fi

echo "📡 IP da VM '$VM_NAME': $IP"
echo "$IP"  > /opt/kvm-manager/current_vm_ip.txt
# Lança o ttyd na máquina virtual via ssh
PORTA_TTYD=8022
echo "🚀 A iniciar ttyd na VM $VM_NAME ($IP) na porta $PORTA_TTYD..."

sshpass -p 'password' ssh -f -o StrictHostKeyChecking=no "admin@$IP" \
"nohup ttyd --render-type=dom --once --writable -i 0.0.0.0 -p $PORTA_TTYD /bin/bash --login >/dev/null 2>&1 &" 
# Indicar o URL ao utilizador
echo "🌍 Aceda ao terminal via: http://$IP:$PORTA_TTYD"
# Aguarda um pouco
sleep 2
# Abre o navegador se possível
echo "🌍 Aceda via browser em: http://mgr.fragmentoscaos.eu"
#
#echo "" > /opt/kvm-manager/current_vm_ip.txt
#
