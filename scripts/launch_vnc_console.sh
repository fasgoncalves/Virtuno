#!/bin/bash

# Nome da VM passado como argumento
VM_NAME="$1"

# Diretório onde tens o noVNC (instalado via git clone ou apt-get)
NOVNC_DIR="/opt/novnc"
WEBSOCKIFY="$NOVNC_DIR/utils/websockify/run"
# Porta em que vai correr o noVNC
WEBSOCKET_PORT="6080"

# Descobre a porta VNC real associada à VM. Exemplo de saída de virsh domdisplay:
# vnc://127.0.0.1:5904
VNC_PORT=$(virsh domdisplay "$VM_NAME" | sed 's|.*127.0.0.1:||; s|^0*||')

if [ -z "$VNC_PORT" ]; then
  echo "Erro: não foi possível encontrar a porta VNC para a VM $VM_NAME"
  exit 1
fi

echo "Encontrada porta VNC: $VNC_PORT"

# Parar qualquer instância antiga em 6080
# (podes ajustar se quiseres iniciar em várias portas)
lsof -ti tcp:$WEBSOCKET_PORT | xargs -r kill -9

echo "🟢 Porta VNC encontrada: $PORTA_VNC"

# === Verifica se websockify existe ===
if [ ! -x "$WEBSOCKIFY" ]; then
    echo "❌ Websockify não encontrado ou não executável em $WEBSOCKIFY"
    exit 1
fi

# === Lança noVNC ===
echo "🚀 Iniciando noVNC em http://localhost:$PORTA_HTTP/vnc.html"
$WEBSOCKIFY --web "$NOVNC_DIR" $PORTA_HTTP localhost:$PORTA_VNC &

# Espera 2 segundos
sleep 2

# Verifica se a porta está ativa
if lsof -i :$PORTA_HTTP >/dev/null 2>&1; then
    echo "🌍 Abrindo browser em: http://localhost:$PORTA_HTTP/vnc.html?host=localhost&port=$PORTA_VNC"
    xdg-open "https://localhost:$PORTA_HTTP/vnc.html?host=localhost&port=$PORTA_VNC" >/dev/null 2>&1 &
else
    echo "⚠️ Erro: A porta $PORTA_HTTP não está ativa. Verifique permissões ou conflitos."
fi

