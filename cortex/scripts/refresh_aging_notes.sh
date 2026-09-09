#!/bin/bash
# refresh_aging_notes.sh — Lista notas aging (freshness 0.3-0.7) para revisão.
#
# Não decide automaticamente — humano revisa e marca:
#   (a) refresh — relevante, atualizar last_verified
#   (b) archive — superseded
#   (c) keep — válida mas pouca consulta
#
# Output: ~/cortex/reports/aging-notes-YYYY-MM-DD.md
#
# Origem: F2 do plano de fragilidades (10-Mai-2026).

set -uo pipefail

TODAY=$(date +%Y-%m-%d)
REPORT_DIR="${HOME}/cortex/reports"
REPORT_FILE="${REPORT_DIR}/aging-notes-${TODAY}.md"
mkdir -p "${REPORT_DIR}"

python3 << PYEOF
import json
import re
import math
import subprocess
from pathlib import Path
from datetime import datetime

# FÓRMULA CANÔNICA — alinhada com cortex_engine.py:calculate_freshness()
# Ver: ~/cortex/vault/concepts/cortex-formula-canonica-freshness.md
#   freshness = exp(-decay_rate * weeks_elapsed)
# Antes deste alinhamento, este script usava fórmula linear mensal divergente
# que reportava 0 aging enquanto o engine reportava 30 (incidente 22-Mai-2026).
vault = Path.home() / "cortex" / "vault"
aging = []
today = datetime.now()

IGNORE_PARTS = {"_index_by_axis", "_archive", ".obsidian", ".git", ".trash"}

for f in vault.rglob("*.md"):
    if any(p in IGNORE_PARTS for p in f.parts):
        continue
    if f.is_symlink():
        continue
    try:
        text = f.read_text(encoding="utf-8")
    except Exception:
        continue
    if not text.startswith("---"):
        continue
    end = text.find("---", 3)
    if end == -1: continue
    block = text[3:end]
    fm = {}
    for line in block.split("\n"):
        m = re.match(r"^([\w_-]+):\s*(.*)$", line.strip())
        if m: fm[m.group(1)] = m.group(2).strip("'\"")
    lv = fm.get("last_verified", "") or fm.get("created", "")
    decay = float(fm.get("decay_rate", "0.05") or "0.05")
    if not lv: continue
    try:
        # Aceita "YYYY-MM-DD" e ISO completo
        date_part = lv.split("T")[0]
        lv_date = datetime.strptime(date_part, "%Y-%m-%d")
        days = (today - lv_date).days
        weeks = days / 7.0
        # FÓRMULA CANÔNICA — exponencial em semanas
        fresh = round(max(0.0, min(1.0, math.exp(-decay * weeks))), 3)
    except Exception:
        continue
    if 0.3 <= fresh <= 0.7:
        aging.append({
            "id": fm.get("id", f.stem),
            "title": fm.get("title", "")[:80],
            "type": fm.get("type", ""),
            "freshness": round(fresh, 3),
            "domain": fm.get("domain", ""),
            "last_verified": lv,
            "days_since": days,
            "path": str(f.relative_to(Path.home())),
        })

aging.sort(key=lambda x: x["freshness"])

report = ["# Aging Notes — " + "$TODAY", ""]
report.append(f"> Notas com freshness entre 0.3 e 0.7 — relevantes mas precisam revisão.")
report.append(f"> Total: **{len(aging)}**")
report.append("")
report.append("| Freshness | Tipo | Título | Domínio | Last Verified |")
report.append("|-----------|------|--------|---------|---------------|")
for n in aging[:30]:
    report.append(f"| {n['freshness']} | {n['type']} | {n['title']} | {n['domain']} | {n['last_verified']} |")

if len(aging) > 30:
    report.append("")
    report.append(f"_+{len(aging)-30} notas adicionais._")

report.append("")
report.append("## Ações por nota")
report.append("")
report.append("Para cada nota acima, decidir:")
report.append("- **REFRESH** — relevante, atualizar \`last_verified\` no frontmatter para hoje")
report.append("- **ARCHIVE** — superseded ou obsoleta, mover para \`~/cortex/vault/_archived/\`")
report.append("- **KEEP** — válida mas pouca consulta, OK manter aging")
report.append("")
report.append("## Como aplicar REFRESH em lote")
report.append("\`\`\`bash")
report.append("# Atualiza last_verified de todas notas com type=playbook freshness aging")
report.append("# (exemplo — adapte critério)")
report.append("python3 ~/cortex/scripts/refresh.sh <note_id>")
report.append("\`\`\`")
report.append("")
report.append("## Como rodar de novo")
report.append("\`\`\`bash")
report.append("bash ~/cortex/scripts/refresh_aging_notes.sh")
report.append("\`\`\`")

Path("$REPORT_FILE").write_text("\n".join(report))
print(f"Aging notes: {len(aging)} encontradas")
print(f"Relatório: $REPORT_FILE")
PYEOF
