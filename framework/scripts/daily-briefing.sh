#!/bin/bash
# =============================================================================
# daily-briefing.sh — Resumo do estado do framework Segunda-feira ao abrir terminal.
#
# Mostra 1x por dia (cache em ~/.cache/sf-briefing-DATA.txt).
# Latência alvo: < 500ms. Não atrasa abertura do terminal.
# =============================================================================

CACHE_DIR="$HOME/.cache"
mkdir -p "$CACHE_DIR"
TODAY=$(date +%Y-%m-%d)
CACHE_FILE="$CACHE_DIR/sf-briefing-$TODAY.txt"
PYTHON_FW="/usr/local/bin/python3"

# Versão lida do CLAUDE.md — linha do footer "Constituição vX.Y"
SF_VERSION=$(grep -m1 'Constituição v[0-9]' "$HOME/.claude/CLAUDE.md" 2>/dev/null | grep -oE 'v[0-9]+\.[0-9]+' | head -1)
SF_VERSION="${SF_VERSION:-v?.?}"

# Throttle: já mostrado hoje? mostra cache.
if [[ -f "$CACHE_FILE" ]]; then
  cat "$CACHE_FILE"
  exit 0
fi

# Coletar dados (todos com fallback silencioso pra <500ms)
SIGNALS_ACTIVE=$(python3 -c "
import json
try:
    d = json.load(open('$HOME/broadcast/signals.json'))
    SYSTEM_TYPES = {'BRAIN_ALERT', 'CONSOLIDATION_COMPLETE'}
    active = []
    for s in (d if isinstance(d, list) else d.get('signals', [])):
        if s.get('type') in SYSTEM_TYPES:
            continue
        consumed_by = s.get('consumed_by')
        consumed = s.get('consumed', False)
        if consumed or (isinstance(consumed_by, list) and consumed_by) or (isinstance(consumed_by, str) and consumed_by):
            continue
        active.append(s)
    print(len(active))
except: print(0)
" 2>/dev/null || echo "?")

DECISIONS_OVERDUE=$(python3 -c "
import json, os, sys
sys.path.insert(0, os.path.expanduser('~/cortex/scripts'))
try:
    from decision_engine import get_overdue_decisions
    print(len(get_overdue_decisions()))
except: print(0)
" 2>/dev/null || echo "0")

# Sugestão do dia: agente menos usado dos top-30
SUGGESTION=$($PYTHON_FW -c "
import os
from pathlib import Path
agents = sorted([f.stem for f in Path.home().joinpath('.claude/agents').glob('*.md') if not f.stem.startswith('_')])
ep_dir = Path.home() / 'consciousness' / 'memory' / 'episodic'
unused = [a for a in agents if not (ep_dir / f'{a}.jsonl').exists()]
if unused:
    import random
    random.seed($(date +%s))
    print('@' + random.choice(unused))
else:
    print('@analyst')
" 2>/dev/null || echo "@analyst")

# Health do CORTEX
HEALTH=$($PYTHON_FW -c "
import json, os
try:
    d = json.load(open(os.path.expanduser('~/cortex/index/health.json')))
    print(f\"{d.get('health_score', 0):.0f}%\")
except: print('?%')
" 2>/dev/null || echo "?%")

# Última sync VPS
LAST_SYNC=$(ssh -o ConnectTimeout=2 -o BatchMode=yes root@${VPS_HOST} 'cat /opt/segunda-feira-mirror/_last-sync.txt 2>/dev/null' 2>/dev/null || echo "—")

# Próximo cron
DOW=$(date +%u)
case $DOW in
  5) NEXT_CRON="hoje 09:07 — INEMA scout (sexta)" ;;
  7) NEXT_CRON="hoje 23:17 — Reflect weekly (domingo)" ;;
  *) NEXT_CRON="amanhã 03:00 — CORTEX sync para VPS" ;;
esac

# Montar briefing
DAY_PT=$(date +%A | sed 's/Monday/segunda/;s/Tuesday/terça/;s/Wednesday/quarta/;s/Thursday/quinta/;s/Friday/sexta/;s/Saturday/sábado/;s/Sunday/domingo/')

# Detectar se há Auto Orchestrator briefing de hoje
MORNING_FILE="$HOME/.cache/sf-morning-$TODAY.md"
MORNING_SECTION=""
if [[ -f "$MORNING_FILE" ]]; then
  # Mostrar só as 3 primeiras frases de cada agente (resumo do resumo)
  MORNING_SECTION=$(awk '/^### @/{agent=$0; print "\n   " agent} /^[A-ZÀ-Ý].*\./ && !seen[agent]++ {gsub(/^/, "      "); print substr($0, 1, 220)}' "$MORNING_FILE" 2>/dev/null | head -25)
fi

cat > "$CACHE_FILE" <<EOF

╔══════════════════════════════════════════════════════════╗
║  ☀️  SEGUNDA-FEIRA $SF_VERSION — Daily Briefing               ║
╚══════════════════════════════════════════════════════════╝

   Hoje é $DAY_PT, $(date +%d/%m/%Y).

   📡 Sinais ativos:        $SIGNALS_ACTIVE
   ⚠️  Decisões vencidas:    $DECISIONS_OVERDUE
   🧠 CORTEX health:         $HEALTH
   💾 Última sync VPS:       $LAST_SYNC
   ⏰ Próximo cron:          $NEXT_CRON

EOF

if [[ -n "$MORNING_SECTION" ]]; then
  cat >> "$CACHE_FILE" <<EOF
   ─────────────────────────────────────────────────────────
   🤖 AUTO ORCHESTRATOR — agentes consultaram seu contexto
   ─────────────────────────────────────────────────────────
$MORNING_SECTION

   📖 Briefing completo: cat ~/.cache/sf-morning-latest.md
   ─────────────────────────────────────────────────────────

EOF
else
  cat >> "$CACHE_FILE" <<EOF
   ─────────────────────────────────────────────────────────
   💡 Sugestão de hoje:  você nunca chamou $SUGGESTION
      Experimente: "$SUGGESTION, sua opinião sobre meu próximo passo?"
   ─────────────────────────────────────────────────────────

EOF
fi

cat >> "$CACHE_FILE" <<EOF
   📚 'sf' abre a Segunda-feira | 'sf-briefing' atualiza este resumo
   ─────────────────────────────────────────────────────────

EOF

cat "$CACHE_FILE"
