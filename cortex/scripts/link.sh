#!/bin/bash
# CORTEX — Criar link tipado entre duas notas
# Uso: ~/cortex/scripts/link.sh source_id target_id tipo
#
# Tipos: depends_on, extends, supersedes, contradicts, instance_of, learned_from, related

if [ -z "$3" ]; then
    echo "Uso: link.sh source_id target_id tipo"
    echo ""
    echo "Tipos de link:"
    echo "  depends_on    — Preciso saber isso primeiro"
    echo "  extends       — Expande esse conhecimento"
    echo "  supersedes    — Substituiu essa nota"
    echo "  contradicts   — Aprendizado oposto"
    echo "  instance_of   — Caso específico de padrão"
    echo "  learned_from  — Extraído desse feedback"
    echo "  related       — Relacionado genericamente"
    exit 1
fi

python3 ~/cortex/scripts/cortex_engine.py link "$1" "$2" "$3"

# Rebuild graph
echo "🔄 Atualizando grafo..."
python3 ~/cortex/scripts/cortex_engine.py build-index 2>/dev/null
