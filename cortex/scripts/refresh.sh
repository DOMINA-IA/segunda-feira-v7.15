#!/bin/bash
# CORTEX — Marcar nota como verificada (reseta freshness)
# Uso: ~/cortex/scripts/refresh.sh note_id

if [ -z "$1" ]; then
    echo "Uso: refresh.sh note_id"
    echo "Marca a nota como verificada hoje, resetando o freshness score."
    exit 1
fi

python3 ~/cortex/scripts/cortex_engine.py refresh "$1"
