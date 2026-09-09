#!/bin/bash
# CORTEX — Gera briefings pré-computados por agente
# Uso: ~/cortex/scripts/build-briefings.sh
#
# FIX 25-Abr: cron usa /usr/bin/python3 (sem pyyaml). Forçar Python framework com pyyaml.
# PATH: usa o python3 do sistema (portavel Linux/macOS)
echo "📋 CORTEX — Gerando briefings..."
python3 ~/cortex/scripts/cortex_engine.py build-index 2>/dev/null
python3 ~/cortex/scripts/cortex_engine.py build-briefings
