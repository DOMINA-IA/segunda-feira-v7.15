#!/bin/bash
# =============================================================================
# telegram-session-monitor.sh — Vigia a sessão Telethon do INEMA scraper.
#
# POR QUE EXISTE: em 04-Set-2026 o inema-weekly-scout falhou às 09:07 por sessão
# expirada. O alerta foi emitido corretamente, mas ficou 14h invisível — o Pulse
# só mostrava "Sinais ativos: N". Descobriu-se ao pedir uma raspagem manual, com
# 14 dias de mensagens perdidas.
#
# Roda QUINTA, véspera do scout de sexta: reautenticar exige código SMS, ou seja,
# depende do humano. Avisar na sexta de manhã já é tarde.
#
# Cron: 0 9 * * 4   (quinta 09:00 BRT)
#
# Exit codes — falha de execução NUNCA se confunde com sessão OK:
#   0 = sessão válida e raspagem recente
#   1 = sessão expirada (ação humana necessária: código SMS)
#   2 = raspagem velha demais apesar de sessão válida (cron do scout pode estar quebrado)
#   3 = erro de execução (script/deps/diretório) — desconhecido, não é "OK"
# =============================================================================

set -uo pipefail
# PATH: usa o python3 do sistema (portavel Linux/macOS)
SCRAPER_DIR="$HOME/projetos/telegram-scraper"
SIGNAL_FILE="$HOME/broadcast/signals.json"
NOTIFY="$HOME/framework/scripts/sf-notify.sh"
MAX_IDADE_DIAS=10   # scout roda semanal; >10 dias significa que já pulou uma rodada

TS=$(date +%Y-%m-%d_%H:%M:%S)

emit_signal() {
  python3 - "$1" "$2" <<'PY' 2>/dev/null
import json, sys
from datetime import datetime
from pathlib import Path
sig_type, action = sys.argv[1], sys.argv[2]
p = Path.home()/"broadcast"/"signals.json"
try:
    data = json.loads(p.read_text())
except Exception:
    data = []
if not isinstance(data, list):
    data = []
# Não empilhar o mesmo alerta toda semana: substitui o anterior ainda não consumido
data = [s for s in data if not (s.get("id","").startswith("sig_tgsession_") and not s.get("consumed"))]
data.append({
    "id": f"sig_tgsession_{datetime.now().strftime('%Y%m%d_%H%M')}",
    "type": sig_type, "agent": "@inema-scout",
    "action": action, "ts": datetime.now().isoformat(), "consumed": False,
})
p.write_text(json.dumps(data, indent=2, ensure_ascii=False))
PY
}

alerta() {  # $1=titulo  $2=mensagem  $3=fala
  emit_signal "ALERT" "$2"
  [[ -x "$NOTIFY" ]] && "$NOTIFY" "$1" "$2" "critical"
  /usr/bin/say -v Luciana "$3" 2>/dev/null || true
}

# ── Guarda: o projeto existe? ────────────────────────────────────────────────
if [[ ! -d "$SCRAPER_DIR" ]]; then
  alerta "🚨 Telegram monitor" \
    "Monitor de sessão ABORTOU em $TS — $SCRAPER_DIR não existe. Path stale após reorg? Rodar: grep -rl telegram-scraper ~/framework/scripts ~/.claude" \
    "Monitor do Telegram falhou. Diretório do scraper não existe."
  exit 3
fi
cd "$SCRAPER_DIR" || exit 3

# ── Checagem 1: a sessão está autorizada? ────────────────────────────────────
# Exit 0 = autorizada · 1 = expirada · 3 = erro de execução (deps, .env, rede).
python3 - <<'PY'
import os, sys, asyncio
from pathlib import Path
try:
    env = Path('.env')
    if not env.exists(): sys.exit(3)
    for l in env.read_text().splitlines():
        if '=' in l and not l.startswith('#'):
            k, v = l.split('=', 1); os.environ.setdefault(k.strip(), v.strip())
    from telethon import TelegramClient
except Exception:
    sys.exit(3)

async def main():
    try:
        c = TelegramClient('telegram_session', os.environ['TELEGRAM_API_ID'], os.environ['TELEGRAM_API_HASH'])
        await c.connect()
        ok = await c.is_user_authorized()
        await c.disconnect()
    except Exception:
        sys.exit(3)          # rede/credencial: desconhecido, não é "expirada" nem "OK"
    sys.exit(0 if ok else 1)

asyncio.run(main())
PY
RC=$?

if [[ $RC -eq 1 ]]; then
  alerta "🚨 Telegram: sessão expirada" \
    "Sessão Telethon EXPIRADA (checado $TS). O scout de amanhã vai falhar. Reautenticar HOJE: cd ~/projetos/telegram-scraper && python3 request_code.py → passar o código ao Claude Code → bash absorver-inema.sh" \
    "Atenção. A sessão do Telegram expirou. O scout de amanhã vai falhar sem reautenticação."
  echo "[$TS] SESSAO EXPIRADA"
  exit 1
elif [[ $RC -eq 3 ]]; then
  alerta "🚨 Telegram monitor com erro" \
    "Monitor não CONSEGUIU verificar a sessão em $TS (deps, .env ou rede). Estado desconhecido — não assumir que está OK. Rodar manualmente: cd ~/projetos/telegram-scraper && python3 request_code.py" \
    "Monitor do Telegram não conseguiu verificar a sessão." 
  echo "[$TS] ERRO DE EXECUCAO"
  exit 3
fi

# ── Checagem 2: a raspagem está recente? ─────────────────────────────────────
# Sessão válida não basta: o cron do scout pode estar quebrado por outro motivo.
IDADE=$(python3 -c "
import json,sys
from datetime import datetime,timezone
try:
    d=json.load(open('output/summary.json'))['scrape_date']
    dt=datetime.fromisoformat(d)
    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
    print(int((datetime.now(timezone.utc)-dt).days))
except Exception: print(-1)
" 2>/dev/null)

if [[ "$IDADE" == "-1" ]]; then
  alerta "🚨 Telegram: sem histórico de raspagem" \
    "Sessão OK, mas output/summary.json ilegível em $TS. Raspagem pode nunca ter rodado." \
    "Não foi possível ler o histórico de raspagem do Telegram."
  echo "[$TS] SUMMARY ILEGIVEL"
  exit 2
fi

if [[ "$IDADE" -gt "$MAX_IDADE_DIAS" ]]; then
  alerta "⚠️ Telegram: raspagem parada" \
    "Sessão VÁLIDA, mas a última raspagem tem $IDADE dias (limite $MAX_IDADE_DIAS). O scout de sexta pode estar falhando por outro motivo — checar ~/logs/inema-weekly.log." \
    "A raspagem do Telegram está parada há $IDADE dias, mesmo com a sessão válida."
  echo "[$TS] RASPAGEM VELHA: $IDADE dias"
  exit 2
fi

echo "[$TS] OK — sessão válida, última raspagem há $IDADE dia(s)"
exit 0
