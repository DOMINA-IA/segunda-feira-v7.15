#!/bin/bash
# =============================================================================
# sf-notify.sh — Helper centralizador de notificações macOS para Segunda-feira.
#
# Uso:
#   sf-notify.sh "Título" "Mensagem" [info|alert|critical|silent]
#
# Sons por urgência:
#   info     → Tink   (curto, leve)
#   alert    → Glass  (médio, clara)
#   critical → Submarine (longo, atenção)
#   silent   → sem som
#
# Logs em ~/logs/notifications.log
# =============================================================================

TITLE="${1:-Segunda-feira v7.4}"
MSG="${2:-Notificação sem mensagem}"
URGENCY="${3:-info}"

LOG_DIR="$HOME/logs"
mkdir -p "$LOG_DIR"

case "$URGENCY" in
  critical) SOUND="Submarine" ;;
  alert)    SOUND="Glass" ;;
  silent)   SOUND="" ;;
  *)        SOUND="Tink" ;;
esac

# Sanitizar para osascript (escapar aspas)
TITLE_SAFE=$(echo "$TITLE" | sed 's/"/\\"/g')
MSG_SAFE=$(echo "$MSG" | sed 's/"/\\"/g')

if [[ -n "$SOUND" ]]; then
  /usr/bin/osascript -e "display notification \"$MSG_SAFE\" with title \"$TITLE_SAFE\" sound name \"$SOUND\"" 2>/dev/null
else
  /usr/bin/osascript -e "display notification \"$MSG_SAFE\" with title \"$TITLE_SAFE\"" 2>/dev/null
fi

# Log
echo "$(date '+%Y-%m-%d %H:%M:%S') [$URGENCY] $TITLE — $MSG" >> "$LOG_DIR/notifications.log"
