#!/bin/bash
# CORTEX — Adicionar nova nota ao vault
# Uso: ~/cortex/scripts/ingest.sh --title "Nome" --type project --domain traffic content --tags meta-ads clienteexemplo
#
# Tipos válidos: project, infra, pattern, playbook, feedback, rule, agent, meta

if [ -z "$1" ]; then
    echo "Uso: ingest.sh --title \"Nome\" --type tipo [--domain d1 d2] [--agents a1 a2] [--tags t1 t2] [--body \"texto\"] [--status active|paused|archived] [--skip-dedup]"
    echo ""
    echo "Tipos: project, infra, pattern, playbook, feedback, rule, agent, meta"
    echo ""
    echo "Flags:"
    echo "  --skip-dedup  Pula verificação de duplicata (default: avisa mas prossegue)"
    echo "  --strict-dedup  Aborta se duplicata for detectada"
    exit 1
fi

# Detectar flags de dedup e remover dos args para não passar ao engine
SKIP_DEDUP=false
STRICT_DEDUP=false
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --skip-dedup) SKIP_DEDUP=true ;;
        --strict-dedup) STRICT_DEDUP=true ;;
        *) ARGS+=("$arg") ;;
    esac
done

# Adaptive Memory Updates (inspirado em Mem0): checar duplicata antes de criar
if [ "$SKIP_DEDUP" = false ]; then
    DEDUP_FLAGS=()
    [ "$STRICT_DEDUP" = true ] && DEDUP_FLAGS+=(--strict)
    python3 ~/cortex/scripts/dedup-check.py "${ARGS[@]}" "${DEDUP_FLAGS[@]}"
    DEDUP_EXIT=$?
    if [ $DEDUP_EXIT -eq 1 ]; then
        echo "❌ Ingest abortado pelo dedup-check (modo --strict-dedup)."
        echo "   Use --skip-dedup para forçar criação."
        exit 1
    fi
fi

python3 ~/cortex/scripts/cortex_engine.py ingest "${ARGS[@]}"

# Rebuild indices após ingestão
echo "🔄 Reconstruindo índices..."
python3 ~/cortex/scripts/cortex_engine.py build-index 2>/dev/null
