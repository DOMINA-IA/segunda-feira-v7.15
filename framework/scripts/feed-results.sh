#!/bin/bash
# feed-results.sh — Importa resultados no feedback loop do framework Segunda-feira
# Uso: bash ~/scripts/feed-results.sh <subcommand> [options]
# Subcomandos: campaign, content, whatsapp, sales, summary

set -euo pipefail

# --- Caminhos absolutos ---
RESULTS_FILE="$HOME/feedback-loop/results.json"
SIGNALS_FILE="$HOME/broadcast/signals.json"
SCRIPT_NAME="feed-results.sh"

# --- Cores ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# --- Helpers ---
log_ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_err()  { echo -e "${RED}[ERROR]${NC} $1"; }
log_info() { echo -e "${CYAN}[INFO]${NC} $1"; }

usage() {
    echo -e "${BOLD}feed-results.sh${NC} — Importar resultados no feedback loop"
    echo ""
    echo -e "${BOLD}Uso:${NC}"
    echo "  bash ~/scripts/feed-results.sh <subcomando> [opcoes]"
    echo ""
    echo -e "${BOLD}Subcomandos:${NC}"
    echo "  campaign   Adicionar/atualizar campanha Meta Ads"
    echo "  content    Adicionar post Instagram"
    echo "  whatsapp   Adicionar sequencia WhatsApp"
    echo "  sales      Adicionar venda"
    echo "  summary    Mostrar resumo do feedback loop (read-only)"
    echo ""
    echo -e "${BOLD}Exemplos:${NC}"
    echo "  bash ~/scripts/feed-results.sh campaign --name 'AIF-V2' --spend 50 --leads 5 --cpl 10"
    echo "  bash ~/scripts/feed-results.sh content --type reel --hook 'IA para empresarios' --reach 5000"
    echo "  bash ~/scripts/feed-results.sh whatsapp --name 'Reativacao MI' --sent 603 --delivered 580"
    echo "  bash ~/scripts/feed-results.sh sales --product 'Comunidade' --revenue 7970 --source meta_ads"
    echo "  bash ~/scripts/feed-results.sh summary"
    exit 0
}

validate_number() {
    local name="$1"
    local value="$2"
    if [[ -n "$value" ]] && ! echo "$value" | grep -qE '^-?[0-9]+\.?[0-9]*$'; then
        log_err "--$name deve ser numerico, recebeu: '$value'"
        exit 1
    fi
}

check_prereqs() {
    if ! command -v python3 &>/dev/null; then
        log_err "python3 nao encontrado. Instale Python 3."
        exit 1
    fi
    if [[ ! -f "$RESULTS_FILE" ]]; then
        log_err "results.json nao encontrado em $RESULTS_FILE"
        exit 1
    fi
}

emit_signal() {
    local section="$1"
    local entry_id="$2"
    local summary="$3"

    python3 << PYEOF
import json, os
from datetime import datetime

signals_file = "$SIGNALS_FILE"

if not os.path.exists(signals_file):
    data = {"meta": {"description": "Canal de comunicacao entre agentes", "last_updated": "", "max_signals": 50}, "active_signals": []}
else:
    with open(signals_file, 'r') as f:
        data = json.load(f)

sig = {
    "id": "sig_feed_${entry_id}",
    "type": "FEEDBACK_UPDATED",
    "from": "@ceo",
    "data": {
        "section": "$section",
        "entry_id": "$entry_id",
        "summary": "$summary"
    },
    "confidence": 1.0,
    "timestamp": datetime.now().isoformat(),
    "consumed_by": [],
    "ttl_days": 7
}

data["active_signals"].append(sig)
data["meta"]["last_updated"] = datetime.now().isoformat()

# Manter max 50 sinais
if len(data["active_signals"]) > 50:
    data["active_signals"] = data["active_signals"][-50:]

with open(signals_file, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

PYEOF
    log_info "Sinal FEEDBACK_UPDATED emitido no broadcast"
}

# ============================================================
# CAMPAIGN
# ============================================================
cmd_campaign() {
    local name="" status="active" platform="meta_ads" spend="" impressions="" clicks=""
    local ctr="" leads="" cpl="" creative_angle="" lp_variant="" notes="" campaign_id=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --name)       name="$2"; shift 2;;
            --id)         campaign_id="$2"; shift 2;;
            --status)     status="$2"; shift 2;;
            --platform)   platform="$2"; shift 2;;
            --spend)      spend="$2"; shift 2;;
            --impressions) impressions="$2"; shift 2;;
            --clicks)     clicks="$2"; shift 2;;
            --ctr)        ctr="$2"; shift 2;;
            --leads)      leads="$2"; shift 2;;
            --cpl)        cpl="$2"; shift 2;;
            --angle)      creative_angle="$2"; shift 2;;
            --lp)         lp_variant="$2"; shift 2;;
            --notes)      notes="$2"; shift 2;;
            *) log_err "Opcao desconhecida para campaign: $1"; exit 1;;
        esac
    done

    if [[ -z "$name" ]]; then
        log_err "--name e obrigatorio para campaign"
        exit 1
    fi

    # Validar numeros
    validate_number "spend" "$spend"
    validate_number "impressions" "$impressions"
    validate_number "clicks" "$clicks"
    validate_number "ctr" "$ctr"
    validate_number "leads" "$leads"
    validate_number "cpl" "$cpl"

    python3 << PYEOF
import json, sys
from datetime import datetime

with open("$RESULTS_FILE", 'r') as f:
    data = json.load(f)

name = """$name"""
campaign_id = """$campaign_id"""
entry_id = campaign_id if campaign_id else f"entry_{int(datetime.now().timestamp())}"

# Verificar duplicata por nome
existing_idx = None
for i, e in enumerate(data["campaigns"]["entries"]):
    if e["name"] == name:
        existing_idx = i
        break

entry = {
    "id": entry_id,
    "name": name,
    "platform": "$platform",
    "status": "$status",
    "date": datetime.now().strftime("%Y-%m-%d"),
}

# Campos opcionais numericos
for field, val in [
    ("spend", "$spend"), ("impressions", "$impressions"),
    ("clicks", "$clicks"), ("ctr", "$ctr"),
    ("leads", "$leads"), ("cpl", "$cpl")
]:
    if val:
        entry[field] = float(val)

# Calcular metricas derivadas
if "$clicks" and "$impressions" and not "$ctr":
    clicks = float("$clicks")
    impressions = float("$impressions")
    if impressions > 0:
        entry["ctr"] = round(clicks / impressions * 100, 2)

if "$spend" and "$leads" and not "$cpl":
    spend = float("$spend")
    leads = float("$leads")
    if leads > 0:
        entry["cpl"] = round(spend / leads, 2)

if "$spend" and "$clicks":
    spend = float("$spend")
    clicks = float("$clicks")
    if clicks > 0:
        entry["cpc"] = round(spend / clicks, 2)

# Campos opcionais texto
if """$creative_angle""":
    entry["creative_angle"] = """$creative_angle"""
if """$lp_variant""":
    entry["lp_variant"] = """$lp_variant"""
if """$notes""":
    entry["notes"] = """$notes"""

if existing_idx is not None:
    # Atualizar existente (merge)
    old = data["campaigns"]["entries"][existing_idx]
    old.update(entry)
    data["campaigns"]["entries"][existing_idx] = old
    action = "ATUALIZADA"
else:
    data["campaigns"]["entries"].append(entry)
    action = "ADICIONADA"

with open("$RESULTS_FILE", 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"CAMPAIGN_{action}|{entry['id']}|{name}")
PYEOF

    result=$(python3 << 'PYEOF2'
import json
with open("$HOME/feedback-loop/results.json", 'r') as f:
    data = json.load(f)
last = data["campaigns"]["entries"][-1]
print(f"{last.get('id','?')}|{last.get('name','?')}")
PYEOF2
    )

    local eid=$(echo "$result" | cut -d'|' -f1)
    log_ok "Campanha '$name' processada (ID: $eid)"
    emit_signal "campaigns" "$eid" "Campanha $name importada"
}

# ============================================================
# CONTENT
# ============================================================
cmd_content() {
    local type="" hook="" angle="" reach="" impressions="" likes="" comments=""
    local shares="" saves="" engagement="" watch_time="" retention="" follows="" notes=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --type)        type="$2"; shift 2;;
            --hook)        hook="$2"; shift 2;;
            --angle)       angle="$2"; shift 2;;
            --reach)       reach="$2"; shift 2;;
            --impressions) impressions="$2"; shift 2;;
            --likes)       likes="$2"; shift 2;;
            --comments)    comments="$2"; shift 2;;
            --shares)      shares="$2"; shift 2;;
            --saves)       saves="$2"; shift 2;;
            --engagement)  engagement="$2"; shift 2;;
            --watch-time)  watch_time="$2"; shift 2;;
            --retention)   retention="$2"; shift 2;;
            --follows)     follows="$2"; shift 2;;
            --notes)       notes="$2"; shift 2;;
            *) log_err "Opcao desconhecida para content: $1"; exit 1;;
        esac
    done

    if [[ -z "$type" ]]; then
        log_err "--type e obrigatorio (reel|carousel|static|story)"
        exit 1
    fi

    # Validar numeros
    for f_name in reach impressions likes comments shares saves engagement watch_time retention follows; do
        eval "validate_number \"$f_name\" \"\$$f_name\""
    done

    python3 << PYEOF
import json
from datetime import datetime

with open("$RESULTS_FILE", 'r') as f:
    data = json.load(f)

entry_id = f"entry_{int(datetime.now().timestamp())}"
hook = """$hook"""

# Verificar duplicata por hook + date (mesmo dia)
today = datetime.now().strftime("%Y-%m-%d")
existing_idx = None
for i, p in enumerate(data["content"]["posts"]):
    if p.get("hook") == hook and p.get("date") == today and hook:
        existing_idx = i
        break

entry = {
    "post_id": entry_id,
    "date": today,
    "type": "$type",
}

if hook:
    entry["hook"] = hook
if """$angle""":
    entry["angle"] = """$angle"""

# Campos numericos
for field, val in [
    ("reach", "$reach"), ("impressions", "$impressions"),
    ("likes", "$likes"), ("comments", "$comments"),
    ("shares", "$shares"), ("saves", "$saves"),
    ("engagement_rate", "$engagement"),
    ("watch_time_avg", "$watch_time"),
    ("retention_rate", "$retention"),
    ("follows", "$follows")
]:
    if val:
        entry[field] = float(val)

# Calcular engagement se nao fornecido
if not "$engagement" and "$reach":
    reach_val = float("$reach")
    if reach_val > 0:
        interactions = 0
        for m in ["$likes", "$comments", "$shares", "$saves"]:
            if m:
                interactions += float(m)
        entry["engagement_rate"] = round(interactions / reach_val * 100, 2)

if """$notes""":
    entry["notes"] = """$notes"""

if existing_idx is not None:
    old = data["content"]["posts"][existing_idx]
    old.update(entry)
    data["content"]["posts"][existing_idx] = old
    action = "ATUALIZADO"
else:
    data["content"]["posts"].append(entry)
    action = "ADICIONADO"

data["content"]["last_updated"] = today

with open("$RESULTS_FILE", 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"CONTENT_{action}|{entry['post_id']}")
PYEOF

    log_ok "Post '$type' processado (hook: '${hook:-sem hook}')"
    emit_signal "content" "entry_$(date +%s)" "Post $type importado: $hook"
}

# ============================================================
# WHATSAPP
# ============================================================
cmd_whatsapp() {
    local name="" sent="" delivered="" read_count="" replied="" clicked="" converted="" notes=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --name)      name="$2"; shift 2;;
            --sent)      sent="$2"; shift 2;;
            --delivered) delivered="$2"; shift 2;;
            --read)      read_count="$2"; shift 2;;
            --replied)   replied="$2"; shift 2;;
            --clicked)   clicked="$2"; shift 2;;
            --converted) converted="$2"; shift 2;;
            --notes)     notes="$2"; shift 2;;
            *) log_err "Opcao desconhecida para whatsapp: $1"; exit 1;;
        esac
    done

    if [[ -z "$name" ]]; then
        log_err "--name e obrigatorio para whatsapp"
        exit 1
    fi

    for f_name in sent delivered read_count replied clicked converted; do
        eval "validate_number \"$f_name\" \"\$$f_name\""
    done

    python3 << PYEOF
import json
from datetime import datetime

with open("$RESULTS_FILE", 'r') as f:
    data = json.load(f)

entry_id = f"entry_{int(datetime.now().timestamp())}"
name = """$name"""
today = datetime.now().strftime("%Y-%m-%d")

# Verificar duplicata por nome
existing_idx = None
for i, s in enumerate(data["whatsapp"]["sequences"]):
    if s.get("name") == name:
        existing_idx = i
        break

entry = {
    "sequence_id": entry_id,
    "name": name,
    "date_range": today,
}

for field, val in [
    ("total_sent", "$sent"), ("delivered", "$delivered"),
    ("read", "$read_count"), ("replied", "$replied"),
    ("clicked_link", "$clicked"), ("converted", "$converted")
]:
    if val:
        entry[field] = int(float(val))

# Metricas derivadas
sent_val = float("$sent") if "$sent" else 0
delivered_val = float("$delivered") if "$delivered" else 0
read_val = float("$read_count") if "$read_count" else 0
replied_val = float("$replied") if "$replied" else 0
converted_val = float("$converted") if "$converted" else 0

if delivered_val > 0:
    entry["delivery_rate"] = round(delivered_val / sent_val * 100, 2) if sent_val > 0 else 0
    entry["read_rate"] = round(read_val / delivered_val * 100, 2) if read_val else 0
if read_val > 0:
    entry["reply_rate"] = round(replied_val / read_val * 100, 2) if replied_val else 0
if sent_val > 0:
    entry["conversion_rate"] = round(converted_val / sent_val * 100, 2) if converted_val else 0

if """$notes""":
    entry["notes"] = """$notes"""

if existing_idx is not None:
    old = data["whatsapp"]["sequences"][existing_idx]
    old.update(entry)
    data["whatsapp"]["sequences"][existing_idx] = old
else:
    data["whatsapp"]["sequences"].append(entry)

data["whatsapp"]["last_updated"] = today

with open("$RESULTS_FILE", 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"OK|{entry['sequence_id']}")
PYEOF

    log_ok "Sequencia WhatsApp '$name' processada"
    emit_signal "whatsapp" "entry_$(date +%s)" "Sequencia $name importada"
}

# ============================================================
# SALES
# ============================================================
cmd_sales() {
    local product="" revenue="" source="" status="paid" quantity="1"
    local campaign_id="" payment_method="" ticket="" notes=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --product)    product="$2"; shift 2;;
            --revenue)    revenue="$2"; shift 2;;
            --source)     source="$2"; shift 2;;
            --status)     status="$2"; shift 2;;
            --quantity)   quantity="$2"; shift 2;;
            --campaign)   campaign_id="$2"; shift 2;;
            --payment)    payment_method="$2"; shift 2;;
            --ticket)     ticket="$2"; shift 2;;
            --notes)      notes="$2"; shift 2;;
            *) log_err "Opcao desconhecida para sales: $1"; exit 1;;
        esac
    done

    if [[ -z "$product" ]]; then
        log_err "--product e obrigatorio para sales"
        exit 1
    fi
    if [[ -z "$revenue" ]]; then
        log_err "--revenue e obrigatorio para sales"
        exit 1
    fi

    validate_number "revenue" "$revenue"
    validate_number "quantity" "$quantity"
    validate_number "ticket" "$ticket"

    python3 << PYEOF
import json
from datetime import datetime

with open("$RESULTS_FILE", 'r') as f:
    data = json.load(f)

entry_id = f"entry_{int(datetime.now().timestamp())}"
today = datetime.now().strftime("%Y-%m-%d")

entry = {
    "id": entry_id,
    "product": """$product""",
    "date": today,
    "revenue": float("$revenue"),
    "quantity": int(float("$quantity")),
    "status": "$status",
}

if """$source""":
    entry["source"] = """$source"""
if """$campaign_id""":
    entry["campaign_id"] = """$campaign_id"""
if """$payment_method""":
    entry["payment_method"] = """$payment_method"""

# Ticket: fornecido ou calculado
if "$ticket":
    entry["ticket"] = float("$ticket")
else:
    qty = int(float("$quantity"))
    if qty > 0:
        entry["ticket"] = round(float("$revenue") / qty, 2)

if """$notes""":
    entry["notes"] = """$notes"""

data["sales"]["transactions"].append(entry)
data["sales"]["last_updated"] = today

# Recalcular summary
txns = data["sales"]["transactions"]
paid = [t for t in txns if t.get("status") == "paid"]
refunded = [t for t in txns if t.get("status") == "refunded"]

total_rev = sum(t.get("revenue", 0) for t in paid)
total_sales = len(paid)
avg_ticket = round(total_rev / total_sales, 2) if total_sales > 0 else 0
refund_rate = round(len(refunded) / len(txns) * 100, 2) if txns else 0

# Best source
from collections import Counter
sources = Counter(t.get("source", "unknown") for t in paid)
best_source = sources.most_common(1)[0][0] if sources else ""

# Best product
products = Counter(t.get("product", "unknown") for t in paid)
best_product = products.most_common(1)[0][0] if products else ""

data["sales"]["summary"] = {
    "total_revenue": round(total_rev, 2),
    "total_sales": total_sales,
    "avg_ticket": avg_ticket,
    "refund_rate": refund_rate,
    "best_source": best_source,
    "best_product": best_product,
}

with open("$RESULTS_FILE", 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"OK|{entry_id}|R\${entry['revenue']:.2f}")
PYEOF

    log_ok "Venda '$product' processada (R\$$revenue)"
    emit_signal "sales" "entry_$(date +%s)" "Venda $product: R\$$revenue"
}

# ============================================================
# SUMMARY
# ============================================================
cmd_summary() {
    python3 << 'PYEOF'
import json

with open("$HOME/feedback-loop/results.json", 'r') as f:
    data = json.load(f)

print("\033[1m" + "=" * 60)
print("  FEEDBACK LOOP — RESUMO")
print("=" * 60 + "\033[0m")

# Campaigns
camps = data.get("campaigns", {}).get("entries", [])
active = [c for c in camps if c.get("status") == "active"]
completed = [c for c in camps if c.get("status") == "completed"]
total_spend = sum(c.get("spend", 0) for c in camps)
total_leads = sum(c.get("leads", 0) for c in camps)
avg_cpl = round(total_spend / total_leads, 2) if total_leads > 0 else 0

print(f"\n\033[1;36mCAMPANHAS\033[0m ({len(camps)} total | {len(active)} ativas | {len(completed)} concluidas)")
print(f"  Spend total: R${total_spend:.2f}")
print(f"  Leads total: {total_leads}")
print(f"  CPL medio:   R${avg_cpl:.2f}")
if camps:
    best = min([c for c in camps if c.get("cpl") and c["cpl"] > 0], key=lambda c: c["cpl"], default=None)
    if best:
        print(f"  Melhor CPL:   R${best['cpl']:.2f} ({best['name']})")

# Content
posts = data.get("content", {}).get("posts", [])
print(f"\n\033[1;36mCONTEUDO\033[0m ({len(posts)} posts)")
if posts:
    types = {}
    for p in posts:
        t = p.get("type", "?")
        types[t] = types.get(t, 0) + 1
    for t, c in types.items():
        print(f"  {t}: {c}")
    avg_eng = [p.get("engagement_rate", 0) for p in posts if p.get("engagement_rate")]
    if avg_eng:
        print(f"  Engagement medio: {round(sum(avg_eng)/len(avg_eng), 2)}%")
else:
    print("  (vazio)")

# WhatsApp
seqs = data.get("whatsapp", {}).get("sequences", [])
print(f"\n\033[1;36mWHATSAPP\033[0m ({len(seqs)} sequencias)")
if seqs:
    total_sent = sum(s.get("total_sent", 0) for s in seqs)
    total_conv = sum(s.get("converted", 0) for s in seqs)
    print(f"  Total enviados:  {total_sent}")
    print(f"  Total convertidos: {total_conv}")
    if total_sent > 0:
        print(f"  Conv rate global: {round(total_conv/total_sent*100, 2)}%")
else:
    print("  (vazio)")

# Sales
txns = data.get("sales", {}).get("transactions", [])
summary = data.get("sales", {}).get("summary", {})
print(f"\n\033[1;36mVENDAS\033[0m ({len(txns)} transacoes)")
if txns:
    print(f"  Receita total: R${summary.get('total_revenue', 0):.2f}")
    print(f"  Ticket medio:  R${summary.get('avg_ticket', 0):.2f}")
    print(f"  Melhor fonte:  {summary.get('best_source', '-')}")
    print(f"  Melhor produto: {summary.get('best_product', '-')}")
    print(f"  Taxa reembolso: {summary.get('refund_rate', 0)}%")
else:
    print("  (vazio)")

# Offers
offers = data.get("offers", {}).get("entries", [])
print(f"\n\033[1;36mOFERTAS\033[0m ({len(offers)} registradas)")
for o in offers:
    print(f"  {o.get('name', '?')} — R${o.get('price', 0)} | {o.get('leads', 0)} leads")

# Patterns
patterns = data.get("patterns", {})
winning = patterns.get("winning_angles", [])
insights = patterns.get("insights", [])
print(f"\n\033[1;36mPADROES\033[0m ({len(winning)} angulos vencedores | {len(insights)} insights)")
for w in winning:
    print(f"  Angulo: '{w['angle']}' — CPL medio R${w.get('avg_cpl', '?')} (n={w.get('sample_size', '?')})")

print("\n" + "=" * 60)
print(f"Versao: {data.get('meta', {}).get('version', '?')}")
print(f"Ultima atualizacao: {data.get('meta', {}).get('last_updated', '?')}")
print("=" * 60)

PYEOF
}

# ============================================================
# MAIN
# ============================================================
check_prereqs

if [[ $# -lt 1 ]]; then
    usage
fi

SUBCOMMAND="$1"
shift

case "$SUBCOMMAND" in
    campaign)  cmd_campaign "$@";;
    content)   cmd_content "$@";;
    whatsapp)  cmd_whatsapp "$@";;
    sales)     cmd_sales "$@";;
    summary)   cmd_summary;;
    help|-h|--help) usage;;
    *) log_err "Subcomando desconhecido: $SUBCOMMAND"; usage;;
esac
