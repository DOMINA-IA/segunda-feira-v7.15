#!/bin/bash
# agent-ranking.sh — Ranking canônico de atividade de agentes (filtra smoke tests)
#
# Uso: ./agent-ranking.sh [--days N] [--include-smoke]
# Default: últimos 7 dias, exclui @autonomous-smoke
#
# Origem: 13-Mai-2026 — item C do plano de saúde. Smoke test polui rankings
# brutos do consciousness/memory/episodic. Esta é a view filtrada canônica.

set -uo pipefail

DAYS=7
INCLUDE_SMOKE=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --days) DAYS="$2"; shift 2;;
    --include-smoke) INCLUDE_SMOKE=true; shift;;
    *) shift;;
  esac
done

python3 - "$DAYS" "$INCLUDE_SMOKE" << 'PYEOF'
import json, glob, os, sys
from collections import Counter
from datetime import datetime, timezone, timedelta

days = int(sys.argv[1])
include_smoke = sys.argv[2].lower() == 'true'

# Agentes excluídos por padrão (heartbeat/smoke)
EXCLUDED = set() if include_smoke else {'@autonomous-smoke'}

home = os.path.expanduser('~')
files = sorted(glob.glob(f'{home}/consciousness/memory/episodic/*.jsonl'))

cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
agents = Counter()
results = Counter()
valence_sum = {}
valence_n = {}

for f in files:
    with open(f) as fp:
        for line in fp:
            line = line.strip()
            if not line.startswith('{'): continue
            try: e = json.loads(line)
            except: continue
            if e.get('timestamp','') < cutoff: continue
            ag = e.get('agent','?')
            if ag in EXCLUDED: continue
            agents[ag] += 1
            r = e.get('outcome',{}).get('result','?')
            results[r] += 1
            v = e.get('valence', 0)
            if isinstance(v, dict): v = v.get('score', 0)
            try: v = float(v)
            except: v = 0
            valence_sum[ag] = valence_sum.get(ag, 0) + v
            valence_n[ag] = valence_n.get(ag, 0) + 1

total = sum(agents.values())
print(f"=== Atividade últimos {days} dias (smoke {'incluído' if include_smoke else 'excluído'}) ===")
print(f"Total episódios: {total}")
print(f"Resultados: {dict(results)}")
print()
print(f"{'Agente':<28} {'Eps':>5} {'Val.médio':>10}")
print("─" * 50)
for ag, n in agents.most_common(20):
    vm = valence_sum.get(ag, 0) / max(1, valence_n.get(ag, 1))
    print(f"{ag:<28} {n:>5} {vm:>+10.2f}")
PYEOF
