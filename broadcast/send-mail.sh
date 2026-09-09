#!/bin/bash
# send-mail.sh — Envia mensagem para a mailbox de um agente
# Uso: echo "corpo da mensagem" | bash ~/broadcast/send-mail.sh <from> <to> <type> <subject>
# Exemplo: echo "Detalhes aqui" | bash ~/broadcast/send-mail.sh @traffic @content info "Novo ângulo disponível"
# Types válidos: request, info, alert, response

set -euo pipefail

if [ $# -ne 4 ]; then
    echo "Uso: echo \"corpo\" | $0 <from_agent> <to_agent> <type> <subject>"
    echo "Exemplo: echo \"Detalhes\" | $0 @traffic @content info \"Novo ângulo\""
    echo "Types: request, info, alert, response"
    exit 1
fi

FROM_AGENT="$1"
TO_AGENT="$2"
MSG_TYPE="$3"
SUBJECT="$4"

# Ler body de stdin (ou vazio se não houver)
BODY=""
if [ ! -t 0 ]; then
    BODY=$(cat)
fi

# Salvar body em tempfile para evitar problemas de escaping
TMPFILE=$(mktemp)
echo "$BODY" > "$TMPFILE"

python3 - "$FROM_AGENT" "$TO_AGENT" "$MSG_TYPE" "$SUBJECT" "$TMPFILE" <<'PYEOF'
import json, sys, os
from datetime import datetime

from_agent = sys.argv[1]
to_agent = sys.argv[2]
msg_type = sys.argv[3]
subject = sys.argv[4]
body_file = sys.argv[5]

MAILBOX_DIR = "$HOME/broadcast/mailbox"

# Ler body do tempfile
with open(body_file, 'r') as f:
    body = f.read().strip()
os.unlink(body_file)

# Validar type
valid_types = ['request', 'info', 'alert', 'response']
if msg_type not in valid_types:
    print(f'ERRO: type "{msg_type}" inválido. Use: {valid_types}')
    sys.exit(1)

# Nome do arquivo de mailbox: remove @ do nome do agente
agent_file_name = to_agent.lstrip('@')
mailbox_file = os.path.join(MAILBOX_DIR, f"{agent_file_name}.json")

# Criar mailbox se não existir
if not os.path.exists(mailbox_file):
    data = {
        "agent": to_agent,
        "inbox": [],
        "last_checked": None
    }
else:
    with open(mailbox_file, 'r') as f:
        data = json.load(f)

# Gerar ID
now = datetime.now()
msg_id = f'msg_{now.strftime("%Y%m%d%H%M%S")}_{now.microsecond // 1000:03d}'

# Determinar prioridade baseada no type
priority_map = {'alert': 'high', 'request': 'normal', 'info': 'normal', 'response': 'low'}
priority = priority_map.get(msg_type, 'normal')

message = {
    "id": msg_id,
    "from": from_agent,
    "to": to_agent,
    "type": msg_type,
    "subject": subject,
    "body": body,
    "priority": priority,
    "data": {},
    "timestamp": now.isoformat(),
    "read": False,
    "thread_id": None
}

data['inbox'].append(message)

with open(mailbox_file, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f'OK: Mensagem {msg_id} enviada de {from_agent} para {to_agent}.')
print(f'    Subject: {subject}')
print(f'    Type: {msg_type} | Priority: {priority}')
print(f'    Arquivo: {mailbox_file}')
PYEOF
