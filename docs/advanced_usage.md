# ⚙️ Virtuno – Documentação Técnica Avançada

Este guia contém instruções para configuração de backups automáticos, coleta de dados, integração com o módulo de previsão (`predictor.py`) e uso de cron.

---

## 🧠 Previsão com `predictor.py`

O script `predictor.py` utiliza dados históricos coletados por `collect.py` para prever padrões de uso de CPU, memória e outras métricas.

---

## 📊 Coleta automática com `collect.py`

Script que recolhe dados de carga do sistema, VMs, etc.

### Agendamento com cron:
Para recolher dados a cada 5 minutos:

```bash
crontab -e
```

Adiciona:
```bash
*/5 * * * * /opt/virtuno/scripts/collect.py >> /opt/virtuno/logs/collect.log 2>&1
```

---

## 💾 Backups de VMs com `virsh`

```bash
mkdir -p /opt/virtuno/backups

# Backup XML da configuração
virsh dumpxml vm_name > /opt/virtuno/backups/vm_name.xml

# Snapshot do estado da VM
virsh save vm_name /opt/virtuno/backups/vm_name.save
```

---

## 🗂️ Exemplo de estrutura de ficheiros

```
/opt/virtuno/
├── scripts/
│   ├── collect.py
│   ├── predictor.py
│   └── backup_vms.sh
├── data/
│   └── metrics.csv
├── logs/
└── backups/
```

---

## 🔁 Atualizações automáticas

```bash
#!/bin/bash
apt update && apt upgrade -y
echo "[$(date)] Sistema atualizado." >> /opt/virtuno/logs/update.log
```

---

## 🧹 Rotação de logs (opcional)

```bash
find /opt/virtuno/logs/*.log -mtime +7 -delete
```

Adicionar ao `crontab`:

```bash
@daily /opt/virtuno/scripts/rotate_logs.sh
```

---

Virtuno © 2025 – Francisco Gonçalves