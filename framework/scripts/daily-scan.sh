#!/bin/bash
# =============================================================================
# Daily Scan — Segunda-feira Framework
# Análise automática de campanhas, sinais, mailboxes e oportunidades
# Standalone — não depende de Claude Code
# =============================================================================

set -euo pipefail

# --- Paths ---
HOME_DIR="$HOME"
RESULTS_JSON="$HOME_DIR/feedback-loop/results.json"
SIGNALS_JSON="$HOME_DIR/broadcast/signals.json"
MAILBOX_DIR="$HOME_DIR/broadcast/mailbox"
PATTERNS_DIR="$HOME_DIR/patterns"
OPPORTUNITIES="$HOME_DIR/framework/observations/opportunities.md"
OBSERVATIONS_DIR="$HOME_DIR/framework/observations"
LOGS_DIR="$HOME_DIR/logs"

DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
REPORT_FILE="$OBSERVATIONS_DIR/daily-scan-${DATE}.md"

# Prevent duplicate runs on same day
if [[ -f "$REPORT_FILE" ]]; then
    echo "[$DATE] Daily scan already ran today. Report exists: $REPORT_FILE"
    exit 0
fi

mkdir -p "$OBSERVATIONS_DIR" "$LOGS_DIR"

echo "[$DATE] Starting daily scan..."

# =============================================================================
# Python analysis script (inline)
# =============================================================================
python3 << 'PYTHON_SCRIPT'
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOME = "$HOME"
DATE = datetime.now().strftime("%Y-%m-%d")
TIMESTAMP = datetime.now(timezone.utc).isoformat()

RESULTS_JSON = f"{HOME}/feedback-loop/results.json"
SIGNALS_JSON = f"{HOME}/broadcast/signals.json"
MAILBOX_DIR = f"{HOME}/broadcast/mailbox"
PATTERNS_DIR = f"{HOME}/patterns"
OPPORTUNITIES = f"{HOME}/framework/observations/opportunities.md"
REPORT_FILE = f"{HOME}/framework/observations/daily-scan-{DATE}.md"

# --- Collectors ---
health_checks = []
anomalies = []
stale_signals = []
stale_mailbox = []
summary_lines = []
critical_alerts = []
new_opportunities = []

# =============================================================================
# 1. Health Check — componentes críticos
# =============================================================================
def check_health():
    components = {
        "feedback-loop/results.json": RESULTS_JSON,
        "broadcast/signals.json": SIGNALS_JSON,
        "broadcast/mailbox/": MAILBOX_DIR,
        "patterns/angles.md": f"{PATTERNS_DIR}/angles.md",
        "patterns/hooks.md": f"{PATTERNS_DIR}/hooks.md",
        "patterns/formats.md": f"{PATTERNS_DIR}/formats.md",
        "patterns/offers.md": f"{PATTERNS_DIR}/offers.md",
        "observations/opportunities.md": OPPORTUNITIES,
    }

    all_ok = True
    for name, path in components.items():
        exists = os.path.exists(path)
        if not exists:
            health_checks.append(f"- MISSING: `{name}`")
            all_ok = True  # not critical enough to stop
        else:
            # Check if file is not empty (for files, not dirs)
            if os.path.isfile(path):
                size = os.path.getsize(path)
                if size == 0:
                    health_checks.append(f"- EMPTY: `{name}` (0 bytes)")
                else:
                    health_checks.append(f"- OK: `{name}` ({size} bytes)")
            else:
                health_checks.append(f"- OK: `{name}` (directory)")

    return all_ok

# =============================================================================
# 2. Análise de results.json — anomalias em campanhas
# =============================================================================
def analyze_results():
    if not os.path.exists(RESULTS_JSON):
        anomalies.append("- results.json NAO ENCONTRADO — impossivel analisar campanhas")
        return

    with open(RESULTS_JSON, "r") as f:
        data = json.load(f)

    campaigns = data.get("campaigns", {}).get("entries", [])
    active_campaigns = [c for c in campaigns if c.get("status") == "active"]
    completed_campaigns = [c for c in campaigns if c.get("status") == "completed"]

    summary_lines.append(f"- Campanhas ativas: {len(active_campaigns)}")
    summary_lines.append(f"- Campanhas concluidas: {len(completed_campaigns)}")
    summary_lines.append(f"- Total campanhas: {len(campaigns)}")

    # --- CPL analysis (only for campaigns with leads > 0) ---
    cpls = [c["cpl"] for c in campaigns if c.get("cpl") and c["cpl"] > 0]
    if cpls:
        avg_cpl = sum(cpls) / len(cpls)
        summary_lines.append(f"- CPL medio historico: R${avg_cpl:.2f}")
        for c in active_campaigns:
            cpl = c.get("cpl")
            if cpl and cpl > avg_cpl * 2:
                msg = f"- ANOMALIA CPL: `{c['name']}` com CPL R${cpl:.2f} (media R${avg_cpl:.2f}, {cpl/avg_cpl:.1f}x acima)"
                anomalies.append(msg)
                critical_alerts.append(f"CPL anomalo em {c['name']}: R${cpl:.2f} vs media R${avg_cpl:.2f}")

    # --- CTR analysis (benchmark 2.0%) ---
    CTR_BENCHMARK = 2.0
    for c in active_campaigns:
        ctr = c.get("ctr")
        if ctr is not None and ctr < CTR_BENCHMARK:
            anomalies.append(f"- CTR ABAIXO: `{c['name']}` com CTR {ctr}% (benchmark {CTR_BENCHMARK}%)")

    # --- Landing page drop analysis ---
    for c in active_campaigns:
        clicks = c.get("link_clicks", 0)
        lp_views = c.get("landing_page_views", 0)
        if clicks and clicks > 3:  # minimum sample
            conversion = (lp_views / clicks) * 100 if clicks > 0 else 0
            if conversion < 60:
                anomalies.append(
                    f"- LP DROP: `{c['name']}` — {conversion:.0f}% clique-para-LP "
                    f"({lp_views}/{clicks} cliques, benchmark 70%+)"
                )

    # --- Budget utilization ---
    total_daily_budget = sum(
        c.get("daily_budget_cents", 0) / 100 for c in active_campaigns
    )
    total_spend = sum(c.get("spend", 0) for c in active_campaigns)
    if total_daily_budget > 0:
        summary_lines.append(f"- Budget diario total: R${total_daily_budget:.2f}")
        summary_lines.append(f"- Spend total (campanhas ativas): R${total_spend:.2f}")

    # --- Content gap ---
    content_entries = data.get("content", {}).get("entries", [])
    if len(content_entries) == 0:
        anomalies.append("- CONTENT GAP: Nenhum conteudo organico sendo trackeado em results.json")

    # --- WhatsApp gap ---
    wa_entries = data.get("whatsapp", {}).get("entries", [])
    if len(wa_entries) == 0:
        summary_lines.append("- WhatsApp: Nenhuma campanha de WhatsApp trackeada")

    # --- Patterns/insights count ---
    patterns = data.get("patterns", {})
    winning = patterns.get("winning_angles", [])
    insights = patterns.get("insights", [])
    summary_lines.append(f"- Angulos vencedores: {len(winning)}")
    summary_lines.append(f"- Insights acumulados: {len(insights)}")

# =============================================================================
# 3. Sinais não consumidos há mais de 24h
# =============================================================================
def check_stale_signals():
    if not os.path.exists(SIGNALS_JSON):
        stale_signals.append("- signals.json NAO ENCONTRADO")
        return

    with open(SIGNALS_JSON, "r") as f:
        data = json.load(f)

    now = datetime.now(timezone.utc)
    # Robust to both formats: list top-level OR dict with "active_signals"
    if isinstance(data, list):
        signals = data
    elif isinstance(data, dict):
        signals = data.get("active_signals", [])
    else:
        signals = []
    summary_lines.append(f"- Sinais ativos: {len(signals)}")

    for sig in signals:
        consumed = sig.get("consumed_by", [])
        ts_str = sig.get("timestamp", "")

        try:
            # Handle multiple timestamp formats
            if "T" in ts_str:
                # Remove timezone info for parsing
                clean = ts_str.replace("-03:00", "+00:00").replace("-0300", "+00:00")
                ts = datetime.fromisoformat(clean)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            else:
                continue
        except (ValueError, TypeError):
            continue

        age_hours = (now - ts).total_seconds() / 3600

        if len(consumed) == 0 and age_hours > 24:
            stale_signals.append(
                f"- SINAL NAO CONSUMIDO (>{age_hours:.0f}h): "
                f"`{sig.get('id')}` tipo `{sig.get('type')}` de `{sig.get('from')}` — "
                f"\"{sig.get('data', {}).get('message', sig.get('data', {}).get('description', 'sem descricao'))}\""
            )

# =============================================================================
# 4. Mailboxes com mensagens não lidas há mais de 48h
# =============================================================================
def check_stale_mailbox():
    if not os.path.isdir(MAILBOX_DIR):
        stale_mailbox.append("- Diretorio mailbox NAO ENCONTRADO")
        return

    now = datetime.now(timezone.utc)
    total_unread = 0
    total_read = 0

    for fname in sorted(os.listdir(MAILBOX_DIR)):
        if not fname.endswith(".json"):
            continue

        fpath = os.path.join(MAILBOX_DIR, fname)
        try:
            with open(fpath, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            stale_mailbox.append(f"- ERRO ao ler mailbox: `{fname}`")
            continue

        if isinstance(data, list):
            agent = fname.replace(".json", "")
            inbox = data
        else:
            agent = data.get("agent", fname.replace(".json", ""))
            inbox = data.get("inbox", [])

        for msg in inbox:
            if msg.get("read", False):
                total_read += 1
                continue

            total_unread += 1
            ts_str = msg.get("timestamp", "")
            try:
                clean = ts_str.replace("-03:00", "+00:00").replace("-0300", "+00:00")
                ts = datetime.fromisoformat(clean)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue

            age_hours = (now - ts).total_seconds() / 3600

            if age_hours > 48:
                stale_mailbox.append(
                    f"- MAILBOX `{agent}`: mensagem nao lida ha {age_hours:.0f}h — "
                    f"de `{msg.get('from')}`: \"{msg.get('subject', 'sem subject')}\""
                )

    summary_lines.append(f"- Mailbox: {total_unread} nao lidas, {total_read} lidas")

# =============================================================================
# 5. Gerar relatório diário
# =============================================================================
def generate_report():
    lines = []
    lines.append(f"# Daily Scan — {DATE}")
    lines.append("")
    lines.append(f"> Gerado automaticamente em {TIMESTAMP}")
    lines.append(f"> Script: ~/scripts/daily-scan.sh")
    lines.append("")

    # Summary
    lines.append("## Resumo")
    lines.append("")
    for s in summary_lines:
        lines.append(s)
    lines.append("")

    # Health
    lines.append("## Saude dos Componentes")
    lines.append("")
    for h in health_checks:
        lines.append(h)
    lines.append("")

    # Anomalies
    lines.append("## Anomalias Detectadas")
    lines.append("")
    if anomalies:
        for a in anomalies:
            lines.append(a)
    else:
        lines.append("- Nenhuma anomalia detectada.")
    lines.append("")

    # Stale signals
    lines.append("## Sinais Nao Consumidos (>24h)")
    lines.append("")
    if stale_signals:
        for s in stale_signals:
            lines.append(s)
    else:
        lines.append("- Todos os sinais foram consumidos.")
    lines.append("")

    # Stale mailbox
    lines.append("## Mailboxes com Mensagens Antigas (>48h)")
    lines.append("")
    if stale_mailbox:
        for m in stale_mailbox:
            lines.append(m)
    else:
        lines.append("- Nenhuma mensagem pendente ha mais de 48h.")
    lines.append("")

    # Critical alerts
    if critical_alerts:
        lines.append("## ALERTAS CRITICOS")
        lines.append("")
        for c in critical_alerts:
            lines.append(f"- {c}")
        lines.append("")

    # Write report
    with open(REPORT_FILE, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"[{DATE}] Report written to {REPORT_FILE}")

# =============================================================================
# 6. Emitir sinal DAILY_SCAN_ALERT se anomalias críticas
# =============================================================================
def emit_alert_signal():
    if not critical_alerts:
        return

    if not os.path.exists(SIGNALS_JSON):
        return

    with open(SIGNALS_JSON, "r") as f:
        data = json.load(f)

    # Remove previous DAILY_SCAN_ALERT from today (idempotent)
    data["active_signals"] = [
        s for s in data.get("active_signals", [])
        if not (s.get("type") == "DAILY_SCAN_ALERT" and s.get("timestamp", "").startswith(DATE))
    ]

    new_signal = {
        "id": f"sig_daily_{DATE.replace('-', '')}",
        "type": "DAILY_SCAN_ALERT",
        "from": "@daily-scan",
        "data": {
            "date": DATE,
            "alerts": critical_alerts,
            "report": REPORT_FILE,
            "description": f"{len(critical_alerts)} alerta(s) critico(s) detectado(s)"
        },
        "confidence": 0.9,
        "timestamp": TIMESTAMP,
        "consumed_by": [],
        "ttl_days": 3
    }

    data["active_signals"].append(new_signal)
    data["meta"]["last_updated"] = TIMESTAMP

    with open(SIGNALS_JSON, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[{DATE}] ALERT signal emitted: {len(critical_alerts)} critical alert(s)")

# =============================================================================
# 7. Append novas oportunidades ao opportunities.md (sem sobrescrever)
# =============================================================================
def append_opportunities():
    """
    Se anomalias foram detectadas que geram oportunidades automáticas,
    adiciona ao opportunities.md. Usa marcador para evitar duplicatas.
    """
    if not anomalies:
        return

    if not os.path.exists(OPPORTUNITIES):
        return

    with open(OPPORTUNITIES, "r") as f:
        existing = f.read()

    # Check for daily marker to avoid duplicates
    marker = f"daily-scan-{DATE}"
    if marker in existing:
        print(f"[{DATE}] Opportunities already appended for today. Skipping.")
        return

    # Find insertion point (before "## Executadas")
    insert_marker = "## Executadas"
    if insert_marker not in existing:
        return

    # Build new opportunity entries from anomalies
    new_items = []
    opp_counter = _get_next_opp_id(existing)

    for anomaly in anomalies:
        if "CPL" in anomaly and "ANOMALIA" in anomaly:
            opp_counter += 1
            new_items.append(f"""### OPP-{opp_counter:03d} | [AUTO] CPL anomalo detectado
- **Data:** {DATE}
- **Detectado por:** /daily-scan (automatico) <!-- {marker} -->
- **Dados:** {anomaly.replace('- ANOMALIA CPL: ', '')}
- **Acao sugerida:** Verificar campanha — pausar se CPL continuar acima de 2x a media.
- **Agente:** @traffic
- **Prioridade:** ALTA
- **Status:** Pendente

""")
        elif "LP DROP" in anomaly:
            opp_counter += 1
            new_items.append(f"""### OPP-{opp_counter:03d} | [AUTO] Drop de conversao clique-para-LP
- **Data:** {DATE}
- **Detectado por:** /daily-scan (automatico) <!-- {marker} -->
- **Dados:** {anomaly.replace('- LP DROP: ', '')}
- **Acao sugerida:** Verificar LP — carregamento, congruencia com criativo, teste mobile.
- **Agente:** @dev + @traffic
- **Prioridade:** ALTA
- **Status:** Pendente

""")

    if new_items:
        new_content = existing.replace(
            insert_marker,
            "".join(new_items) + insert_marker
        )
        with open(OPPORTUNITIES, "w") as f:
            f.write(new_content)
        print(f"[{DATE}] {len(new_items)} new opportunity(ies) appended to opportunities.md")


def _get_next_opp_id(text):
    """Extract highest OPP-NNN number from existing file."""
    import re
    matches = re.findall(r"OPP-(\d+)", text)
    if matches:
        return max(int(m) for m in matches)
    return 0

# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    check_health()
    analyze_results()
    check_stale_signals()
    check_stale_mailbox()
    generate_report()
    emit_alert_signal()
    append_opportunities()
    print(f"[{DATE}] Daily scan complete.")

PYTHON_SCRIPT

# =============================================================================
# CONSCIOUSNESS ENGINE INTEGRATION
# =============================================================================

# Avaliar workspace global (propostas pendentes → ignições)
if [[ -x "$HOME_DIR/consciousness/scripts/workspace.sh" ]]; then
    echo "[$DATE] Evaluating consciousness workspace..."
    "$HOME_DIR/consciousness/scripts/workspace.sh" evaluate 2>/dev/null || true
fi

# Verificar episódios não consolidados (lembrete)
UNCONSOLIDATED=0
for ep_file in "$HOME_DIR/consciousness/memory/episodic/"*.jsonl; do
    [[ -f "$ep_file" ]] || continue
    raw=$(grep -c '"consolidation_status":"raw"' "$ep_file" 2>/dev/null | head -1)
    [[ "$raw" =~ ^[0-9]+$ ]] || raw=0
    UNCONSOLIDATED=$((UNCONSOLIDATED + raw))
done

if [[ $UNCONSOLIDATED -gt 10 ]]; then
    echo "[$DATE] AVISO: $UNCONSOLIDATED episódios não consolidados. Consolidação noturna pendente."
fi

echo "[$DATE] Daily scan finished."
