#!/bin/bash
# sf-evolucao.sh — wrapper do Ciclo de Evolução (job semanal na VPS; à mão em qualquer host).
#   sf-evolucao.sh ciclo [--max N] [--sem-replay]
#   sf-evolucao.sh status | aprovar <data> <id> | rejeitar <data> <id> [motivo]
set -uo pipefail
PY="${PYTHON:-python3}"
[[ -x "$HOME/.venv/bin/python3" ]] && PY="$HOME/.venv/bin/python3"
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH:$HOME/.npm-global/bin"
export SF_AUTOMATED=1   # hooks de sessão (loop de heurística, coach) não se aplicam a chamada automatizada
LOG="$HOME/logs/evolucao.log"; mkdir -p "$HOME/logs"
echo "[$(date +%Y-%m-%dT%H:%M:%S)] === sf-evolucao $* ===" >> "$LOG"
if [[ "${1:-}" == "ciclo" ]]; then
  TO="$(command -v timeout || command -v gtimeout || true)"   # macOS não tem timeout
  if ! env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT ${TO:+$TO 90} claude -p --model haiku --output-format text --max-turns 3 "responda apenas: OK" </dev/null 2>/dev/null | grep -q OK; then
    echo "claude CLI sem login neste host ($(hostname), user $(id -un)) — rode 'claude login' aqui. Ciclo abortado." | tee -a "$LOG"; exit 2
  fi
fi
"$PY" "$HOME/framework/runtime/evolucao/pipeline.py" "$@" 2>&1 | tee -a "$LOG"
exit "${PIPESTATUS[0]}"
