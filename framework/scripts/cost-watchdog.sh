#!/bin/bash
# cost-watchdog.sh — Observabilidade de custo do Claude Code CLI.
#
# v2 (28-Mai-2026): antes só media Opus (cego a Sonnet/Haiku). Agora mede TODOS
# os modelos com preços corretos, loga custo total diário SEMPRE (visibilidade),
# e mantém o alerta de DESPERDÍCIO: padrão dev (Bash+Edit+Write) rodando em Opus
# quando Sonnet bastaria. Roda diário 23:35 BRT.
#
# Origem: cost-optimizer (09-Mai). Recalibrado após auditoria 28-Mai que achou
# R$ X.XXX/7d em Opus por ausência de "model":"sonnet" no settings.json.

set -uo pipefail

JSONL_DIR="$HOME/.claude/projects/-HOME-"
SIGNALS="$HOME/broadcast/signals.json"
SF_NOTIFY="$HOME/framework/scripts/sf-notify.sh"
# Threshold de DESPERDÍCIO Opus-dev. Sonnet-dev é ~10x mais barato; não alarma.
THRESHOLD_BRL="${COST_WATCHDOG_THRESHOLD_BRL:-300}"
THRESHOLD_DEV_TOOLS="${COST_WATCHDOG_DEV_THRESHOLD:-50}"
# Threshold de custo TOTAL diário (qualquer modelo) para visibilidade/alerta leve.
THRESHOLD_DAILY_BRL="${COST_WATCHDOG_DAILY_BRL:-500}"

if [[ ! -d "$JSONL_DIR" ]]; then
  echo "[$(date -Iseconds)] JSONL_DIR não encontrado: $JSONL_DIR"
  exit 0
fi

REPORT=$(python3 - "$JSONL_DIR" "$THRESHOLD_BRL" "$THRESHOLD_DEV_TOOLS" << 'PYEOF'
import json, os, glob, sys, time
from collections import Counter, defaultdict

JSONL_DIR = sys.argv[1]
THRESHOLD_BRL = float(sys.argv[2])
THRESHOLD_DEV_TOOLS = int(sys.argv[3])
USD_TO_BRL = 5.75

# Preços Anthropic (USD por 1M tokens): input, output, cache_read, cache_write
PRICING = {
    "opus":   (15.0, 75.0, 1.5,  3.75),
    "sonnet": (3.0,  15.0, 0.30, 3.75),
    "haiku":  (1.0,  5.0,  0.10, 1.25),
}

def model_family(model):
    m = (model or "").lower()
    for fam in PRICING:
        if fam in m:
            return fam
    return None

def cost_usd(fam, u):
    pi, po, pcr, pcw = PRICING[fam]
    return (
        u.get("input_tokens", 0) * pi
        + u.get("output_tokens", 0) * po
        + u.get("cache_read_input_tokens", 0) * pcr
        + u.get("cache_creation_input_tokens", 0) * pcw
    ) / 1_000_000

files = glob.glob(f"{JSONL_DIR}/*.jsonl")
yesterday = time.time() - 86400

total_by_model = defaultdict(float)   # custo BRL hoje por família
alerts = []                           # sessões Opus-dev desperdício

for fpath in files:
    try:
        st = os.stat(fpath)
        file_age = getattr(st, "st_birthtime", st.st_mtime)
        if file_age < yesterday:
            continue
    except OSError:
        continue

    sess_by_model = defaultdict(float)
    tools = Counter()
    try:
        with open(fpath, errors="ignore") as fh:
            for line in fh:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = obj.get("message", {})
                fam = model_family(msg.get("model"))
                if not fam:
                    continue
                c = cost_usd(fam, msg.get("usage", {})) * USD_TO_BRL
                sess_by_model[fam] += c
                for block in (msg.get("content") or []):
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tools[block.get("name", "?")] += 1
    except (IOError, OSError):
        continue

    for fam, c in sess_by_model.items():
        total_by_model[fam] += c

    dev_tools = tools["Bash"] + tools["Edit"] + tools["Write"] + tools["MultiEdit"]
    opus_brl = sess_by_model.get("opus", 0.0)
    # DESPERDÍCIO: padrão dev pesado rodando em Opus
    if opus_brl >= THRESHOLD_BRL and dev_tools >= THRESHOLD_DEV_TOOLS:
        alerts.append({
            "file": os.path.basename(fpath),
            "opus_brl": round(opus_brl, 2),
            "dev_tools": dev_tools,
            "tools_breakdown": dict(tools.most_common(5)),
        })

print(json.dumps({
    "total_by_model": {k: round(v, 2) for k, v in total_by_model.items()},
    "total_brl": round(sum(total_by_model.values()), 2),
    "alerts": alerts,
}))
PYEOF
)

# ─── Visibilidade: custo total diário por modelo (sempre logado) ──────────────
TOTAL_DAILY=$(echo "$REPORT" | python3 -c "import json,sys; print(json.loads(sys.stdin.read())['total_brl'])")
BREAKDOWN=$(echo "$REPORT" | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())['total_by_model']
print(' | '.join(f'{k}: R\$ {v:.2f}' for k, v in sorted(d.items(), key=lambda x: -x[1])) or '(sem uso)')
")
echo "[$(date -Iseconds)] Custo hoje: R\$ $TOTAL_DAILY ($BREAKDOWN)"

COUNT=$(echo "$REPORT" | python3 -c "import json,sys; print(len(json.loads(sys.stdin.read())['alerts']))")

# ─── Alerta leve de custo diário total (mesmo sem desperdício Opus) ───────────
DAILY_HIGH=$(echo "$TOTAL_DAILY $THRESHOLD_DAILY_BRL" | python3 -c "import sys; a,b=map(float,sys.stdin.read().split()); print('1' if a>=b else '0')")
if [[ "$DAILY_HIGH" == "1" && "$COUNT" == "0" ]]; then
  echo "[$(date -Iseconds)] AVISO: custo diário R\$ $TOTAL_DAILY acima do limite R\$ $THRESHOLD_DAILY_BRL (sem padrão Opus-dev — verificar volume)"
  [[ -x "$SF_NOTIFY" ]] && bash "$SF_NOTIFY" "Cost Watchdog" "Custo diário R\$ $TOTAL_DAILY ($BREAKDOWN)" "warn"
fi

if [[ "$COUNT" == "0" ]]; then
  [[ "$DAILY_HIGH" == "0" ]] && echo "[$(date -Iseconds)] Sem desperdício Opus-dev (threshold R\$$THRESHOLD_BRL + ${THRESHOLD_DEV_TOOLS}+ tools dev)"
  exit 0
fi

ALERTS=$(echo "$REPORT" | python3 -c "import json,sys; print(json.dumps(json.loads(sys.stdin.read())['alerts']))")
TOTAL_BRL=$(echo "$ALERTS" | python3 -c "import json,sys; a=json.loads(sys.stdin.read()); print(f'{sum(x[\"opus_brl\"] for x in a):.2f}')")

SUMMARY="$COUNT sessão(ões) Opus com padrão dev — desperdício R\$$TOTAL_BRL (Sonnet bastaria)"
echo "[$(date -Iseconds)] $SUMMARY"
echo "$ALERTS" | python3 -m json.tool

# Emitir sinal
TS=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
SIG_ID="cost_alert_$(date +%s)"
python3 - "$SIGNALS" "$SIG_ID" "$TS" "$SUMMARY" "$ALERTS" << 'PYEOF'
import json, sys, pathlib
sf, sig_id, ts, summary, alerts_json = sys.argv[1:6]
p = pathlib.Path(sf)
data = json.loads(p.read_text()) if p.exists() else []
if not isinstance(data, list):
    data = []
data.append({
    "id": sig_id,
    "type": "cost_alert",
    "agent": "@cost-watchdog",
    "action": summary,
    "confidence": 0.95,
    "risk": "low",
    "timestamp": ts,
    "data": json.loads(alerts_json),
})
p.write_text(json.dumps(data, indent=2, ensure_ascii=False))
print(f"Sinal cost_alert emitido: {sig_id}")
PYEOF

# Notificação macOS
if [[ -x "$SF_NOTIFY" ]]; then
  bash "$SF_NOTIFY" "Cost Watchdog" "$SUMMARY — verifique signals.json" "alert"
fi

# ─── ATUADOR: episódio + heurística (recorrência escala valência) ─────────────
RECORD="$HOME/consciousness/scripts/record-episode.sh"
if [[ -x "$RECORD" ]]; then
  TOP_TOOLS=$(echo "$ALERTS" | python3 -c "
import json, sys
from collections import Counter
a = json.loads(sys.stdin.read())
c = Counter()
for s in a:
    for k, v in s.get('tools_breakdown', {}).items():
        c[k] += v
print(' '.join(f'{k}:{v}' for k, v in c.most_common(3)))
" 2>/dev/null)

  RECURRENCE=$(python3 - "$SIGNALS" << 'PYEOF'
import json, pathlib, sys
from datetime import datetime, timezone, timedelta
sf = pathlib.Path(sys.argv[1])
sigs = json.loads(sf.read_text()) if sf.exists() else []
cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
n = sum(1 for s in sigs if s.get('type')=='cost_alert' and s.get('timestamp','') > cutoff)
print(n)
PYEOF
)

  if [[ "${RECURRENCE:-0}" -ge 3 ]]; then
    VALENCE="-0.7"; INTENSITY="0.9"
    HEURISTIC_ARG=(--heuristic "Quando dev_tools dominantes forem $TOP_TOOLS e custo > R\$300/sessao, rotear para Sonnet 4.6 desde o inicio. Padrao recorrente (${RECURRENCE}x em 7 dias). Reservar Opus para arquitetura/decisao.")
  else
    VALENCE="-0.4"; INTENSITY="0.5"; HEURISTIC_ARG=()
  fi

  bash "$RECORD" \
    --agent "@cost-watchdog" \
    --type "pattern_detected" \
    --summary "$SUMMARY (top tools: $TOP_TOOLS)" \
    --result "partial" \
    --valence "$VALENCE" \
    --intensity "$INTENSITY" \
    --failed "Padrao mecanico rodando em Opus quando Sonnet bastaria" \
    ${HEURISTIC_ARG[@]+"${HEURISTIC_ARG[@]}"} >/dev/null 2>&1 && \
    echo "[$(date -Iseconds)] Episódio registrado (recurrence=${RECURRENCE:-0}, valence=$VALENCE)"
fi
