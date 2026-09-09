#!/usr/bin/env bash
# benchmark.sh — Performance benchmark do framework Segunda-feira
# Origem: ruflo worker `benchmark` adaptado.
#
# Uso:
#   bash ~/.claude/skills/scripts/benchmark.sh             # quick
#   bash ~/.claude/skills/scripts/benchmark.sh --full      # inclui crons
#   bash ~/.claude/skills/scripts/benchmark.sh --compare last-week

set -uo pipefail

MODE="quick"
COMPARE=""
for arg in "$@"; do
  case "$arg" in
    --full) MODE="full" ;;
    --compare) COMPARE="last" ;;
    --compare=*) COMPARE="${arg#--compare=}" ;;
  esac
done

REPORTS_DIR="$HOME/cortex/reports"
mkdir -p "$REPORTS_DIR"
NOW=$(date +%Y-%m-%d)
WEEK=$(date +%Y-W%V)
OUT="$REPORTS_DIR/benchmark-$NOW.md"

bench_query() {
  local q="$1"
  local start=$(python3 -c "import time; print(time.time())")
  python3 "$HOME/cortex/scripts/cortex_engine.py" query "$q" > /dev/null 2>&1
  local end=$(python3 -c "import time; print(time.time())")
  python3 -c "print(round(($end - $start) * 1000, 1))"
}

bench_briefings() {
  local start=$(python3 -c "import time; print(time.time())")
  python3 "$HOME/cortex/scripts/cortex_engine.py" build-briefings > /dev/null 2>&1
  local end=$(python3 -c "import time; print(time.time())")
  python3 -c "print(round($end - $start, 2))"
}

bench_hook() {
  local hook="$1"
  local input='{"tool_name":"Write","tool_input":{"file_path":"/tmp/x.md","content":"test"}}'
  local start=$(python3 -c "import time; print(time.time())")
  echo "$input" | python3 "$hook" > /dev/null 2>&1
  local end=$(python3 -c "import time; print(time.time())")
  python3 -c "print(round(($end - $start) * 1000, 1))"
}

echo "📊 Benchmark Framework — $NOW" | tee "$OUT"
echo "" | tee -a "$OUT"
echo "## CORTEX Query Latency (5 runs avg)" | tee -a "$OUT"
echo "" | tee -a "$OUT"
echo "| Query | Latency (ms) |" | tee -a "$OUT"
echo "|-------|--------------|" | tee -a "$OUT"
for q in "agent" "campanha" "story" "feedback" "deploy"; do
  total=0
  for _ in {1..5}; do
    t=$(bench_query "$q" || echo "0")
    total=$(python3 -c "print($total + $t)")
  done
  avg=$(python3 -c "print(round($total / 5, 1))")
  printf "| %s | %s |\n" "$q" "$avg" | tee -a "$OUT"
done
echo "" | tee -a "$OUT"

echo "## CORTEX Sizes" | tee -a "$OUT"
echo "" | tee -a "$OUT"
echo "- Notas (.md): $(find $HOME/cortex/vault -name '*.md' -not -path '*/_index_by_axis/*' 2>/dev/null | wc -l | tr -d ' ')" | tee -a "$OUT"
echo "- Vault size:  $(du -sh $HOME/cortex/vault 2>/dev/null | awk '{print $1}')" | tee -a "$OUT"
echo "- Briefings:   $(find $HOME/cortex/briefings -name '*.md' 2>/dev/null | wc -l | tr -d ' ')" | tee -a "$OUT"
echo "- Heurísticas: $(wc -l < $HOME/consciousness/memory/procedural/heuristics.jsonl 2>/dev/null | tr -d ' ')" | tee -a "$OUT"
echo "- Mailboxes:   $(ls $HOME/broadcast/mailbox/*.json 2>/dev/null | wc -l | tr -d ' ')" | tee -a "$OUT"
echo "" | tee -a "$OUT"

echo "## Hook Latency" | tee -a "$OUT"
echo "" | tee -a "$OUT"
echo "| Hook | Latency (ms) |" | tee -a "$OUT"
echo "|------|--------------|" | tee -a "$OUT"
for hook_name in check-acentos.py telegram-guard.py preflight-stop.py; do
  hook_path="$HOME/.claude/hooks/$hook_name"
  if [ -f "$hook_path" ]; then
    t=$(bench_hook "$hook_path" || echo "n/a")
    printf "| %s | %s |\n" "$hook_name" "$t" | tee -a "$OUT"
  fi
done
echo "" | tee -a "$OUT"

if [ "$MODE" = "full" ]; then
  echo "## Build-Briefings Time" | tee -a "$OUT"
  echo "" | tee -a "$OUT"
  t=$(bench_briefings || echo "0")
  echo "- build-briefings: ${t}s" | tee -a "$OUT"
  echo "" | tee -a "$OUT"
fi

echo "## Comparação" | tee -a "$OUT"
echo "" | tee -a "$OUT"
LAST=$(ls -1t $REPORTS_DIR/benchmark-*.md 2>/dev/null | grep -v "$NOW" | head -1)
if [ -n "$LAST" ]; then
  echo "Última run: $(basename $LAST)" | tee -a "$OUT"
  echo "Compare manualmente: diff $LAST $OUT" | tee -a "$OUT"
else
  echo "Sem comparação anterior — este é o primeiro benchmark." | tee -a "$OUT"
fi

echo "" | tee -a "$OUT"
echo "✅ Relatório: $OUT" >&2
