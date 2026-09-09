#!/bin/bash
# =============================================================================
# heuristic-decay.sh — Curva de esquecimento da memória procedural
# Parte da Camada 1: Memória Profunda (Consciousness Engine) — Sprint 3 Grupo B
#
# Analogia: como memória humana que desbota sem reforço, heurísticas que
# ficam muito tempo sem ser revalidadas perdem confiança gradualmente. Isso
# evita que uma heurística obsoleta continue sendo injetada com confidence
# inflada só porque ninguém a contradisse recentemente.
#
# Regra:
#   - Heurística com last_validated (ou created, se nunca validada) há mais
#     de 90 dias perde 0.1 de confidence.
#   - Decai no máximo 1x a cada 30 dias — campo "last_decay" evita decaimento
#     duplicado se o cron rodar mais de uma vez no mesmo mês.
#   - Piso de confidence 0.1 (mesmo piso usado em record-episode.sh
#     --heuristic-failed).
#   - Heurística cuja confidence final ficar abaixo de 0.4 ganha
#     "status": "review" — não é deletada, só sinalizada.
#
# Uso: ./heuristic-decay.sh [--dry-run]
# Recomendado: cron semanal (segunda 07:50 BRT, ver crontab)
# =============================================================================

set -euo pipefail

PROCEDURAL_FILE="$HOME/consciousness/memory/procedural/heuristics.jsonl"

DRY_RUN=false

# Parse argumentos
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run) DRY_RUN=true; shift;;
    *) echo "Argumento desconhecido: $1"; exit 1;;
  esac
done

log() {
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $1"
}

if [[ ! -f "$PROCEDURAL_FILE" ]]; then
  log "ERRO: arquivo de heurísticas não encontrado em $PROCEDURAL_FILE"
  exit 1
fi

log "=== CURVA DE ESQUECIMENTO INICIADA ==="
log "Modo: $(if $DRY_RUN; then echo 'DRY-RUN'; else echo 'PRODUÇÃO'; fi)"

NOW_TS=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
TMP_FILE="$(mktemp "${PROCEDURAL_FILE}.tmp.XXXXXX")"

SUMMARY=$(python3 - "$PROCEDURAL_FILE" "$TMP_FILE" "$NOW_TS" "$DRY_RUN" <<'PY'
import json, sys
from datetime import datetime, timezone, timedelta

procedural_path, tmp_path, now_ts, dry_run = sys.argv[1:5]
dry_run = dry_run.lower() == "true"

# now_ts sempre no formato "%Y-%m-%dT%H:%M:%S.000Z" (gerado pelo bash acima)
now = datetime.fromisoformat(now_ts.replace('.000Z', '+00:00'))


def parse_dt(s):
    """Parseia timestamps do vault — tolera o bug conhecido de sufixo
    '+00:00Z' duplicado (offset explícito seguido de 'Z' redundante,
    produzido por trechos que fazem isoformat() + 'Z' em datetime já
    tz-aware)."""
    if not s:
        return None
    s = s.strip()
    if '+' in s and s.endswith('Z'):
        s = s[:-1]
    elif s.endswith('Z'):
        s = s[:-1] + '+00:00'
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


CUTOFF_STALE = now - timedelta(days=90)
CUTOFF_REDECAY = now - timedelta(days=30)
CONF_FLOOR = 0.1
REVIEW_THRESHOLD = 0.4

with open(procedural_path) as f:
    lines = [l.rstrip('\n') for l in f if l.strip()]

records = []
for l in lines:
    try:
        records.append(json.loads(l))
    except Exception:
        records.append(None)  # preserva linha bruta se já vier inválida

decayed = 0
skipped_recent_decay = 0
no_date = 0
newly_review = 0

for r in records:
    if r is None:
        continue

    ref_date = parse_dt(r.get('last_validated') or r.get('created'))
    if ref_date is None:
        no_date += 1
        continue

    if ref_date >= CUTOFF_STALE:
        continue  # ainda "fresca" (revalidada ou criada há < 90 dias)

    last_decay = parse_dt(r.get('last_decay'))
    if last_decay is not None and last_decay >= CUTOFF_REDECAY:
        skipped_recent_decay += 1
        continue  # já decaiu neste ciclo de 30 dias — não decai 2x

    try:
        old_conf = float(r.get('confidence', 0.5))
    except Exception:
        old_conf = 0.5

    new_conf = max(round(old_conf - 0.1, 4), CONF_FLOOR)
    r['confidence'] = new_conf
    r['last_decay'] = now_ts
    decayed += 1

    if new_conf < REVIEW_THRESHOLD:
        if r.get('status') != 'review':
            newly_review += 1
        r['status'] = 'review'

total_review = sum(1 for r in records if r is not None and r.get('status') == 'review')

if not dry_run:
    with open(tmp_path, 'w') as f:
        for r, original_line in zip(records, lines):
            f.write((json.dumps(r, ensure_ascii=False) if r is not None else original_line) + '\n')

print(f"decayed={decayed}")
print(f"newly_review={newly_review}")
print(f"total_review={total_review}")
print(f"skipped_recent_decay={skipped_recent_decay}")
print(f"no_date={no_date}")
print(f"total_records={len(records)}")
PY
)

# Resumo vem como "chave=valor" linha a linha (só inteiros — seguro para eval)
eval "$SUMMARY"

if $DRY_RUN; then
  rm -f "$TMP_FILE"
  log "[DRY-RUN] Nenhuma alteração gravada em $PROCEDURAL_FILE"
else
  mv "$TMP_FILE" "$PROCEDURAL_FILE"
fi

log "--- Resumo ---"
log "Heurísticas avaliadas: ${total_records}"
log "Decaídas nesta execução: ${decayed}"
log "Puladas (já decaíram há <30d): ${skipped_recent_decay}"
log "Sem data válida (não avaliadas): ${no_date}"
log "Novas em review nesta execução: ${newly_review}"
log "Total em review (acumulado): ${total_review}"
log "=== CURVA DE ESQUECIMENTO CONCLUÍDA ==="
