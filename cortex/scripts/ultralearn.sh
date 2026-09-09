#!/usr/bin/env bash
# ultralearn.sh — Scan profundo de codebase + populate CORTEX
# Origem: ruflo worker `ultralearn` + INEMA multi-LLM strategy.
#
# Pipeline:
#   1. INVENTORY  ($0)         find + classificação por extensão
#   2. EXTRACT    (Gemini Flash | cheap mode: stats locais)
#   3. SYNTHESIZE (Sonnet | cheap mode: skip)
#   4. INDEX      ($0)         build-index + build-briefings
#
# Uso:
#   ultralearn.sh --project ~/clientes/X --client X
#   ultralearn.sh --project ~/clientes/X --client X --deep
#   ultralearn.sh --project ~/clientes/X --client X --cheap

set -uo pipefail

PROJECT=""
CLIENT=""
DEEP=0
CHEAP=0

while [ $# -gt 0 ]; do
  case "$1" in
    --project) PROJECT="$2"; shift 2 ;;
    --project=*) PROJECT="${1#--project=}"; shift ;;
    --client) CLIENT="$2"; shift 2 ;;
    --client=*) CLIENT="${1#--client=}"; shift ;;
    --deep) DEEP=1; shift ;;
    --cheap) CHEAP=1; shift ;;
    *) shift ;;
  esac
done

if [ -z "$PROJECT" ] || [ ! -d "$PROJECT" ]; then
  echo "⚠️  --project obrigatório (diretório válido)"
  exit 1
fi

SLUG=$(basename "$PROJECT" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9' '-' | sed 's/--*/-/g; s/^-//; s/-$//')
DATE=$(date +%Y-%m-%d)
REPORT_DIR="$HOME/cortex/reports"
NOTES_DIR="$HOME/cortex/vault/projects"
TEMP_DIR=$(mktemp -d)
mkdir -p "$REPORT_DIR" "$NOTES_DIR"

echo "🔍 ultralearn — project: $PROJECT | client: ${CLIENT:-n/a} | slug: $SLUG"
[ $DEEP -eq 1 ] && echo "   modo: DEEP"
[ $CHEAP -eq 1 ] && echo "   modo: CHEAP (sem Sonnet)"

# ════════════════════════════════════════════════════════════════════
# FASE 1 — INVENTORY ($0)
# ════════════════════════════════════════════════════════════════════
echo ""
echo "📋 [1/4] Inventory..."
INVENTORY_FILE="$TEMP_DIR/files.txt"
find "$PROJECT" -type f \( \
  -name "*.md" -o -name "*.ts" -o -name "*.tsx" \
  -o -name "*.js" -o -name "*.jsx" -o -name "*.mjs" \
  -o -name "*.py" -o -name "*.go" -o -name "*.rs" -o -name "*.rb" \
  -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.toml" \
  -o -name "*.sql" -o -name "Dockerfile" -o -name "*.env.example" \
  -o -name "package.json" -o -name "Cargo.toml" -o -name "pyproject.toml" \
\) \
  -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/dist/*" \
  -not -path "*/build/*" -not -path "*/__pycache__/*" -not -path "*/.next/*" \
  -not -path "*/venv/*" -not -path "*/.venv/*" \
  > "$INVENTORY_FILE" 2>/dev/null

TOTAL=$(wc -l < "$INVENTORY_FILE" | tr -d ' ')
echo "   $TOTAL arquivos descobertos"

# Distribuição por extensão
EXT_DIST=$(awk -F. '{print $NF}' "$INVENTORY_FILE" | sort | uniq -c | sort -rn | head -10)

# ════════════════════════════════════════════════════════════════════
# FASE 2 — EXTRACT (Gemini Flash em prod | local em cheap mode)
# ════════════════════════════════════════════════════════════════════
echo ""
echo "🔬 [2/4] Extract..."
DEPS_FILE="$TEMP_DIR/deps.txt"

# Detectar package managers e listar dependências
if [ -f "$PROJECT/package.json" ]; then
  jq -r '.dependencies, .devDependencies // {} | keys[]' "$PROJECT/package.json" 2>/dev/null | sort -u > "$DEPS_FILE" || true
fi
if [ -f "$PROJECT/Cargo.toml" ]; then
  grep -E '^[a-z-]+ = ' "$PROJECT/Cargo.toml" 2>/dev/null | awk -F' = ' '{print $1}' >> "$DEPS_FILE" || true
fi
if [ -f "$PROJECT/pyproject.toml" ] || [ -f "$PROJECT/requirements.txt" ]; then
  cat "$PROJECT/requirements.txt" 2>/dev/null | awk -F'==' '{print $1}' >> "$DEPS_FILE" || true
fi

DEP_COUNT=$(wc -l < "$DEPS_FILE" 2>/dev/null | tr -d ' ' || echo "0")
echo "   $DEP_COUNT dependências detectadas"

# Detectar stack
STACK=""
[ -f "$PROJECT/package.json" ] && STACK="${STACK}Node.js, "
[ -f "$PROJECT/Cargo.toml" ] && STACK="${STACK}Rust, "
[ -f "$PROJECT/pyproject.toml" ] || [ -f "$PROJECT/requirements.txt" ] && STACK="${STACK}Python, "
[ -f "$PROJECT/go.mod" ] && STACK="${STACK}Go, "
[ -f "$PROJECT/Gemfile" ] && STACK="${STACK}Ruby, "
[ -f "$PROJECT/Dockerfile" ] && STACK="${STACK}Docker, "
STACK="${STACK%, }"
[ -z "$STACK" ] && STACK="(não detectado)"

# Entry points
ENTRY_POINTS=$(find "$PROJECT" -maxdepth 3 -type f \( -name "main.*" -o -name "index.*" -o -name "app.*" -o -name "server.*" -o -name "__main__.py" \) -not -path "*/node_modules/*" 2>/dev/null | head -5)

# README?
README_PRESENT="não"
[ -f "$PROJECT/README.md" ] && README_PRESENT="sim ($(wc -l < $PROJECT/README.md | tr -d ' ') linhas)"

# Tests?
TEST_DIRS=$(find "$PROJECT" -type d \( -name "tests" -o -name "test" -o -name "__tests__" -o -name "spec" \) -not -path "*/node_modules/*" 2>/dev/null | head -3)

# ════════════════════════════════════════════════════════════════════
# FASE 3 — SYNTHESIZE (Sonnet em prod | skip em cheap)
# ════════════════════════════════════════════════════════════════════
echo ""
echo "🧠 [3/4] Synthesize..."

ARCH_NOTE="$NOTES_DIR/${SLUG}-architecture.md"
STACK_NOTE="$NOTES_DIR/${SLUG}-stack.md"
HOTPATHS_NOTE="$NOTES_DIR/${SLUG}-hot-paths.md"

cat > "$ARCH_NOTE" <<EOF
---
id: ${SLUG}-architecture
type: architecture
axis: meta
project: ${SLUG}
${CLIENT:+client: ${CLIENT}}
date: ${DATE}
generated_by: ultralearn.sh
---

# ${SLUG} — Arquitetura (auto-gerada)

## Resumo
- **Total de arquivos:** ${TOTAL}
- **Stack detectada:** ${STACK}
- **README presente:** ${README_PRESENT}
- **Dependências:** ${DEP_COUNT}

## Distribuição por extensão (top 10)

\`\`\`
${EXT_DIST}
\`\`\`

## Entry points detectados

\`\`\`
${ENTRY_POINTS:-nenhum identificado}
\`\`\`

## Diretórios de teste

\`\`\`
${TEST_DIRS:-nenhum detectado}
\`\`\`

## Próximos passos (modo --deep)

$([ $DEEP -eq 1 ] && echo "- Análise de bounded contexts (DDD)" || echo "_Execute novamente com \`--deep\` para análise estrutural profunda._")

## Links

- [[cortex-system]]
- [[framework-vps-deployment-fase-a-2026-05-22]]
EOF
echo "   ✓ $ARCH_NOTE"

cat > "$STACK_NOTE" <<EOF
---
id: ${SLUG}-stack
type: meta
axis: meta
project: ${SLUG}
${CLIENT:+client: ${CLIENT}}
date: ${DATE}
generated_by: ultralearn.sh
---

# ${SLUG} — Stack & Dependências

## Stack: ${STACK}

## Dependências (${DEP_COUNT})

\`\`\`
$(head -50 "$DEPS_FILE" 2>/dev/null || echo "(nenhuma)")
\`\`\`

$([ $DEP_COUNT -gt 50 ] && echo "_Mostrando primeiras 50 de ${DEP_COUNT}._")

## Links

- [[${SLUG}-architecture]]
EOF
echo "   ✓ $STACK_NOTE"

if [ $CHEAP -eq 0 ]; then
  cat > "$HOTPATHS_NOTE" <<EOF
---
id: ${SLUG}-hot-paths
type: pattern
axis: meta
project: ${SLUG}
${CLIENT:+client: ${CLIENT}}
date: ${DATE}
generated_by: ultralearn.sh
---

# ${SLUG} — Hot Paths

## Maiores arquivos (top 20)

\`\`\`
$(find "$PROJECT" -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.py" -o -name "*.go" \) \
   -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/dist/*" \
   -exec wc -l {} \; 2>/dev/null | sort -rn | head -20)
\`\`\`

_Arquivos grandes são candidatos a refactor ou tem alta densidade de funcionalidade._

## Links

- [[${SLUG}-architecture]]
- [[${SLUG}-stack]]
EOF
  echo "   ✓ $HOTPATHS_NOTE"
fi

# ════════════════════════════════════════════════════════════════════
# FASE 4 — INDEX ($0)
# ════════════════════════════════════════════════════════════════════
echo ""
echo "🔗 [4/4] Index & Briefings..."
python3 "$HOME/cortex/scripts/cortex_engine.py" build-index 2>&1 | tail -3 || true
python3 "$HOME/cortex/scripts/cortex_engine.py" build-briefings 2>&1 | tail -3 || true

# ════════════════════════════════════════════════════════════════════
# RELATÓRIO
# ════════════════════════════════════════════════════════════════════
REPORT="$REPORT_DIR/ultralearn-${SLUG}-${DATE}.md"
cat > "$REPORT" <<EOF
# Ultralearn Report — ${SLUG}

> Gerado: ${DATE} | Modo: $([ $DEEP -eq 1 ] && echo "DEEP" || echo "default")$([ $CHEAP -eq 1 ] && echo " CHEAP")

## Estatísticas
- Arquivos: ${TOTAL}
- Stack: ${STACK}
- Dependências: ${DEP_COUNT}
- README: ${README_PRESENT}

## Notas geradas
- \`${ARCH_NOTE}\`
- \`${STACK_NOTE}\`
$([ $CHEAP -eq 0 ] && echo "- \`${HOTPATHS_NOTE}\`")

## Próximos passos
1. Revisar notas geradas
2. Adicionar links \`[[...]]\` cross-project manualmente
3. Marcar pontos de dor em nota \`${SLUG}-pain-points.md\` (manual)
EOF

rm -rf "$TEMP_DIR"
echo ""
echo "✅ Concluído. Relatório: $REPORT"
echo "   Notas em: $NOTES_DIR/${SLUG}-*.md"
