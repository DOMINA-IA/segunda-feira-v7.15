#!/usr/bin/env bash
# refactor-suggest.sh — Diff-aware refactor suggestions
# Origem: ruflo worker `refactor` + Agent Booster 3-tier routing.
# Implementação inicial: heurísticas locais ($0). Tier 0 puro.
#
# Uso:
#   refactor-suggest.sh                              # diff atual
#   refactor-suggest.sh --base main                  # vs main
#   refactor-suggest.sh --files "src/auth/*"         # restrito
#   refactor-suggest.sh --format markdown            # output formatado

set -uo pipefail

BASE=""
FILES=""
FORMAT="text"

while [ $# -gt 0 ]; do
  case "$1" in
    --base) BASE="$2"; shift 2 ;;
    --base=*) BASE="${1#--base=}"; shift ;;
    --files) FILES="$2"; shift 2 ;;
    --files=*) FILES="${1#--files=}"; shift ;;
    --format) FORMAT="$2"; shift 2 ;;
    --format=*) FORMAT="${1#--format=}"; shift ;;
    *) shift ;;
  esac
done

# Em diretório sem git, abortar com aviso
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "⚠️  Não é um repo git. refactor-suggest precisa de git diff."
  exit 1
fi

# Determinar diff
if [ -n "$BASE" ]; then
  DIFF_ARGS="$BASE...HEAD"
else
  DIFF_ARGS="HEAD"
fi

# Lista de arquivos no diff
if [ -n "$FILES" ]; then
  CHANGED=$(git diff --name-only "$DIFF_ARGS" -- $FILES 2>/dev/null)
else
  CHANGED=$(git diff --name-only "$DIFF_ARGS" 2>/dev/null)
fi

if [ -z "$CHANGED" ]; then
  echo "Sem arquivos no diff. Nada a sugerir."
  exit 0
fi

[ "$FORMAT" = "markdown" ] && echo "## Refactor Suggestions — $(date +%Y-%m-%d\ %H:%M)" && echo ""

HIGH_COUNT=0
MED_COUNT=0
LOW_COUNT=0

for file in $CHANGED; do
  [ ! -f "$file" ] && continue

  # Smell 1: Long methods (function/def com >40 linhas)
  long=$(awk '
    /^(function |def )/ { name=$0; start=NR }
    /^}/ { if (start && (NR - start) > 40) { print FILENAME ":" start " — função >40 linhas: " substr(name,1,60) }; start=0 }
  ' "$file" 2>/dev/null)
  if [ -n "$long" ]; then
    echo "🟡 [LONG] $long"
    MED_COUNT=$((MED_COUNT + 1))
  fi

  # Smell 2: Magic numbers (números literais >9 que aparecem 2+ vezes)
  magic=$(grep -oE '\b[1-9][0-9]{2,}\b' "$file" 2>/dev/null | sort | uniq -c | awk '$1 >= 3 {print $2}' | head -3)
  if [ -n "$magic" ]; then
    for m in $magic; do
      echo "🟢 [MAGIC] $file: número $m aparece 3+ vezes — extrair constante"
      LOW_COUNT=$((LOW_COUNT + 1))
    done
  fi

  # Smell 3: Console.log / print de debug
  debug=$(grep -nE '\b(console\.log|print|console\.error|debugger)\b' "$file" 2>/dev/null | head -3)
  if [ -n "$debug" ]; then
    while IFS= read -r line; do
      echo "🟢 [DEBUG] $file:${line%%:*} — debug statement (remover antes de commit)"
      LOW_COUNT=$((LOW_COUNT + 1))
    done <<< "$debug"
  fi

  # Smell 4: TODO/FIXME novos
  todos=$(git diff "$DIFF_ARGS" -- "$file" 2>/dev/null | grep -E '^\+.*\b(TODO|FIXME|XXX|HACK)\b' | head -3)
  if [ -n "$todos" ]; then
    n=$(echo "$todos" | wc -l | tr -d ' ')
    echo "🟡 [TODO] $file: $n novo(s) TODO/FIXME no diff — criar issue ou resolver"
    MED_COUNT=$((MED_COUNT + 1))
  fi

  # Smell 5: var em JS/TS (preferir const/let)
  if [[ "$file" == *.js || "$file" == *.ts || "$file" == *.jsx || "$file" == *.tsx ]]; then
    vars=$(git diff "$DIFF_ARGS" -- "$file" 2>/dev/null | grep -cE '^\+.*\bvar ' || true)
    if [ "${vars:-0}" -gt 0 ]; then
      echo "🔴 [VAR] $file: $vars uso(s) de \`var\` (Agent Booster Tier 0: var→const, \$0)"
      HIGH_COUNT=$((HIGH_COUNT + 1))
    fi
  fi

  # Smell 6: any em TypeScript
  if [[ "$file" == *.ts || "$file" == *.tsx ]]; then
    anys=$(git diff "$DIFF_ARGS" -- "$file" 2>/dev/null | grep -cE '^\+.*:\s*any\b' || true)
    if [ "${anys:-0}" -gt 0 ]; then
      echo "🟡 [ANY] $file: $anys uso(s) de \`any\` — tipar corretamente"
      MED_COUNT=$((MED_COUNT + 1))
    fi
  fi
done

echo ""
echo "─────────────────────────────────"
echo "Total: 🔴 $HIGH_COUNT high │ 🟡 $MED_COUNT med │ 🟢 $LOW_COUNT low"
echo ""
if [ "$HIGH_COUNT" -gt 0 ]; then
  echo "💡 Para refactors mecânicos high-confidence (var→const, etc):"
  echo "   node ~/.claude/skills/scripts/agent-booster.mjs --intent var-to-const --file <path>"
fi
