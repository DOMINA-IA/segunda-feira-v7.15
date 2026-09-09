#!/bin/bash
# CORTEX Pulse Check — Coleta dados do negócio 2x/dia
# Roda via cron 09:00 e 18:00 BRT (12:00 e 21:00 UTC)

LOG_FILE="$HOME/logs/cortex-pulse.log"
echo "$(date '+%Y-%m-%d %H:%M:%S') — Pulse check..." >> "$LOG_FILE"

python3 ~/cortex/scripts/pulse_check.py >> "$LOG_FILE" 2>&1

# Gerar predições após pulse
python3 ~/cortex/scripts/predictor.py >> "$LOG_FILE" 2>&1

# Rodar decision engine para detectar alertas
python3 ~/cortex/scripts/decision_engine.py alerts >> "$LOG_FILE" 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') — Pulse + predict + alerts done." >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"
