#!/bin/bash
# agent-boot-context.sh — Imprime contexto fresco para um subagent na ativação.
# Uso: bash ~/broadcast/agent-boot-context.sh <agent-name>
#
# Saída (em ordem de prioridade):
#   1. Briefing CORTEX do agente
#   2. Top heurísticas com confidence >= 0.7
#   3. Mensagens não lidas na mailbox
#   4. Sinais recentes (<24h) onde o agente é destinatário

set -euo pipefail
AGENT="${1:-}"
if [[ -z "$AGENT" ]]; then
  echo "Uso: $0 <agent-name>"
  exit 1
fi
AGENT_CLEAN="${AGENT#@}"

# Briefings vivem em briefings/{meta,ops}/ desde a migração de axis; a raiz
# permanece como fallback legado. Mesma ordem de candidatos que router.py.
BRIEFING=""
for cand in "$HOME/cortex/briefings/${AGENT_CLEAN}.md" \
            "$HOME/cortex/briefings/meta/${AGENT_CLEAN}.md" \
            "$HOME/cortex/briefings/ops/${AGENT_CLEAN}.md"; do
  if [[ -f "$cand" ]]; then BRIEFING="$cand"; break; fi
done
HEURISTICS="$HOME/consciousness/memory/procedural/heuristics.jsonl"
MAILBOX="$HOME/broadcast/mailbox/${AGENT_CLEAN}.json"

echo "=== BOOT CONTEXT @${AGENT_CLEAN} — $(date -u +%Y-%m-%dT%H:%MZ) ==="

if [[ -n "$BRIEFING" ]]; then
  echo ""
  echo "--- BRIEFING CORTEX ---"
  head -60 "$BRIEFING"
else
  # Ausência tem de ser audível: boot silencioso sem briefing foi o bug de 15-Jul.
  echo ""
  echo "--- BRIEFING CORTEX: AUSENTE para @${AGENT_CLEAN} ---"
  echo "    Procurado em briefings/{,meta/,ops/}${AGENT_CLEAN}.md"
  echo "    Regenerar: python3 ~/cortex/scripts/cortex_engine.py build-briefings"
fi

if [[ -f "$HEURISTICS" ]]; then
  echo ""
  # Piso 0.4 = "não refutada". A escala mudou em 15-Jul: confidence agora mede
  # evidência independente (0.5 = não corroborada, <0.5 = tem contra-evidência),
  # não coocorrência de palavras. Ver ~/consciousness/scripts/heuristic_validator.py.
  echo "--- TOP HEURÍSTICAS (não refutadas, mais corroboradas primeiro) ---"
  python3 -c "
import json, sys
hits = []
for line in open('$HEURISTICS'):
    try:
        h = json.loads(line)
    except: continue
    if h.get('agent') == '@${AGENT_CLEAN}' and h.get('confidence', 0) >= 0.4:
        hits.append(h)
# Corroborada por episódio independente vem antes; empate desempata pela mais recente.
hits.sort(key=lambda h: (-h.get('confidence', 0), -h.get('times_validated', 0), h.get('created', '')), reverse=False)
for h in hits[:5]:
    ev = h.get('times_validated', 0)
    tag = f'{ev}x' if h.get('validation_method') in ('declared', 'inferred') else 'nova'
    print(f\"  [{h.get('confidence',0):.2f} {tag}] {h.get('heuristic','?')[:120]}\")
if not hits:
    print('  (sem heurísticas validadas para este agente)')
" 2>/dev/null || echo "  (erro ao ler heurísticas)"
fi

if [[ -f "$MAILBOX" ]]; then
  echo ""
  echo "--- MAILBOX (não lidas) ---"
  python3 -c "
import json
data = json.load(open('$MAILBOX'))
msgs = data if isinstance(data, list) else data.get('messages', [])
unread = [m for m in msgs if isinstance(m, dict) and not m.get('read')]
for m in unread[-5:]:
    print(f\"  [{m.get('priority','normal')}] {m.get('subject','?')[:100]} (de {m.get('from','?')})\")
if not unread:
    print('  (mailbox vazia)')
" 2>/dev/null || echo "  (erro ao ler mailbox)"
fi

echo ""
echo "=== END BOOT CONTEXT ==="
