#!/bin/bash
# =============================================================================
# transcript-retention.sh — Política de retenção dos transcripts do Claude Code.
#
# POR QUE EXISTE: auditoria de 05-Set-2026 encontrou 93 credenciais em texto
# plano em 14 de 465 transcripts, e nenhuma expiração automática — o histórico
# só não era maior porque começou há 57 dias. Sem retenção, todo segredo que
# passar por uma conversa fica em disco para sempre.
#
# NÃO substitui a redação (redact-transcripts.py): retenção limita o acúmulo
# futuro, redação trata o que já existe.
#
# Cron: 30 4 * * 0   (domingo 04:30)
#
# Config por env var:
#   RETENCAO_DIAS   (default 90)  — idade máxima
#   RETENCAO_APPLY  (default 0)   — 1 executa, 0 só relata
# =============================================================================
set -uo pipefail

RAIZ="$HOME/.claude/projects"
DIAS="${RETENCAO_DIAS:-90}"
APPLY="${RETENCAO_APPLY:-0}"
LOG="$HOME/logs/transcript-retention.log"
MIN_INATIVO_MIN=60          # nunca tocar em sessão com escrita recente
TS=$(date +%Y-%m-%dT%H:%M:%SZ)

mkdir -p "$HOME/logs"

if [[ ! -d "$RAIZ" ]]; then
  echo "[$TS] ERRO: $RAIZ não existe" >> "$LOG"
  exit 3
fi

# Candidatos: mais velhos que $DIAS E sem escrita na última hora.
# O segundo filtro evita apagar sessão longa que ainda está aberta.
CANDIDATOS=$(find "$RAIZ" -type f \( -name "*.jsonl" -o -name "*.txt" \) \
             -mtime +"$DIAS" -mmin +"$MIN_INATIVO_MIN" 2>/dev/null)

N=$(echo "$CANDIDATOS" | grep -c . || true)
TOTAL=$(find "$RAIZ" -type f \( -name "*.jsonl" -o -name "*.txt" \) 2>/dev/null | wc -l | tr -d ' ')

if [[ "$N" -eq 0 ]]; then
  echo "[$TS] OK — nenhum transcript acima de ${DIAS}d (total: $TOTAL)" >> "$LOG"
  exit 0
fi

BYTES=$(echo "$CANDIDATOS" | xargs -I{} stat -f %z "{}" 2>/dev/null | awk '{s+=$1} END {print s+0}')
MB=$(( BYTES / 1048576 ))

if [[ "$APPLY" != "1" ]]; then
  echo "[$TS] RELATO — $N de $TOTAL transcripts acima de ${DIAS}d (~${MB}MB). RETENCAO_APPLY=1 para remover." >> "$LOG"
  echo "$CANDIDATOS" | sed 's|.*/|  · |' >> "$LOG"
  "$HOME/framework/scripts/sf-notify.sh" "🗂 Transcripts antigos" \
    "$N transcripts acima de ${DIAS}d (~${MB}MB). Rode com RETENCAO_APPLY=1 para limpar." "info" 2>/dev/null || true
  exit 0
fi

echo "[$TS] APLICANDO — removendo $N transcript(s) acima de ${DIAS}d (~${MB}MB)" >> "$LOG"
echo "$CANDIDATOS" | while read -r f; do
  [[ -n "$f" ]] && rm -f "$f" && echo "  removido: $(basename "$f")" >> "$LOG"
done
echo "[$TS] CONCLUÍDO — liberados ~${MB}MB" >> "$LOG"
exit 0
