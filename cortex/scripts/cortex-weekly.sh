#!/bin/bash
# CORTEX Weekly — Manutenção semanal profunda
# Roda semanalmente via crontab (domingo 23:00 BRT)
#
# Faz tudo do cron diário + auto-linker + relatório completo

CORTEX_HOME="$HOME/cortex"
LOG_FILE="$HOME/logs/cortex-weekly.log"

echo "$(date '+%Y-%m-%d %H:%M:%S') — CORTEX Weekly iniciando..." >> "$LOG_FILE"

# 1. Auto-linker (detecta novas relações)
echo "--- Auto-linker ---" >> "$LOG_FILE"
python3 "$CORTEX_HOME/scripts/auto_link.py" >> "$LOG_FILE" 2>&1

# 2. Rebuild completo (índices + briefings)
echo "--- Rebuild ---" >> "$LOG_FILE"
python3 "$CORTEX_HOME/scripts/cortex_engine.py" build-index >> "$LOG_FILE" 2>&1
python3 "$CORTEX_HOME/scripts/cortex_engine.py" build-briefings >> "$LOG_FILE" 2>&1

# 3. Health report completo
echo "--- Health Report ---" >> "$LOG_FILE"
python3 "$CORTEX_HOME/scripts/cortex_engine.py" health >> "$LOG_FILE" 2>&1

# 4. Stats
echo "--- Stats ---" >> "$LOG_FILE"
python3 "$CORTEX_HOME/scripts/cortex_engine.py" stats >> "$LOG_FILE" 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') — CORTEX Weekly finalizado." >> "$LOG_FILE"
echo "===" >> "$LOG_FILE"
