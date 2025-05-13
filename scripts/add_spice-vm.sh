#!/bin/bash

# Verifica se foi fornecido o nome da VM
if [ -z "$1" ]; then
  echo "⚠️  Uso: $0 nome_da_vm"
  exit 1
fi

VM_NAME="$1"
TMP_FILE="/tmp/${VM_NAME}_mod.xml"

# Exporta a configuração atual da VM
virsh dumpxml "$VM_NAME" > "$TMP_FILE"

# Verifica se já existe uma secção SPICE
if grep -q "<graphics type='spice'" "$TMP_FILE"; then
  echo "✅ A VM '$VM_NAME' já possui configuração SPICE."
  exit 0
fi

# Adiciona apenas a secção SPICE
sed -i '/<\/devices>/i \
  <graphics type="spice" autoport="yes" listen="0.0.0.0">\
    <listen type="address" address="0.0.0.0"/>\
    <image compression="auto_glz"/>\
    <streaming mode="filter"/>\
  </graphics>' "$TMP_FILE"

# Redefine a VM com a nova configuração
virsh define "$TMP_FILE"

echo "✅ Configuração SPICE adicionada à VM '$VM_NAME' com sucesso."
