#!/bin/bash
# emit-signal.sh — Emite um sinal no broadcast (~/broadcast/signals.json).
#
# Criado 16-Jul-2026: múltiplos agentes (fabio-soares, mestre-do-conselho,
# challenge-funnel) referenciavam este script, mas ele não existia — os sinais
# que eles deveriam emitir nunca eram escritos.
#
# Formato canônico = LISTA de sinais (é o que signal-router.py e heartbeat.py
# leem via isinstance(data, list)). Cada sinal é um objeto append à lista.
#
# Uso: emit-signal.sh <type> <from> <detail> [priority]
#   type     — tipo do sinal (ex: method_deviation_blocked, council_decision)
#   from     — agente emissor (ex: @fabio-soares)
#   detail   — descrição curta
#   priority — high|normal|low (default: normal)

set -euo pipefail

TYPE="${1:-}"
FROM="${2:-}"
DETAIL="${3:-}"
PRIORITY="${4:-normal}"

if [ -z "$TYPE" ] || [ -z "$FROM" ]; then
  echo "Uso: emit-signal.sh <type> <from> <detail> [priority]" >&2
  exit 1
fi

SIGNALS_FILE="$HOME/broadcast/signals.json"

TYPE="$TYPE" FROM="$FROM" DETAIL="$DETAIL" PRIORITY="$PRIORITY" \
SIGNALS_FILE="$SIGNALS_FILE" python3 <<'PYEOF'
import json, os, sys, hashlib
from datetime import datetime, timezone

path = os.environ["SIGNALS_FILE"]
now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
# id determinístico-ish sem depender de random (indisponível em alguns harnesses)
seed = os.environ["TYPE"] + os.environ["FROM"] + now
sid = "sig_" + hashlib.md5(seed.encode()).hexdigest()[:12]

signal = {
    "id": sid,
    "type": os.environ["TYPE"],
    "from": os.environ["FROM"],
    "data": {"detail": os.environ["DETAIL"]},
    "priority": os.environ["PRIORITY"],
    "timestamp": now,
    "status": "active",
}

# Lê tolerante: aceita list (canônico) ou dict legado com active_signals.
signals = []
try:
    with open(path) as f:
        cur = json.load(f)
    signals = cur if isinstance(cur, list) else cur.get("active_signals", [])
except (FileNotFoundError, json.JSONDecodeError):
    signals = []

signals.append(signal)
with open(path, "w") as f:
    json.dump(signals, f, ensure_ascii=False, indent=2)

print(f"sinal emitido: {sid} ({signal['type']} de {signal['from']}, prioridade {signal['priority']})")
PYEOF
