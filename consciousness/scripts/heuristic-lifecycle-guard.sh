#!/bin/bash
# =============================================================================
# heuristic-lifecycle-guard.sh — Garante que o ciclo de vida das heurísticas
# rode mesmo que a janela semanal seja perdida.
#
# POR QUE EXISTE: o cron era "50 7 * * 1" (segunda 07:50). Rodou 27-Jul, 03-Ago,
# 10-Ago e parou — 4 segundas seguidas sem execução, provavelmente com o Mac
# dormindo no horário. Ninguém soube; o decay acumulou 4 semanas e derrubou 217
# heurísticas de uma vez quando finalmente rodou em 04-Set.
#
# Cron de janela única em máquina que dorme é frágil. Este guard roda DIÁRIO e
# só executa se passaram >=7 dias — assim qualquer dia com o Mac acordado serve.
#
# Cron: 50 7 * * *   (todo dia 07:50; executa de fato ~1x por semana)
# =============================================================================
set -uo pipefail
# PATH: usa o python3 do sistema (portavel Linux/macOS)
STAMP="$HOME/consciousness/memory/procedural/.lifecycle-last-run"
LOG="$HOME/logs/heuristic-lifecycle.log"
INTERVALO_DIAS=7
TS=$(date +%Y-%m-%dT%H:%M:%SZ)

if [[ -f "$STAMP" ]]; then
  MT=$(python3 -c "import os,sys;print(int(os.path.getmtime(sys.argv[1])))" "$STAMP" 2>/dev/null || echo 0)   # portável: stat -f é BSD e no GNU não falha, imprime outra coisa (07-Set: "File: unbound variable")
  IDADE=$(( ( $(date +%s) - MT ) / 86400 ))
  if [[ "$IDADE" -lt "$INTERVALO_DIAS" ]]; then
    exit 0   # rodou há menos de 7 dias — silencioso, sem poluir log
  fi
else
  IDADE="nunca"
fi

echo "[$TS] === GUARD: última execução há $IDADE dia(s), disparando ciclo ===" >> "$LOG"

python3 "$HOME/consciousness/scripts/heuristic_validator.py" --apply >> "$LOG" 2>&1; RC_V=$?   # evidência primeiro (05-Set: recalibrar depois do decay anulava o decay)
bash "$HOME/consciousness/scripts/heuristic-decay.sh"   >> "$LOG" 2>&1; RC_D=$?
bash "$HOME/consciousness/scripts/heuristic-promote.sh" >> "$LOG" 2>&1; RC_P=$?

# Validador: única coisa que escreve times_validated. Vivia só no consolidate.sh,
# que foi migrado para a VPS em 22-Mai enquanto heuristics.jsonl ficou no Mac —
# o campo não se movia há 3,5 meses e o gate de promoção depende dele.

if [[ $RC_D -ne 0 || $RC_P -ne 0 || $RC_V -ne 0 ]]; then
  echo "[$TS] FALHA no ciclo (decay=$RC_D promote=$RC_P validator=$RC_V)" >> "$LOG"
  "$HOME/framework/scripts/sf-notify.sh" "⚠️ Heurísticas: ciclo falhou" \
    "decay=$RC_D promote=$RC_P validator=$RC_V — ver ~/logs/heuristic-lifecycle.log" "warn" 2>/dev/null || true
  exit 1
fi

touch "$STAMP"
echo "[$TS] === GUARD: ciclo completo ===" >> "$LOG"
exit 0
