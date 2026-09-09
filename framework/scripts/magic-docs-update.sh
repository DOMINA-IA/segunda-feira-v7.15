#!/bin/bash
# =============================================================================
# Magic Docs Auto-Update — Segunda-feira Framework
# Atualiza business-state.md e decisions-log.md com dados reais
# Gera snapshot diario em ~/docs/snapshots/
# Idempotente — seguro para rodar multiplas vezes no mesmo dia
# =============================================================================

set -euo pipefail

# --- Paths ---
HOME_DIR="$HOME"
RESULTS_JSON="$HOME_DIR/feedback-loop/results.json"
SIGNALS_JSON="$HOME_DIR/broadcast/signals.json"
MAILBOX_DIR="$HOME_DIR/broadcast/mailbox"
OPPORTUNITIES_MD="$HOME_DIR/framework/observations/opportunities.md"
BUSINESS_STATE="$HOME_DIR/docs/business-state.md"
DECISIONS_LOG="$HOME_DIR/docs/decisions-log.md"
SNAPSHOTS_DIR="$HOME_DIR/docs/snapshots"

TODAY=$(date "+%Y-%m-%d")
TODAY_BR=$(date "+%d/%b/%Y" | sed 's/Jan/Jan/;s/Feb/Fev/;s/Mar/Mar/;s/Apr/Abr/;s/May/Mai/;s/Jun/Jun/;s/Jul/Jul/;s/Aug/Ago/;s/Sep/Set/;s/Oct/Out/;s/Nov/Nov/;s/Dec/Dez/')

echo "[$TODAY] Magic Docs Auto-Update iniciado"

# --- Validacao ---
if [ ! -f "$RESULTS_JSON" ]; then
    echo "ERRO: $RESULTS_JSON nao encontrado"
    exit 1
fi
if [ ! -f "$SIGNALS_JSON" ]; then
    echo "ERRO: $SIGNALS_JSON nao encontrado"
    exit 1
fi
if [ ! -f "$BUSINESS_STATE" ]; then
    echo "ERRO: $BUSINESS_STATE nao encontrado"
    exit 1
fi

mkdir -p "$SNAPSHOTS_DIR"

# =============================================================================
# PARTE A: Extrair metricas do results.json
# =============================================================================

METRICS=$(python3 << 'PYEOF'
import json
import sys
import os
from datetime import datetime

results_path = os.path.expanduser("$HOME/feedback-loop/results.json")
signals_path = os.path.expanduser("$HOME/broadcast/signals.json")
mailbox_dir = os.path.expanduser("$HOME/broadcast/mailbox")
opportunities_path = os.path.expanduser("$HOME/framework/observations/opportunities.md")

# --- Ler results.json ---
with open(results_path, "r") as f:
    results = json.load(f)

campaigns = results.get("campaigns", {}).get("entries", [])

# Filtrar campanhas ativas
active_campaigns = [c for c in campaigns if c.get("status") == "active"]
all_campaigns = campaigns

# Metricas de campanhas ativas
total_spend_active = sum(c.get("spend", 0) for c in active_campaigns)
total_leads_active = sum(c.get("leads", 0) for c in active_campaigns)
total_spend_all = sum(c.get("spend", 0) for c in all_campaigns)
total_leads_all = sum(c.get("leads", 0) for c in all_campaigns)

# CPL medio (apenas campanhas com leads > 0)
campaigns_with_leads = [c for c in all_campaigns if c.get("leads", 0) > 0 and c.get("cpl")]
cpl_medio = 0
if campaigns_with_leads:
    cpl_medio = sum(c["cpl"] for c in campaigns_with_leads) / len(campaigns_with_leads)

# Melhor campanha ativa (por CPC mais baixo entre as com cliques)
best_campaign = None
if active_campaigns:
    with_cpc = [c for c in active_campaigns if c.get("cpc") and c.get("cpc") > 0]
    if with_cpc:
        best_campaign = min(with_cpc, key=lambda c: c["cpc"])

# CTR medio das ativas
ctrs = [c.get("ctr", 0) for c in active_campaigns if c.get("ctr") and c.get("ctr") > 0]
ctr_medio = sum(ctrs) / len(ctrs) if ctrs else 0

# LP views total
lp_views_total = sum(c.get("landing_page_views", 0) for c in active_campaigns)

# Budget diario total (cents para reais)
budget_diario = sum(c.get("daily_budget_cents", 0) for c in active_campaigns) / 100

# --- Ler signals.json ---
with open(signals_path, "r") as f:
    signals = json.load(f)

active_signals = signals.get("active_signals", [])
signals_count = len(active_signals)

# Contar sinais por tipo
signal_types = {}
for sig in active_signals:
    t = sig.get("type", "UNKNOWN")
    signal_types[t] = signal_types.get(t, 0) + 1

# Verificar decisoes nao registradas (council_decision ou PROACTIVE_ACTION)
new_decisions = []
for sig in active_signals:
    sig_type = sig.get("type", "")
    if sig_type in ("council_decision", "PROACTIVE_ACTION"):
        new_decisions.append({
            "date": sig.get("timestamp", "")[:10],
            "type": sig_type,
            "from": sig.get("from", ""),
            "data": sig.get("data", {}),
            "id": sig.get("id", "")
        })

# --- Contar mailbox unread ---
mailbox_unread = 0
mailbox_details = {}
if os.path.isdir(mailbox_dir):
    for fname in os.listdir(mailbox_dir):
        if fname.endswith(".json"):
            fpath = os.path.join(mailbox_dir, fname)
            try:
                with open(fpath, "r") as f:
                    mbox = json.load(f)
                if isinstance(mbox, dict):
                    messages = mbox.get("messages", [])
                elif isinstance(mbox, list):
                    messages = mbox
                else:
                    messages = []
                unread = sum(1 for m in messages if not m.get("read", True))
                if unread > 0:
                    agent = fname.replace(".json", "")
                    mailbox_details[agent] = unread
                    mailbox_unread += unread
            except (json.JSONDecodeError, KeyError):
                pass

# --- Contar oportunidades pendentes ---
opportunities_pending = 0
if os.path.isfile(opportunities_path):
    with open(opportunities_path, "r") as f:
        content = f.read()
    # Contar headers ### OPP- na secao Pendentes
    in_pendentes = False
    for line in content.split("\n"):
        if "## Pendentes" in line:
            in_pendentes = True
        elif line.startswith("## ") and in_pendentes:
            in_pendentes = False
        elif in_pendentes and line.startswith("### OPP-"):
            opportunities_pending += 1

# --- Health score (0-100) ---
health = 100
# Penalizar se sem leads apos 3+ dias de campanha
# Penalizar se signals de QUALITY_DROP
for sig in active_signals:
    if sig.get("type") == "QUALITY_DROP":
        health -= 10
# Penalizar se oportunidades pendentes > 5
if opportunities_pending > 5:
    health -= 5
# Penalizar se mailbox unread > 10
if mailbox_unread > 10:
    health -= 5
health = max(0, min(100, health))

# --- Output como JSON para o bash consumir ---
output = {
    "campaigns_active": len(active_campaigns),
    "campaigns_total": len(all_campaigns),
    "total_spend_active": round(total_spend_active, 2),
    "total_spend_all": round(total_spend_all, 2),
    "total_leads_active": total_leads_active,
    "total_leads_all": total_leads_all,
    "cpl_medio": round(cpl_medio, 2),
    "ctr_medio": round(ctr_medio, 2),
    "lp_views_total": lp_views_total,
    "budget_diario": round(budget_diario, 2),
    "best_campaign_name": best_campaign.get("name", "N/A") if best_campaign else "N/A",
    "best_campaign_cpc": best_campaign.get("cpc", 0) if best_campaign else 0,
    "best_campaign_ctr": best_campaign.get("ctr", 0) if best_campaign else 0,
    "signals_active": signals_count,
    "signal_types": signal_types,
    "mailbox_unread": mailbox_unread,
    "mailbox_details": mailbox_details,
    "opportunities_pending": opportunities_pending,
    "health_score": health,
    "new_decisions": new_decisions,
    # Tabela de campanhas ativas para o business-state
    "active_campaigns_table": [],
}

# Montar tabela de campanhas ativas
for c in active_campaigns:
    output["active_campaigns_table"].append({
        "name": c.get("name", ""),
        "objective": c.get("objective", "Leads"),
        "spend": c.get("spend", 0),
        "impressions": c.get("impressions", 0),
        "ctr": c.get("ctr", 0),
        "cpc": c.get("cpc", 0),
        "lp_views": c.get("landing_page_views", 0),
        "leads": c.get("leads", 0),
        "status": c.get("status", ""),
    })

print(json.dumps(output))
PYEOF
)

if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao extrair metricas"
    exit 1
fi

echo "[$TODAY] Metricas extraidas com sucesso"

# =============================================================================
# PARTE B: Atualizar business-state.md (apenas secoes de metricas)
# =============================================================================

python3 << PYEOF
import json
import re
from datetime import datetime

metrics = json.loads('''$METRICS''')
today_br = "$TODAY_BR"
today = "$TODAY"
business_state_path = "$BUSINESS_STATE"

with open(business_state_path, "r") as f:
    content = f.read()

# --- Atualizar header "Ultima atualizacao" ---
content = re.sub(
    r'> Última atualização:.*?\|.*',
    f'> Última atualização: {today_br} | Atualizado por: /magic-docs (auto-update)',
    content
)

# --- Atualizar secao "Campanhas Meta Ads — Dados Reais" ---
# Encontrar e substituir a tabela de campanhas
campaigns_header_pattern = r'### Campanhas Meta Ads — Dados Reais.*?\n\n\|.*?\n\|[-\| ]+\n((\|.*?\n)*)'
campaigns = metrics["active_campaigns_table"]

if campaigns:
    date_pulled = today
    new_table_header = f"### Campanhas Meta Ads — Dados Reais (auto-update {today})\n\n"
    new_table = "| Campanha | Objetivo | Spend | Impressões | CTR | CPC | LP Views | Leads | Status |\n"
    new_table += "|----------|----------|-------|------------|-----|-----|----------|-------|--------|\n"
    for c in campaigns:
        name = c["name"]
        obj = c["objective"]
        spend = f"R\${c['spend']:.2f}"
        impressions = f"{c['impressions']:,}".replace(",", ".")
        ctr = f"{c['ctr']:.2f}%"
        cpc = f"R\${c['cpc']:.2f}"
        lp = str(c["lp_views"])
        leads = str(c["leads"])
        status = c["status"].capitalize()
        new_table += f"| {name} | {obj} | {spend} | {impressions} | {ctr} | {cpc} | {lp} | {leads} | {status} |\n"

    # Totais
    total_spend = metrics["total_spend_active"]
    total_lp = metrics["lp_views_total"]
    total_leads = metrics["total_leads_active"]
    new_table += f"\n**Totais:** R\${total_spend:.2f} gastos | {total_lp} LP views | {total_leads} leads\n"

    match = re.search(
        r'(### Campanhas Meta Ads — Dados Reais.*?\n\n)(\|.*?\n\|[-\| ]+\n(?:\|.*?\n)*)\n\*\*Totais.*?\n',
        content,
        re.DOTALL
    )
    if match:
        content = content[:match.start()] + new_table_header + new_table + content[match.end():]

# --- Atualizar secao "Sinais Ativos (Broadcast)" ---
signals_header_pattern = r'### Sinais Ativos \(Broadcast\)\n\n\|.*?\n\|[-\| ]+\n((\|.*?\n)*)'

signal_types = metrics.get("signal_types", {})
if signal_types:
    new_signals = "### Sinais Ativos (Broadcast)\n\n"
    new_signals += "| Sinal | Quantidade |\n"
    new_signals += "|-------|------------|\n"
    for stype, count in sorted(signal_types.items()):
        indicator = "**Alerta**" if stype in ("QUALITY_DROP", "DAILY_SCAN_ALERT") else "Info"
        new_signals += f"| {stype} | {count} ({indicator}) |\n"
    new_signals += f"\n**Total sinais ativos:** {metrics['signals_active']} | **Mailbox unread:** {metrics['mailbox_unread']} | **Oportunidades pendentes:** {metrics['opportunities_pending']}\n"

    match = re.search(
        r'### Sinais Ativos \(Broadcast\)\n\n\|.*?\n\|[-\| ]+\n(?:\|.*?\n)*',
        content,
        re.DOTALL
    )
    if match:
        content = content[:match.start()] + new_signals + content[match.end():]

# --- Atualizar "Insights de Performance" ---
insights_pattern = r'### Insights de Performance\n\n(- .*\n)*'
new_insights = "### Insights de Performance\n\n"
new_insights += f"- CTR médio {metrics['ctr_medio']:.2f}% "
if metrics['ctr_medio'] >= 2.0:
    new_insights += "(excelente — acima de 2% para Brasil)\n"
else:
    new_insights += "(abaixo do benchmark de 2%)\n"
new_insights += f"- Campanha **{metrics['best_campaign_name']}** lidera: melhor CPC (R\${metrics['best_campaign_cpc']:.2f})\n"
new_insights += f"- Budget diário total: R\${metrics['budget_diario']:.2f}/dia\n"
new_insights += f"- Total leads (ativas): {metrics['total_leads_active']} | LP views: {metrics['lp_views_total']}\n"
new_insights += f"- Health Score: {metrics['health_score']}/100\n"

match = re.search(insights_pattern, content)
if match:
    content = content[:match.start()] + new_insights + content[match.end():]

# --- Atualizar "Visao Geral" metricas ---
# Atualizar "Campanhas ativas" na tabela de Visao Geral
content = re.sub(
    r'\| Campanhas ativas \| .* \|',
    f"| Campanhas ativas | {metrics['campaigns_active']} |",
    content
)

with open(business_state_path, "w") as f:
    f.write(content)

print(f"business-state.md atualizado com sucesso")
PYEOF

echo "[$TODAY] business-state.md atualizado"

# =============================================================================
# PARTE C: Atualizar decisions-log.md (apenas novas decisoes automaticas)
# =============================================================================

python3 << PYEOF
import json
import os
from datetime import datetime

metrics = json.loads('''$METRICS''')
decisions_path = "$DECISIONS_LOG"
today = "$TODAY"

new_decisions = metrics.get("new_decisions", [])

if not new_decisions:
    print("Nenhuma decisao automatica nova para registrar")
else:
    with open(decisions_path, "r") as f:
        content = f.read()

    for decision in new_decisions:
        sig_id = decision.get("id", "")
        # Verificar se ja esta registrado (idempotencia)
        if sig_id in content:
            print(f"Decisao {sig_id} ja registrada — skip")
            continue

        date = decision.get("date", today)
        sig_type = decision.get("type", "")
        from_agent = decision.get("from", "")
        data = decision.get("data", {})

        # Montar descricao
        if sig_type == "PROACTIVE_ACTION":
            desc = data.get("action", data.get("description", "Acao proativa"))
            context = data.get("justification", data.get("context", "Auto-detectado"))
        elif sig_type == "council_decision":
            desc = data.get("decision", data.get("description", "Decisao do conselho"))
            context = data.get("context", "Conselho deliberativo")
        else:
            desc = str(data)
            context = sig_type

        entry = f"\n### {date} — {desc} (auto)\n"
        entry += f"- **Decisão:** {desc}\n"
        entry += f"- **Contexto:** {context}\n"
        entry += f"- **Quem:** {from_agent} (automático — {sig_id})\n"

        # Inserir apos o header do mes atual
        month_header = datetime.strptime(date, "%Y-%m-%d").strftime("## %B %Y")
        # Mapeamento para portugues
        month_map = {
            "January": "Janeiro", "February": "Fevereiro", "March": "Março",
            "April": "Abril", "May": "Maio", "June": "Junho",
            "July": "Julho", "August": "Agosto", "September": "Setembro",
            "October": "Outubro", "November": "Novembro", "December": "Dezembro"
        }
        for en, pt in month_map.items():
            month_header = month_header.replace(en, pt)

        if month_header in content:
            # Inserir logo apos o header do mes
            idx = content.index(month_header) + len(month_header)
            content = content[:idx] + "\n" + entry + content[idx:]
        else:
            # Criar secao do mes apos o header principal
            header_end = content.index("\n", content.index("## "))
            content = content[:header_end] + "\n\n" + month_header + "\n" + entry + content[header_end:]

        print(f"Decisao registrada: {sig_id}")

    with open(decisions_path, "w") as f:
        f.write(content)

print("decisions-log.md processado")
PYEOF

echo "[$TODAY] decisions-log.md processado"

# =============================================================================
# PARTE D: Gerar snapshot diario
# =============================================================================

python3 << PYEOF
import json
from datetime import datetime

metrics = json.loads('''$METRICS''')
today = "$TODAY"
snapshot_path = f"$SNAPSHOTS_DIR/{today}.json"

snapshot = {
    "date": today,
    "generated_at": datetime.now().isoformat(),
    "campaigns_active": metrics["campaigns_active"],
    "campaigns_total": metrics["campaigns_total"],
    "total_spend": metrics["total_spend_active"],
    "total_spend_all_time": metrics["total_spend_all"],
    "total_leads": metrics["total_leads_active"],
    "total_leads_all_time": metrics["total_leads_all"],
    "cpl_medio": metrics["cpl_medio"],
    "ctr_medio": metrics["ctr_medio"],
    "lp_views": metrics["lp_views_total"],
    "budget_diario": metrics["budget_diario"],
    "best_campaign": metrics["best_campaign_name"],
    "signals_active": metrics["signals_active"],
    "mailbox_unread": metrics["mailbox_unread"],
    "opportunities_pending": metrics["opportunities_pending"],
    "health_score": metrics["health_score"]
}

with open(snapshot_path, "w") as f:
    json.dump(snapshot, f, indent=2, ensure_ascii=False)

print(f"Snapshot salvo: {snapshot_path}")
PYEOF

echo "[$TODAY] Snapshot diario gerado"
echo "[$TODAY] Magic Docs Auto-Update concluido com sucesso"
