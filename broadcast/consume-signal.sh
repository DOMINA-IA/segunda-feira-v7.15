#!/bin/bash
# consume-signal.sh — Marca um sinal como consumido por um agente
# Uso: bash ~/broadcast/consume-signal.sh <signal_id> <agent_name>
# Exemplo: bash ~/broadcast/consume-signal.sh sig_001 @analyst
# Idempotente: não adiciona duplicatas

set -euo pipefail

SIGNALS_FILE="$HOME/broadcast/signals.json"

if [ $# -ne 2 ]; then
    echo "Uso: $0 <signal_id> <agent_name>"
    echo "Exemplo: $0 sig_001 @analyst"
    exit 1
fi

SIGNAL_ID="$1"
AGENT_NAME="$2"

if [ ! -f "$SIGNALS_FILE" ]; then
    echo "ERRO: $SIGNALS_FILE não encontrado."
    exit 1
fi

python3 -c "
import json, sys

signal_id = '$SIGNAL_ID'
agent_name = '$AGENT_NAME'
signals_file = '$SIGNALS_FILE'

with open(signals_file, 'r') as f:
    data = json.load(f)

found = False
for signal in data.get('active_signals', []):
    if signal['id'] == signal_id:
        found = True
        consumed = signal.get('consumed_by', [])
        if agent_name in consumed:
            print(f'INFO: {agent_name} já consumiu o sinal {signal_id}. Nenhuma alteração.')
            sys.exit(0)
        consumed.append(agent_name)
        signal['consumed_by'] = consumed
        break

if not found:
    # Verificar também nos arquivados
    for signal in data.get('archived_signals', []):
        if signal['id'] == signal_id:
            found = True
            consumed = signal.get('consumed_by', [])
            if agent_name in consumed:
                print(f'INFO: {agent_name} já consumiu o sinal {signal_id} (arquivado). Nenhuma alteração.')
                sys.exit(0)
            consumed.append(agent_name)
            signal['consumed_by'] = consumed
            break

if not found:
    print(f'ERRO: Sinal {signal_id} não encontrado em active_signals nem archived_signals.')
    sys.exit(1)

with open(signals_file, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f'OK: {agent_name} consumiu o sinal {signal_id}.')
"
