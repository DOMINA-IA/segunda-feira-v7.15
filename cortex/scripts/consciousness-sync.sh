#!/bin/bash
# CORTEX ← Consciousness Sync
# Converte heurísticas e fatos consolidados em notas CORTEX
# Roda após consolidação noturna (23:30 BRT) ou sob demanda

CORTEX_HOME="$HOME/cortex"
CONSCIOUSNESS_HOME="$HOME/consciousness"
LOG_FILE="$HOME/logs/cortex-consciousness-sync.log"

echo "$(date '+%Y-%m-%d %H:%M:%S') — Consciousness → CORTEX sync iniciando..." >> "$LOG_FILE"

python3 "$CORTEX_HOME/scripts/consciousness_sync.py" >> "$LOG_FILE" 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') — Sync finalizado." >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"
