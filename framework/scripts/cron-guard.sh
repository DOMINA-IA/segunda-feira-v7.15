#!/bin/bash
# =============================================================================
# cron-guard.sh — Executa um job com intervalo mínimo, tentando todo dia.
#
# POR QUE EXISTE (diagnóstico de 05-Set-2026): jobs SEMANAIS neste Mac param
# sozinhos. reflect-weekly (domingo 23:17) 27 dias parado, framework-health
# (segunda 08:00) 26 dias, athena-dormant (segunda 09:00) 19 dias.
#
# A causa não é o cron (daemon vivo) nem script quebrado (todos rodam à mão com
# exit 0). É a JANELA ÚNICA: um job semanal tem 1 chance por semana. Se o Mac
# estiver dormindo naquele minuto, perde a semana inteira. Comparação que fecha
# o caso: athena-daily (5 8 * * 1-5) roda às 08:05 sem falhar, enquanto
# framework-health (0 8 * * 1) não roda há 26 dias — 5 chances contra 1.
#
# Este guard inverte: agenda TODO DIA e só executa se passou o intervalo. Assim
# qualquer dia com o Mac acordado serve.
#
# Uso no crontab:
#   0 11 * * * /bin/bash ~/framework/scripts/cron-guard.sh <id> <dias> <comando...>
#
# Exemplo:
#   0 11 * * * /bin/bash ~/framework/scripts/cron-guard.sh health 7 \
#              /usr/bin/python3 ~/framework/scripts/framework_health_check.py
# =============================================================================
set -uo pipefail

ID="${1:-}"; INTERVALO="${2:-7}"; shift 2 || true
if [[ -z "$ID" || $# -eq 0 ]]; then
  echo "uso: cron-guard.sh <id> <intervalo_dias> <comando...>" >&2
  exit 2
fi

STAMP_DIR="$HOME/logs/.cron-guard"
STAMP="$STAMP_DIR/$ID"
LOG="$HOME/logs/${ID}.log"
mkdir -p "$STAMP_DIR"

if [[ -f "$STAMP" ]]; then
  IDADE=$(( ( $(date +%s) - $(stat -f %m "$STAMP" 2>/dev/null || echo 0) ) / 86400 ))
  [[ "$IDADE" -lt "$INTERVALO" ]] && exit 0   # silencioso: não polui o log
fi

TS=$(date +%Y-%m-%dT%H:%M:%S)
echo "[$TS] === cron-guard '$ID': executando (intervalo ${INTERVALO}d) ===" >> "$LOG"
"$@" >> "$LOG" 2>&1
RC=$?
if [[ $RC -eq 0 ]]; then
  touch "$STAMP"
  echo "[$TS] === '$ID' concluído (rc=0) ===" >> "$LOG"
else
  # Não marca o stamp em caso de falha: tenta de novo amanhã em vez de
  # esperar o intervalo inteiro com o job quebrado.
  echo "[$TS] === '$ID' FALHOU (rc=$RC) — tentará de novo amanhã ===" >> "$LOG"
fi
exit $RC
