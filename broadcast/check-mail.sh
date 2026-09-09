#!/bin/bash
# check-mail.sh — Verifica mensagens não lidas na mailbox de um agente
# Uso: bash ~/broadcast/check-mail.sh <agent_name>
# Exemplo: bash ~/broadcast/check-mail.sh @traffic

set -euo pipefail

MAILBOX_DIR="$HOME/broadcast/mailbox"

if [ $# -ne 1 ]; then
    echo "Uso: $0 <agent_name>"
    echo "Exemplo: $0 @traffic"
    exit 1
fi

AGENT_NAME="$1"
AGENT_FILE_NAME=$(echo "$AGENT_NAME" | sed 's/@//')
MAILBOX_FILE="$MAILBOX_DIR/${AGENT_FILE_NAME}.json"

if [ ! -f "$MAILBOX_FILE" ]; then
    echo "INFO: Nenhuma mailbox encontrada para $AGENT_NAME. Nenhuma mensagem."
    exit 0
fi

python3 -c "
import json, sys, os
from datetime import datetime

agent_name = '$AGENT_NAME'
mailbox_file = '$MAILBOX_FILE'

with open(mailbox_file, 'r') as f:
    data = json.load(f)

inbox = data.get('inbox', [])
unread = [msg for msg in inbox if not msg.get('read', False)]

# Atualizar last_checked
data['last_checked'] = datetime.now().isoformat()
with open(mailbox_file, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

if not unread:
    print(f'Mailbox {agent_name}: 0 mensagens não lidas (total: {len(inbox)})')
    sys.exit(0)

print(f'Mailbox {agent_name}: {len(unread)} mensagem(ns) não lida(s) (total: {len(inbox)})')
print('=' * 70)

for msg in unread:
    priority_icon = {'high': '!!!', 'normal': ' ! ', 'low': '   '}.get(msg.get('priority', 'normal'), '   ')
    type_icon = {'request': 'REQ', 'info': 'INF', 'alert': 'CLIENTE_EXEMPLO', 'response': 'RES'}.get(msg.get('type', 'info'), '???')
    print(f'')
    print(f'  [{priority_icon}] [{type_icon}] {msg.get(\"id\", \"?\")}')
    print(f'  De: {msg.get(\"from\", \"?\")} | {msg.get(\"timestamp\", \"?\")}')
    print(f'  Subject: {msg.get(\"subject\", \"(sem assunto)\")}')
    body = msg.get('body', '')
    if body:
        # Truncar body longo
        lines = body.strip().split('\\n')
        preview = lines[0][:120]
        if len(lines) > 1 or len(lines[0]) > 120:
            preview += '...'
        print(f'  Body: {preview}')
    print(f'  ---')

print(f'')
print(f'Last checked atualizado: {data[\"last_checked\"]}')
"
