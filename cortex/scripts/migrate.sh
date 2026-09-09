#!/bin/bash
# CORTEX — Migrar memórias existentes para o vault
# Uso: ~/cortex/scripts/migrate.sh
#
# Migra arquivos de ~/.claude/projects/-HOME-/memory/
# para ~/cortex/vault/ com frontmatter CORTEX.

MEMORY_DIR="$HOME/.claude/projects/-HOME-/memory"
VAULT_DIR="$HOME/cortex/vault"

echo "🔄 CORTEX — Migração de Memórias"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Origem: $MEMORY_DIR"
echo "Destino: $VAULT_DIR"
echo ""

# Contar arquivos .md (excluindo MEMORY.md)
count=$(find "$MEMORY_DIR" -name "*.md" ! -name "MEMORY.md" | wc -l | tr -d ' ')
echo "📄 $count arquivos de memória encontrados"
echo ""

if [ "$count" -eq 0 ]; then
    echo "Nenhum arquivo para migrar."
    exit 0
fi

echo "A migração vai:"
echo "  1. Ler cada arquivo de memória"
echo "  2. Detectar tipo (user, feedback, project, reference)"
echo "  3. Converter para formato CORTEX com frontmatter"
echo "  4. Salvar no vault na pasta correta"
echo "  5. Reconstruir índices"
echo ""
echo "⚠️  Os arquivos originais NÃO serão deletados."
echo ""

# Chamar engine Python para migração real
python3 ~/cortex/scripts/migrate_engine.py

echo ""
echo "🔄 Reconstruindo índices..."
python3 ~/cortex/scripts/cortex_engine.py build-index

echo ""
echo "✅ Migração completa!"
