#!/bin/bash
# =============================================================================
# feedback-to-consciousness.sh — Converte dados do Feedback Loop em episódios
#
# Lê ~/feedback-loop/results.json, identifica entradas ainda não processadas,
# e gera episódios + heurísticas automaticamente no Consciousness Engine.
#
# Usa um tracker file para evitar reprocessamento.
#
# Uso: ./feedback-to-consciousness.sh [--dry-run]
# Recomendado: rodar junto com consolidate.sh no cron noturno
# =============================================================================

set -euo pipefail

FEEDBACK_FILE="$HOME/feedback-loop/results.json"
TRACKER_FILE="$HOME/consciousness/memory/.feedback-tracker.json"
RECORD_SCRIPT="$HOME/consciousness/scripts/record-episode.sh"

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

if [[ ! -f "$FEEDBACK_FILE" ]]; then
  echo "Feedback loop não encontrado: $FEEDBACK_FILE"
  exit 0
fi

# Garantir tracker existe
if [[ ! -f "$TRACKER_FILE" ]]; then
  echo '{"processed_ids":[]}' > "$TRACKER_FILE"
fi

# Processar campanhas → episódios
python3 << 'PYEOF'
import json
import subprocess
import sys
import os

feedback_path = os.path.expanduser("~/feedback-loop/results.json")
tracker_path = os.path.expanduser("~/consciousness/memory/.feedback-tracker.json")
record_script = os.path.expanduser("~/consciousness/scripts/record-episode.sh")
dry_run = "--dry-run" in sys.argv

with open(feedback_path) as f:
    data = json.load(f)
with open(tracker_path) as f:
    tracker = json.load(f)

processed = set(tracker.get("processed_ids", []))
new_episodes = 0
new_heuristics = 0

# --- CAMPANHAS ---
campaigns = data.get("campaigns", {}).get("entries", [])
for c in campaigns:
    cid = c.get("id", "")
    if cid in processed:
        continue

    name = c.get("name", "")
    cpl = c.get("cpl") or 0
    leads = c.get("leads") or 0
    spend = c.get("spend") or 0
    angle = c.get("creative_angle", "")
    status = c.get("status", "")
    notes = c.get("notes", "")

    # Determinar valência pelo CPL
    if cpl > 0 and cpl < 5:
        valence = 0.7
        result = "success"
    elif cpl > 0 and cpl < 10:
        valence = 0.3
        result = "partial"
    elif cpl >= 10:
        valence = -0.5
        result = "failure"
    else:
        valence = 0.0
        result = "partial"

    # Intensidade pelo volume
    intensity = min(0.9, 0.3 + (leads / 100))

    summary = f"Campanha '{name}': CPL R${cpl:.2f}, {leads} leads, R${spend:.0f} investidos"
    worked = f"Ângulo '{angle}'" if angle and valence > 0 else ""
    failed = f"CPL alto: R${cpl:.2f}" if valence < 0 else ""

    # Gerar heurística se dados suficientes
    heuristic = ""
    if angle and valence > 0.3:
        heuristic = f"Quando usar ângulo '{angle}', esperar CPL ~R${cpl:.2f} com {leads} leads para R${spend:.0f} de investimento"
    elif valence < -0.3:
        heuristic = f"Quando CPL ultrapassa R${cpl:.2f} em campanha similar a '{name}', considerar pausar e testar novo ângulo"

    if not dry_run:
        args = [
            "bash", record_script,
            "--agent", "@traffic",
            "--type", "pattern_detected",
            "--summary", summary[:200],
            "--result", result,
            "--valence", str(valence),
            "--intensity", str(intensity),
        ]
        if worked:
            args.extend(["--worked", worked[:150]])
        if failed:
            args.extend(["--failed", failed[:150]])
        if heuristic:
            args.extend(["--heuristic", heuristic[:200]])

        try:
            subprocess.run(args, capture_output=True, timeout=5)
            new_episodes += 1
            if heuristic:
                new_heuristics += 1
        except Exception as e:
            print(f"  Erro ao registrar episódio: {e}", file=sys.stderr)
    else:
        new_episodes += 1
        if heuristic:
            new_heuristics += 1
        print(f"  [DRY-RUN] {summary}")

    processed.add(cid)

# --- OFERTAS ---
offers = data.get("offers", {}).get("entries", [])
for o in offers:
    oid = o.get("id", o.get("name", ""))
    if oid in processed:
        continue

    name = o.get("name", "desconhecida")
    price = o.get("price", 0)
    conversions = o.get("conversions", 0)
    notes = o.get("notes", "")

    valence = 0.5 if conversions > 0 else 0.0
    summary = f"Oferta '{name}': R${price}, {conversions} conversões"

    if not dry_run:
        subprocess.run([
            "bash", record_script,
            "--agent", "@offer-engineer",
            "--type", "pattern_detected",
            "--summary", summary[:200],
            "--result", "success" if conversions > 0 else "partial",
            "--valence", str(valence),
            "--intensity", "0.5",
        ], capture_output=True, timeout=5)
        new_episodes += 1
    else:
        new_episodes += 1
        print(f"  [DRY-RUN] {summary}")

    processed.add(oid)

# Salvar tracker
if not dry_run:
    tracker["processed_ids"] = list(processed)
    with open(tracker_path, "w") as f:
        json.dump(tracker, f, indent=2)

print(f"Episódios criados: {new_episodes}")
print(f"Heurísticas geradas: {new_heuristics}")
print(f"Total processado: {len(processed)}")
PYEOF
