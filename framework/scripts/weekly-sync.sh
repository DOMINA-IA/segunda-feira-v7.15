#!/bin/bash
# ==============================================================================
# Weekly Sync — Segunda-feira Framework
# Consolida estado semanal de todos os agentes e gera scorecard executivo
# Idempotente: pode rodar multiplas vezes no mesmo dia (sobrescreve mesmo arquivo)
# ==============================================================================

set -euo pipefail

# --- Caminhos absolutos ---
HOME_DIR="$HOME"
RESULTS_JSON="$HOME_DIR/feedback-loop/results.json"
SIGNALS_JSON="$HOME_DIR/broadcast/signals.json"
OPPORTUNITIES_MD="$HOME_DIR/framework/observations/opportunities.md"
DECISIONS_LOG="$HOME_DIR/docs/decisions-log.md"
BUSINESS_STATE="$HOME_DIR/docs/business-state.md"
MAILBOX_DIR="$HOME_DIR/broadcast/mailbox"
WEEKLY_DIR="$HOME_DIR/docs/weekly-sync"

# Semana ISO e ano
YEAR=$(date +%Y)
WEEK=$(date +%V)
TODAY=$(date +%Y-%m-%d)
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%S)

OUTPUT_FILE="$WEEKLY_DIR/${YEAR}-W${WEEK}.md"
METRICS_TMP=$(mktemp /tmp/weekly-sync-metrics.XXXXXX.json)

mkdir -p "$WEEKLY_DIR"

# Cleanup do temp file ao sair
trap "rm -f $METRICS_TMP" EXIT

# ==============================================================================
# Fase 1: Coleta de metricas + Gera scorecard (tudo em um unico Python)
# ==============================================================================

python3 << PYEOF
import json
import os
import re
from datetime import datetime, timezone, timedelta

HOME = "$HOME"
YEAR = "${YEAR}"
WEEK = "${WEEK}"
TODAY = "${TODAY}"
OUTPUT_FILE = "${OUTPUT_FILE}"

# ============================================================
# COLETA DE METRICAS
# ============================================================

# ---------- Sinais ----------
signals_data = {"active_signals": [], "archived_signals": []}
try:
    with open(os.path.join(HOME, "broadcast/signals.json"), "r") as f:
        signals_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    pass

active_signals = signals_data.get("active_signals", [])
total_signals = len(active_signals)
consumed_signals = sum(1 for s in active_signals if s.get("consumed_by"))

# Sinais nao consumidos com mais de 48h
now = datetime.now(timezone.utc)
stale_signals = []
for s in active_signals:
    if not s.get("consumed_by"):
        ts_str = s.get("timestamp", "")
        try:
            ts_str_clean = ts_str.replace("-03:00", "+00:00").replace("-02:00", "+00:00")
            if "+" not in ts_str_clean and "Z" not in ts_str_clean:
                ts_str_clean += "+00:00"
            ts_str_clean = ts_str_clean.replace("Z", "+00:00")
            ts = datetime.fromisoformat(ts_str_clean)
            if (now - ts).total_seconds() > 48 * 3600:
                desc = s.get("data", {}).get("description", s.get("type", ""))
                stale_signals.append({
                    "id": s.get("id", "?"),
                    "type": s.get("type", "?"),
                    "from": s.get("from", "?"),
                    "timestamp": s.get("timestamp", "?"),
                    "subject": str(desc)
                })
        except (ValueError, TypeError):
            pass

# ---------- Mailboxes ----------
mailbox_dir = os.path.join(HOME, "broadcast/mailbox")
total_messages = 0
read_messages = 0
agents_with_backlog = []

if os.path.isdir(mailbox_dir):
    for fname in sorted(os.listdir(mailbox_dir)):
        if not fname.endswith(".json"):
            continue
        agent_name = fname.replace(".json", "")
        try:
            with open(os.path.join(mailbox_dir, fname), "r") as f:
                mb = json.load(f)
            inbox = mb.get("inbox", [])
            agent_total = len(inbox)
            agent_read = sum(1 for m in inbox if m.get("read"))
            agent_unread = agent_total - agent_read
            total_messages += agent_total
            read_messages += agent_read
            if agent_unread > 0:
                agents_with_backlog.append({
                    "agent": "@" + agent_name,
                    "unread": agent_unread,
                    "total": agent_total
                })
        except (json.JSONDecodeError, FileNotFoundError):
            pass

# ---------- Oportunidades ----------
opp_file = os.path.join(HOME, "observations/opportunities.md")
pending_opps = []
executed_count = 0
try:
    with open(opp_file, "r") as f:
        content = f.read()
    pending_section = content.split("## Executadas")[0] if "## Executadas" in content else content
    pending_matches = re.findall(r"### (OPP-\d+[^\n]*)", pending_section)
    for m in pending_matches:
        pending_opps.append(m.strip())
    if "## Executadas" in content:
        exec_section = content.split("## Executadas")[1]
        if "## Descartadas" in exec_section:
            exec_section = exec_section.split("## Descartadas")[0]
        executed_count = len(re.findall(r"### OPP-\d+", exec_section))
except FileNotFoundError:
    pass

# ---------- Decisoes da semana ----------
decisions_file = os.path.join(HOME, "docs/decisions-log.md")
decisions_count = 0
try:
    with open(decisions_file, "r") as f:
        dec_content = f.read()
    decisions_count = len(re.findall(r"### \d{2}/\w{3}", dec_content))
except FileNotFoundError:
    pass

# ---------- Campanhas ativas ----------
campaigns = []
try:
    with open(os.path.join(HOME, "feedback-loop/results.json"), "r") as f:
        results = json.load(f)
    for c in results.get("campaigns", {}).get("entries", []):
        if c.get("status") == "active":
            campaigns.append({
                "name": c.get("name", "?"),
                "spend": c.get("spend", 0),
                "impressions": c.get("impressions", 0),
                "ctr": c.get("ctr", 0),
                "cpc": c.get("cpc", 0),
                "leads": c.get("leads", 0),
                "lp_views": c.get("landing_page_views", 0),
                "objective": c.get("objective", "?"),
                "angle": c.get("creative_angle", "?")
            })
except (FileNotFoundError, json.JSONDecodeError):
    pass

# ---------- Insights ----------
insights = []
try:
    with open(os.path.join(HOME, "feedback-loop/results.json"), "r") as f:
        results = json.load(f)
    insights = results.get("patterns", {}).get("insights", [])
except (FileNotFoundError, json.JSONDecodeError):
    pass

# ============================================================
# GERA SCORECARD MARKDOWN
# ============================================================

sig_pct = round(consumed_signals / total_signals * 100) if total_signals > 0 else 0
msg_pct = round(read_messages / total_messages * 100) if total_messages > 0 else 0
opp_pending = len(pending_opps)

lines = []
lines.append(f"# Weekly Sync — Semana {WEEK}/{YEAR}")
lines.append("")
lines.append(f"> Gerado em: {TODAY} | Script: weekly-sync.sh")
lines.append("")

# --- Scorecard ---
lines.append("## Scorecard")
lines.append("")
lines.append("| Metrica | Valor | Observacao |")
lines.append("|---------|-------|------------|")
lines.append(f"| Sinais emitidos | {total_signals} | — |")
lines.append(f"| Sinais consumidos | {consumed_signals} ({sig_pct}%) | {'OK' if sig_pct >= 70 else 'Baixo consumo'} |")
lines.append(f"| Mensagens enviadas | {total_messages} | — |")
lines.append(f"| Mensagens lidas | {read_messages} ({msg_pct}%) | {'OK' if msg_pct >= 70 else 'Backlog alto'} |")
lines.append(f"| Oportunidades detectadas | {opp_pending + executed_count} | — |")
lines.append(f"| Oportunidades executadas | {executed_count} | {'Nenhuma executada' if executed_count == 0 else ''} |")
lines.append(f"| Decisoes registradas | {decisions_count} | — |")
lines.append("")

# --- Campanhas Ativas ---
lines.append("## Campanhas Ativas")
lines.append("")
if campaigns:
    lines.append("| Campanha | Objetivo | Spend | CTR | CPC | LP Views | Leads | Angulo |")
    lines.append("|----------|----------|-------|-----|-----|----------|-------|--------|")
    for c in campaigns:
        ctr_str = f"{c['ctr']}%" if c['ctr'] else "—"
        cpc_str = f"R\${c['cpc']:.2f}" if c['cpc'] else "—"
        spend_str = f"R\${c['spend']:.2f}" if c['spend'] else "—"
        lines.append(f"| {c['name']} | {c['objective']} | {spend_str} | {ctr_str} | {cpc_str} | {c['lp_views']} | {c['leads']} | {c['angle']} |")
    lines.append("")
    total_spend = sum(c.get("spend", 0) for c in campaigns)
    total_lp = sum(c.get("lp_views", 0) for c in campaigns)
    total_leads = sum(c.get("leads", 0) for c in campaigns)
    lines.append(f"**Totais:** R\${total_spend:.2f} gastos | {total_lp} LP views | {total_leads} leads")
    lines.append("")
else:
    lines.append("_Nenhuma campanha ativa no momento._")
    lines.append("")

# --- Sinais Nao Consumidos (>48h) ---
lines.append("## Sinais Nao Consumidos (>48h)")
lines.append("")
if stale_signals:
    for s in stale_signals:
        lines.append(f"- **{s['id']}** ({s['type']}) de {s['from']} em {s['timestamp']}")
    lines.append("")
else:
    lines.append("_Nenhum sinal pendente com mais de 48h. OK._")
    lines.append("")

# --- Mailboxes com Backlog ---
lines.append("## Mailboxes com Backlog")
lines.append("")
if agents_with_backlog:
    lines.append("| Agente | Nao lidas | Total |")
    lines.append("|--------|-----------|-------|")
    for b in sorted(agents_with_backlog, key=lambda x: x["unread"], reverse=True):
        lines.append(f"| {b['agent']} | {b['unread']} | {b['total']} |")
    lines.append("")
else:
    lines.append("_Todas as mailboxes estao em dia. OK._")
    lines.append("")

# --- Oportunidades Pendentes ---
lines.append("## Oportunidades Pendentes")
lines.append("")
if pending_opps:
    for i, name in enumerate(pending_opps[:5], 1):
        lines.append(f"{i}. {name}")
    if opp_pending > 5:
        lines.append(f"   _... e mais {opp_pending - 5} oportunidades pendentes._")
    lines.append("")
else:
    lines.append("_Nenhuma oportunidade pendente._")
    lines.append("")

# --- Insights de Performance ---
lines.append("## Insights de Performance")
lines.append("")
if insights:
    for ins in insights[:7]:
        lines.append(f"- {ins}")
    lines.append("")
else:
    lines.append("_Sem insights registrados esta semana._")
    lines.append("")

# --- Recomendacoes ---
lines.append("## Recomendacoes para Proxima Semana")
lines.append("")

recs = []

if sig_pct < 70:
    recs.append(f"Consumo de sinais em {sig_pct}% — agentes precisam verificar broadcast ao serem ativados")

if agents_with_backlog:
    agents_str = ", ".join(b["agent"] for b in agents_with_backlog[:3])
    recs.append(f"Mailboxes com backlog: {agents_str} — processar mensagens pendentes")

if opp_pending > 0 and executed_count == 0:
    recs.append(f"{opp_pending} oportunidades detectadas e nenhuma executada — priorizar as de prioridade ALTA")
elif opp_pending > 3:
    recs.append(f"{opp_pending} oportunidades pendentes — avaliar e executar ou descartar")

if campaigns:
    zero_lead_campaigns = [c for c in campaigns if c.get("leads", 0) == 0]
    if zero_lead_campaigns:
        recs.append(f"{len(zero_lead_campaigns)} campanha(s) sem leads — monitorar conversao LP e considerar ajustes")

if decisions_count < 2:
    recs.append("Poucas decisoes registradas — garantir que decisoes estrategicas estejam sendo logadas")

if not recs:
    recs.append("Semana saudavel — manter ritmo atual e monitorar metricas")

for i, rec in enumerate(recs[:5], 1):
    lines.append(f"{i}. {rec}")

lines.append("")
lines.append("---")
lines.append(f"_Gerado automaticamente por weekly-sync.sh em {TODAY}_")

# Escrever arquivo
with open(OUTPUT_FILE, "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"Scorecard gerado: {OUTPUT_FILE}")
PYEOF

# ==============================================================================
# Fase 2: Emitir sinal WEEKLY_SYNC_COMPLETE no broadcast
# ==============================================================================

python3 << PYEOF
import json

signals_file = "${SIGNALS_JSON}"
year = "${YEAR}"
week = "${WEEK}"
timestamp = "${TIMESTAMP}"
output_file = "${OUTPUT_FILE}"

try:
    with open(signals_file, "r") as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    data = {
        "meta": {
            "description": "Canal de comunicacao entre agentes",
            "last_updated": "",
            "max_signals": 50,
            "auto_cleanup": "sinais com mais de 7 dias sao arquivados"
        },
        "active_signals": [],
        "archived_signals": []
    }

week_id = f"{year}-W{week}"

# Remover sinal WEEKLY_SYNC_COMPLETE anterior da mesma semana (idempotencia)
data["active_signals"] = [
    s for s in data["active_signals"]
    if not (s.get("type") == "WEEKLY_SYNC_COMPLETE" and s.get("data", {}).get("week") == week_id)
]

new_signal = {
    "id": f"sig_ws_{year}_W{week}",
    "type": "WEEKLY_SYNC_COMPLETE",
    "from": "@aios-master",
    "data": {
        "week": week_id,
        "report_file": output_file,
        "description": "Weekly sync concluido — scorecard gerado"
    },
    "confidence": 1.0,
    "timestamp": timestamp,
    "consumed_by": [],
    "ttl_days": 7
}

data["active_signals"].append(new_signal)
data["meta"]["last_updated"] = timestamp

with open(signals_file, "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Sinal WEEKLY_SYNC_COMPLETE emitido")
PYEOF

# ==============================================================================
# Fase 3: Atualizar business-state.md com data do ultimo sync
# ==============================================================================

python3 << PYEOF
import re

bs_file = "${BUSINESS_STATE}"
today = "${TODAY}"
week = "${WEEK}"
year = "${YEAR}"

try:
    with open(bs_file, "r") as f:
        content = f.read()

    sync_line = f"- **Semana:** {year}-W{week} | **Data:** {today} | **Report:** docs/weekly-sync/{year}-W{week}.md"

    if "## Ultimo Weekly Sync" in content:
        content = re.sub(
            r"## Ultimo Weekly Sync\n[^\n#]*",
            f"## Ultimo Weekly Sync\n{sync_line}",
            content
        )
    else:
        sync_section = f"\n## Ultimo Weekly Sync\n{sync_line}\n"
        if "## Equipe IA" in content:
            content = content.replace("## Equipe IA", sync_section + "\n## Equipe IA")
        else:
            content += sync_section

    with open(bs_file, "w") as f:
        f.write(content)

    print(f"business-state.md atualizado com ultimo sync: {year}-W{week}")
except FileNotFoundError:
    print("WARN: business-state.md nao encontrado — pulando atualizacao")
PYEOF

echo ""
echo "=== WEEKLY SYNC CONCLUIDO ==="
echo "Scorecard: $OUTPUT_FILE"
echo "Semana: $YEAR-W$WEEK"
echo "Data: $TODAY"
