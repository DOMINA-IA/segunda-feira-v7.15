#!/bin/bash
# sf-alert.sh <unit> — OnFailure dos timers da VPS: enfileira no dispatcher (Telegram).
# Vive em script, não inline na unit: systemd expande ${...} dentro de ExecStart antes do
# bash (07-Set: "${n#sf-}" virou string vazia e o título saiu sem o nome do job).
set -u
UNIT="${1:-desconhecida}"
N="${UNIT#sf-}"; N="${N%.service}"
SF_HOME="${HOME:-/opt/segunda-feira}"
. "$SF_HOME/autonomous/lib/common.sh"
LOG="$SF_HOME/logs/$N.log"
if [[ -s "$LOG" ]]; then
  BODY="$(tail -c 1500 "$LOG")"
else
  BODY="$(journalctl -u "$UNIT" -n 20 --no-pager 2>/dev/null | tail -c 1500)"
  [[ -n "$BODY" ]] || BODY="sem log em $LOG"
fi
notify critical "VPS: $N falhou" "$BODY"
