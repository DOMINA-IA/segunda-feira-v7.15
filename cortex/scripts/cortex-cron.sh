#!/bin/bash
# CORTEX Cron — Manutenção automática do vault
# Roda diariamente via crontab
#
# Faz:
# 1. Rebuild índices (graph, tags, freshness, search, health)
# 2. Rebuild briefings por agente
# 3. Health check — detecta stale, orphans, contradições
# 4. Emite sinal no Nervous System se ação necessária

CORTEX_HOME="$HOME/cortex"
LOG_FILE="$HOME/logs/cortex-cron.log"
SIGNALS_FILE="$HOME/broadcast/signals.json"

echo "$(date '+%Y-%m-%d %H:%M:%S') — CORTEX Cron iniciando..." >> "$LOG_FILE"

# 1. Rebuild índices
python3 "$CORTEX_HOME/scripts/cortex_engine.py" build-index >> "$LOG_FILE" 2>&1

# 2. Rebuild briefings
python3 "$CORTEX_HOME/scripts/cortex_engine.py" build-briefings >> "$LOG_FILE" 2>&1

# 3. Health check — capturar métricas
HEALTH=$(python3 -c "
import json
from pathlib import Path
h = json.loads((Path.home() / 'cortex/index/health.json').read_text())
stale = h.get('stale', 0)
review = h.get('needs_review', 0)
orphans = h.get('orphan_count', 0)
contradictions = h.get('contradictions', 0)
score = h.get('health_score', 0)
print(f'{stale}|{review}|{orphans}|{contradictions}|{score}')
" 2>/dev/null)

STALE=$(echo "$HEALTH" | cut -d'|' -f1)
REVIEW=$(echo "$HEALTH" | cut -d'|' -f2)
ORPHANS=$(echo "$HEALTH" | cut -d'|' -f3)
CONTRADICTIONS=$(echo "$HEALTH" | cut -d'|' -f4)
SCORE=$(echo "$HEALTH" | cut -d'|' -f5)

echo "$(date '+%Y-%m-%d %H:%M:%S') — Health: score=$SCORE stale=$STALE review=$REVIEW orphans=$ORPHANS contradictions=$CONTRADICTIONS" >> "$LOG_FILE"

# 4. Emitir sinal se ação necessária
if [ "${STALE:-0}" -gt 0 ] || [ "${REVIEW:-0}" -gt 3 ] || [ "${CONTRADICTIONS:-0}" -gt 0 ]; then
    TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    SIGNAL_ID="cortex_health_$(date '+%Y%m%d')"

    # Criar sinal
    python3 -c "
import json
from pathlib import Path

signals_file = Path.home() / 'broadcast/signals.json'
try:
    signals = json.loads(signals_file.read_text())
except:
    signals = []

# Remover sinal anterior do CORTEX (evitar duplicatas)
signals = [s for s in signals if not str(s.get('id', '')).startswith('cortex_health_')]

signal = {
    'id': '${SIGNAL_ID}',
    'type': 'CORTEX_HEALTH_ALERT',
    'source': '@cortex',
    'priority': 'normal',
    'data': {
        'health_score': ${SCORE:-0},
        'stale_notes': ${STALE:-0},
        'needs_review': ${REVIEW:-0},
        'orphans': ${ORPHANS:-0},
        'contradictions': ${CONTRADICTIONS:-0}
    },
    'message': 'CORTEX: ${STALE:-0} notas stale, ${REVIEW:-0} precisam revisão, ${CONTRADICTIONS:-0} contradições',
    'timestamp': '${TIMESTAMP}',
    'consumed_by': []
}
signals.append(signal)
signals_file.write_text(json.dumps(signals, indent=2, ensure_ascii=False))
print('Sinal emitido: ${SIGNAL_ID}')
" >> "$LOG_FILE" 2>&1
fi

# 5. Git auto-commit (versionar mudanças do vault)
cd "$CORTEX_HOME" && git add vault/ index/ briefings/ -A 2>/dev/null
CHANGES=$(cd "$CORTEX_HOME" && git diff --cached --stat 2>/dev/null | tail -1)
if [ -n "$CHANGES" ] && [ "$CHANGES" != "" ]; then
    cd "$CORTEX_HOME" && git commit -m "auto: $(date '+%Y-%m-%d') — $CHANGES" >> "$LOG_FILE" 2>&1
    echo "$(date '+%Y-%m-%d %H:%M:%S') — Git commit: $CHANGES" >> "$LOG_FILE"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') — Git: sem mudanças" >> "$LOG_FILE"
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') — CORTEX Cron finalizado." >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"
