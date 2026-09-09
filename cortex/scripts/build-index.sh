#!/bin/bash
# CORTEX — Reconstrói todos os índices do vault
# Uso: ~/cortex/scripts/build-index.sh

echo "🧠 CORTEX — Construindo índices..."
python3 ~/cortex/scripts/cortex_engine.py build-index
