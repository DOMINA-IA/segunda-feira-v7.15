#!/bin/bash
# CORTEX — Relatório de saúde do vault
# Uso: ~/cortex/scripts/health-check.sh

echo "🧠 CORTEX — Health Check"
echo ""

# Rebuild indices primeiro para dados atualizados
python3 ~/cortex/scripts/cortex_engine.py build-index 2>/dev/null
python3 ~/cortex/scripts/cortex_engine.py health
