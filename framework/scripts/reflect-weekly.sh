#!/bin/bash
# =============================================================================
# reflect-weekly.sh — Reflexão metacognitiva semanal dos top agentes.
#
# Roda toda semana e gera 1 reflexão em ~/consciousness/metacognition/reflections/
# para cada agente ativo. Sem reflexão, heurísticas não evoluem.
#
# Cron sugerido: 17 23 * * 0  (domingos 23:17 BRT — fora do horário do pipeline noturno)
# =============================================================================

set -uo pipefail

REFLECT="$HOME/consciousness/scripts/reflect.sh"
LOG_DIR="$HOME/logs"
mkdir -p "$LOG_DIR"

DATE_TAG=$(date +%Y-%m-%d)
TS=$(date +%H:%M:%S)

echo "════════════════════════════════════════════════"
echo " REFLECT WEEKLY — $DATE_TAG $TS"
echo "════════════════════════════════════════════════"

# Top agentes por volume de episódios — quem mais aparece se beneficia mais.
AGENTS=(
  "@sf-master"
  "@dev"
  "@analyst"
  "@traffic"
  "@content"
  "@inema-scout"
  "@fabio-soares"
  "@offer-engineer"
)

ok=0
fail=0
for agent in "${AGENTS[@]}"; do
  echo ""
  echo "→ Refletindo: $agent"
  if "$REFLECT" --agent "$agent" --days 7 2>&1; then
    ok=$((ok + 1))
  else
    fail=$((fail + 1))
    echo "  ⚠️  Reflexão falhou para $agent (provavelmente sem episódios na janela)"
  fi
done

echo ""
echo "════════════════════════════════════════════════"
echo " Resultado: $ok ok | $fail falhou"
echo "════════════════════════════════════════════════"

"$HOME/framework/scripts/sf-notify.sh" "🧘 Reflexão semanal pronta" "$ok agentes refletiram sobre últimos 7 dias. Veja em ~/consciousness/metacognition/reflections/" "info"

# Emitir sinal no broadcast pra próxima sessão saber que rodou
if [[ -d "$HOME/broadcast" ]]; then
  SIGNAL_FILE="$HOME/broadcast/signals.json"
  if [[ -f "$SIGNAL_FILE" ]]; then
    python3 - <<PY
import json
from datetime import datetime
from pathlib import Path
p = Path("$SIGNAL_FILE")
try:
    data = json.loads(p.read_text())
except Exception:
    data = []
if not isinstance(data, list):
    data = []
data.append({
    "id": f"sig_reflect_weekly_{datetime.now().strftime('%Y%m%d')}",
    "type": "REFLECT_COMPLETE",
    "agent": "@cron-weekly",
    "action": "Reflexão semanal rodou — $ok agentes processados",
    "ts": datetime.now().isoformat(),
    "consumed": False,
})
p.write_text(json.dumps(data, indent=2, ensure_ascii=False))
PY
  fi
fi

exit 0
