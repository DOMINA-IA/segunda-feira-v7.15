#!/bin/bash
# =============================================================================
# inema-weekly-scout.sh — Scrape semanal INEMA + ingest CORTEX + auto-reauth alert.
#
# Roda toda sexta de manhã. Se a sessão Telegram tiver expirado,
# emite sinal no broadcast (aparece no próximo prompt do ${CEO_NAME} via CORTEX hook).
#
# Cron sugerido: 7 9 * * 5  (sextas 09:07 BRT)
# =============================================================================

set -uo pipefail

# Cron usa /usr/bin/python3 (sem pyyaml). Forçar framework Python com deps.
# PATH: usa o python3 do sistema (portavel Linux/macOS)
SCRAPER_DIR="$HOME/projetos/telegram-scraper"
CORTEX_SCRIPTS="$HOME/cortex/scripts"
INBOX="$HOME/cortex/inbox"
LOG_DIR="$HOME/logs"
SIGNAL_FILE="$HOME/broadcast/signals.json"

mkdir -p "$LOG_DIR" "$INBOX"

DATE_TAG=$(date +%Y%m%d)
TS=$(date +%Y-%m-%d_%H:%M:%S)

echo "════════════════════════════════════════════════"
echo " INEMA WEEKLY SCOUT — $TS"
echo "════════════════════════════════════════════════"

emit_signal() {
  local sig_type="$1"
  local action="$2"
  python3 - <<PY 2>/dev/null
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
    "id": f"sig_inema_weekly_{datetime.now().strftime('%Y%m%d_%H%M')}",
    "type": "$sig_type",
    "agent": "@inema-scout",
    "action": """$action""",
    "ts": datetime.now().isoformat(),
    "consumed": False,
})
p.write_text(json.dumps(data, indent=2, ensure_ascii=False))
PY
}

# ── Etapa 1: Scrape incremental ───────────────────────────────────────────
echo ""
echo "→ Etapa 1/4: Scrape incremental dos 32 grupos"

# Diretório ausente é falha SILENCIOSA se só ecoar e sair — foi o que aconteceu
# entre 10-Jul e 07-Ago-2026 (reorg moveu o projeto para ~/projetos/ e este cd
# morria antes de qualquer alerta, 5 sextas seguidas). Alertar SEMPRE.
if [[ ! -d "$SCRAPER_DIR" ]]; then
  echo "  ❌ ERRO: $SCRAPER_DIR não existe"
  ALERT="INEMA scout ABORTOU em $TS — diretório $SCRAPER_DIR não existe. Provável reorg de filesystem: rodar grep -rl '~/telegram-scraper' em ~/framework/scripts ~/.claude ~/cortex/scripts e repontar."
  emit_signal "ALERT" "$ALERT"
  "$HOME/framework/scripts/sf-notify.sh" "🚨 INEMA: diretório sumiu" "$SCRAPER_DIR não existe — path stale após reorg?" "critical"
  exit 1
fi
cd "$SCRAPER_DIR" || exit 1

if python3 scraper.py 2>&1 | tee "$LOG_DIR/inema-weekly-scrape.log"; then
  echo "  ✅ Scrape ok"
else
  RC=$?
  echo "  ⚠️  Scrape falhou (rc=$RC) — provável sessão Telegram expirada"
  ALERT="INEMA scrape FALHOU em $TS — provável reauth necessário. Rode: cd ~/projetos/telegram-scraper && python3 request_code.py (recebe SMS) → python3 auth_step2.py CODIGO → python3 scraper.py"
  emit_signal "ALERT" "$ALERT"
  /usr/bin/say -v Luciana "Atenção. INEMA scout precisa reautenticar a sessão Telegram." 2>/dev/null || true
  "$HOME/framework/scripts/sf-notify.sh" "🚨 INEMA precisa reauth" "Sessão Telegram expirou. Rode request_code.py para receber SMS." "critical"
  exit $RC
fi

# ── Etapa 2: Re-indexar canais no CORTEX ──────────────────────────────────
echo ""
echo "→ Etapa 2/4: Atualizar 33 notas-índice INEMA-KB-* no CORTEX"
python3 "$CORTEX_SCRIPTS/ingest_telegram.py" 2>&1 | tail -10

# ── Etapa 3: Build index + auto-link ──────────────────────────────────────
echo ""
echo "→ Etapa 3/4: Rebuild CORTEX (index + auto-link + briefings)"
python3 "$CORTEX_SCRIPTS/cortex_engine.py" build-index 2>&1 | tail -3
python3 "$CORTEX_SCRIPTS/auto_link.py" 2>&1 | tail -3
python3 "$CORTEX_SCRIPTS/cortex_engine.py" build-briefings 2>&1 | tail -3

# ── Etapa 4: Sinal de sucesso ─────────────────────────────────────────────
echo ""
echo "→ Etapa 4/4: Emitir sinal de sucesso no broadcast"
emit_signal "PROACTIVE_ACTION" "INEMA scout semanal completo: scrape + ingest + index. Próxima ação: invocar @inema-scout para gerar digest acionável das novidades."

echo ""
echo "════════════════════════════════════════════════"
echo " ✅ INEMA WEEKLY SCOUT COMPLETO — $(date +%H:%M:%S)"
echo "════════════════════════════════════════════════"
echo ""
echo "Próximo passo manual: abrir Claude Code e pedir:"
echo "  '@inema-scout faz o digest da semana, foca no que mudou'"

"$HOME/framework/scripts/sf-notify.sh" "✅ INEMA scout completo" "Scrape semanal feito + ingest CORTEX. Peça ao @inema-scout um digest." "alert"

exit 0
