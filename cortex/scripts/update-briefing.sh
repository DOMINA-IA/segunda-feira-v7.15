#!/bin/bash
# =============================================================================
# CORTEX update-briefing.sh — Memory Blocks Auto-Editáveis (Absorção #4)
#
# Permite que agentes adicionem aprendizado novo no PRÓPRIO briefing,
# de forma controlada com guardrails calibrados conservadoramente.
#
# Uso:
#   update-briefing.sh --agent NOME --text "aprendizado" \
#                      --confidence 0.X --reason "razão"
#
# Guardrails:
#   - Confidence >= 0.85 (rejeita abaixo)
#   - Append-only (proibido replace/delete)
#   - Máximo 3 linhas por chamada
#   - Rate limit: 3 updates por sessão (reseta noturno)
#   - Versionamento em ~/cortex/briefings/.history/
#   - Seção ## Auto-Updates separada do conteúdo curated
# =============================================================================

set -euo pipefail

AGENT=""
TEXT=""
CONFIDENCE=""
REASON=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --agent) AGENT="$2"; shift 2;;
    --text) TEXT="$2"; shift 2;;
    --confidence) CONFIDENCE="$2"; shift 2;;
    --reason) REASON="$2"; shift 2;;
    *) echo "Argumento desconhecido: $1"; exit 1;;
  esac
done

if [[ -z "$AGENT" || -z "$TEXT" || -z "$CONFIDENCE" || -z "$REASON" ]]; then
  echo "Uso: update-briefing.sh --agent NOME --text 'aprendizado' \\"
  echo "                        --confidence 0.X --reason 'razão'"
  echo ""
  echo "Permite agente adicionar aprendizado no próprio briefing."
  echo "Guardrails: confidence >= 0.85, máx 3 linhas, máx 3 updates/sessão."
  exit 1
fi

# Limpar @ se presente
AGENT_CLEAN="${AGENT#@}"

# Constantes (calibração inicial conservadora — ajustar após 30 dias)
MIN_CONFIDENCE=0.85
MAX_LINES=3
MAX_UPDATES_PER_SESSION=3

# Validar confidence numérico
if ! python3 -c "x=float('$CONFIDENCE'); assert 0<=x<=1" 2>/dev/null; then
  echo "❌ Confidence inválido: $CONFIDENCE (deve ser 0.0-1.0)"
  exit 1
fi

# Guardrail 1: Confidence >= MIN_CONFIDENCE
if ! python3 -c "exit(0 if float('$CONFIDENCE') >= $MIN_CONFIDENCE else 1)"; then
  echo "❌ Confidence ($CONFIDENCE) < mínimo ($MIN_CONFIDENCE) — update rejeitado."
  exit 1
fi

# Guardrail 2: Limite de linhas
LINE_COUNT=$(printf '%s' "$TEXT" | awk 'END{print NR}')
if [[ $LINE_COUNT -gt $MAX_LINES ]]; then
  echo "❌ Texto tem $LINE_COUNT linhas (máximo $MAX_LINES) — update rejeitado."
  exit 1
fi

# Caminhos
BRIEFING_FILE="$HOME/cortex/briefings/${AGENT_CLEAN}.md"
HISTORY_DIR="$HOME/cortex/briefings/.history"
SESSION_LOG_DIR="$HOME/cortex/briefings/.session-log"
SESSION_LOG="$SESSION_LOG_DIR/${AGENT_CLEAN}.count"

mkdir -p "$HISTORY_DIR" "$SESSION_LOG_DIR"

# Validar que briefing existe
if [[ ! -f "$BRIEFING_FILE" ]]; then
  echo "❌ Briefing não encontrado: $BRIEFING_FILE"
  echo "   Rode primeiro: python3 ~/cortex/scripts/cortex_engine.py build-briefings"
  exit 1
fi

# Guardrail 3: Rate limit por sessão
SESSION_COUNT=$(cat "$SESSION_LOG" 2>/dev/null || echo 0)
[[ "$SESSION_COUNT" =~ ^[0-9]+$ ]] || SESSION_COUNT=0
if [[ $SESSION_COUNT -ge $MAX_UPDATES_PER_SESSION ]]; then
  echo "❌ Rate limit atingido (${SESSION_COUNT}/${MAX_UPDATES_PER_SESSION} updates/sessão @${AGENT_CLEAN})"
  echo "   Reseta noturno via cron. Update rejeitado."
  exit 1
fi

# Backup pré-update (versionamento)
TIMESTAMP_FILE=$(date -u +%Y%m%d_%H%M%S)
HISTORY_FILE="$HISTORY_DIR/${AGENT_CLEAN}-${TIMESTAMP_FILE}.md"
cp "$BRIEFING_FILE" "$HISTORY_FILE"

# Garantir seção Auto-Updates
if ! grep -q "^## Auto-Updates" "$BRIEFING_FILE"; then
  {
    echo ""
    echo "## Auto-Updates"
    echo ""
    echo "> Seção preservada por build-briefings. Aprendizados auto-registrados pelos agentes."
    echo ""
  } >> "$BRIEFING_FILE"
fi

# Append do novo conhecimento
TIMESTAMP_HUMAN=$(date '+%Y-%m-%d %H:%M')
{
  echo ""
  echo "### ${TIMESTAMP_HUMAN} — confidence ${CONFIDENCE}"
  echo "**Razão:** ${REASON}"
  echo ""
  echo "${TEXT}"
  echo ""
} >> "$BRIEFING_FILE"

# Incrementar session counter
SESSION_COUNT=$((SESSION_COUNT + 1))
echo "$SESSION_COUNT" > "$SESSION_LOG"

echo "✅ Briefing atualizado: $BRIEFING_FILE"
echo "   Backup: $HISTORY_FILE"
echo "   Session updates: ${SESSION_COUNT}/${MAX_UPDATES_PER_SESSION}"
echo "   Confidence: ${CONFIDENCE} | Linhas: ${LINE_COUNT}/${MAX_LINES}"
