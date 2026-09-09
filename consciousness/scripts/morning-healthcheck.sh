#!/bin/bash
# Healthcheck matinal — se pipeline noturno não rodou, roda agora.
# Garante que o framework NUNCA passa um dia sem assimilar.

set -u
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

STAMP_DIR="$HOME/consciousness/.pipeline-stamps"
LOG="$HOME/logs/morning-healthcheck.log"
mkdir -p "$HOME/logs"

TODAY=$(date +%Y-%m-%d)
YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d)
STAMP_TODAY="$STAMP_DIR/pipeline-$TODAY.done"
STAMP_YESTERDAY="$STAMP_DIR/pipeline-$YESTERDAY.done"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Healthcheck iniciado" >> "$LOG"

# Se pipeline de ontem não rodou, rodar agora (catch-up)
if [[ ! -f "$STAMP_YESTERDAY" ]]; then
    echo "[$(date '+%H:%M:%S')] Pipeline de $YESTERDAY não rodou. Executando catch-up..." >> "$LOG"

    # Alertar que está em catch-up
    TOKEN=$(grep -E '^(TELEGRAM_BOT_TOKEN|BOT_TOKEN)=' "$HOME/.claude/channels/telegram/.env" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
    CHAT=$(python3 -c "import json; print(json.load(open('$HOME/.claude/channels/telegram/access.json'))['allowFrom'][0])" 2>/dev/null)
    if [[ -n "$TOKEN" && -n "$CHAT" ]]; then
        curl -sS --max-time 10 "https://api.telegram.org/bot${TOKEN}/sendMessage" \
            --data-urlencode "chat_id=${CHAT}" \
            --data-urlencode "parse_mode=HTML" \
            --data-urlencode "text=☀️ <b>Healthcheck matinal</b>%0APipeline de $YESTERDAY não rodou (laptop dormindo?). Iniciando catch-up agora..." \
            >/dev/null 2>&1
    fi

    bash "$HOME/consciousness/scripts/run-nightly-pipeline.sh" --force >> "$LOG" 2>&1
    echo "[$(date '+%H:%M:%S')] Catch-up concluído" >> "$LOG"
else
    echo "[$(date '+%H:%M:%S')] Pipeline de $YESTERDAY OK — nada a fazer" >> "$LOG"
fi

# Limpa stamps antigos (>30 dias)
find "$STAMP_DIR" -name "pipeline-*.done" -mtime +30 -delete 2>/dev/null

exit 0
