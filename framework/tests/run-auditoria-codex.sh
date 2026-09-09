#!/bin/bash
# Dispara a auditoria independente do framework pelo Codex (modelo do ~/.codex/config.toml,
# hoje gpt-6-astra) em segundo plano. Uso:  bash ~/framework/tests/run-auditoria-codex.sh
# Log: ~/logs/auditoria-codex-<data>.log  · resultado: ~/cortex/vault/meta/score-framework-*.md
set -u
PROMPT="${1:-$HOME/framework/tests/prompt-auditoria-codex-2026-09-12.md}"
MODEL="${CODEX_MODEL:-gpt-6-astra}"
LOG="$HOME/logs/auditoria-codex-$(date +%Y%m%d).log"
cd "$HOME" || exit 1
echo "[$(date +%H:%M:%S)] início · modelo=$MODEL · prompt=$(basename "$PROMPT")" > "$LOG"
nohup codex exec -m "$MODEL" --dangerously-bypass-approvals-and-sandbox "$(cat "$PROMPT")" >> "$LOG" 2>&1 &
echo "PID $! · acompanhe com: tail -f $LOG"
