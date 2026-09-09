#!/bin/bash
# CORTEX — Busca por intenção no vault
# Uso: ~/cortex/scripts/query.sh "CPL campanha CLIENTE_EXEMPLO"
#       ~/cortex/scripts/query.sh --agent traffic
#       ~/cortex/scripts/query.sh --tag meta-ads

if [ -z "$1" ]; then
    echo "Uso:"
    echo "  query.sh \"termo de busca\"     Busca por keywords"
    echo "  query.sh --agent nome          Notas do agente"
    echo "  query.sh --tag tag             Notas com tag"
    exit 1
fi

case "$1" in
    --agent)
        python3 ~/cortex/scripts/cortex_engine.py query-agent "$2"
        ;;
    --tag)
        python3 ~/cortex/scripts/cortex_engine.py query-tag "$2"
        ;;
    *)
        python3 ~/cortex/scripts/cortex_engine.py query "$@"
        ;;
esac
