#!/bin/bash
# =============================================================================
# check-overdue-decisions.sh — Notifica decisões vencendo hoje/amanhã.
#
# Roda 12:33 diário (almoço). Se há decisões pra verificar, notifica.
# Senão, fica silencioso.
# =============================================================================

# PATH: usa o python3 do sistema (portavel Linux/macOS)
NOTIFY="$HOME/framework/scripts/sf-notify.sh"

OUTPUT=$(python3 <<'PY'
import json
from datetime import datetime, date, timedelta
from pathlib import Path

dec_file = Path.home() / "cortex" / "decisions" / "active.json"
if not dec_file.exists():
    raise SystemExit(0)

try:
    data = json.loads(dec_file.read_text())
except Exception:
    raise SystemExit(0)

today = date.today()
tomorrow = today + timedelta(days=1)

overdue = []
due_tomorrow = []
for d in data.get("decisions", []):
    if d.get("status") != "pending":
        continue
    try:
        verify = datetime.strptime(d["verify_at"], "%Y-%m-%d").date()
    except Exception:
        continue
    if verify <= today:
        overdue.append(d.get("description", "?"))
    elif verify == tomorrow:
        due_tomorrow.append(d.get("description", "?"))

if overdue:
    msg = f"{len(overdue)} decisão(ões) vencida(s): " + " | ".join(o[:60] for o in overdue[:2])
    print(f"critical|⚠️ Decisões vencidas|{msg}")
elif due_tomorrow:
    msg = f"{len(due_tomorrow)} decisão(ões) vencem amanhã: " + " | ".join(o[:60] for o in due_tomorrow[:2])
    print(f"alert|📅 Decisões vencem amanhã|{msg}")
PY
)

if [[ -n "$OUTPUT" ]]; then
  IFS='|' read -r URGENCY TITLE MSG <<< "$OUTPUT"
  "$NOTIFY" "$TITLE" "$MSG" "$URGENCY"
fi
