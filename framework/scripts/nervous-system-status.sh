#!/bin/bash
# SEGUNDA-FEIRA — Nervous System Status Dashboard
# Read-only dashboard that visualizes the health of all nervous system components
# Usage: bash ~/scripts/nervous-system-status.sh

python3 << 'PYTHON_SCRIPT'
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────────────────────────
HOME = os.path.expanduser("~")
SIGNALS_FILE = os.path.join(HOME, "broadcast", "signals.json")
MAILBOX_DIR = os.path.join(HOME, "broadcast", "mailbox")
RESULTS_FILE = os.path.join(HOME, "feedback-loop", "results.json")
OPPORTUNITIES_FILE = os.path.join(HOME, "observations", "opportunities.md")
PATTERNS_DIR = os.path.join(HOME, "patterns")

# ─── Colors ──────────────────────────────────────────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
WHITE = "\033[97m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"

# ─── Helpers ─────────────────────────────────────────────────────────────────
def safe_load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def parse_ts(ts_str):
    """Parse ISO timestamp string, return datetime (naive UTC)."""
    if not ts_str:
        return None
    try:
        ts_str = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo:
            dt = dt.replace(tzinfo=None)
        return dt
    except (ValueError, TypeError):
        return None

def age_hours(ts_str):
    dt = parse_ts(ts_str)
    if not dt:
        return 0
    return (datetime.now() - dt).total_seconds() / 3600

def colorize(value, green_thresh, yellow_thresh, invert=False):
    """Colorize a number. invert=True means lower is better."""
    if invert:
        if value <= green_thresh:
            return f"{GREEN}{value}{RESET}"
        elif value <= yellow_thresh:
            return f"{YELLOW}{value}{RESET}"
        else:
            return f"{RED}{value}{RESET}"
    else:
        if value >= green_thresh:
            return f"{GREEN}{value}{RESET}"
        elif value >= yellow_thresh:
            return f"{YELLOW}{value}{RESET}"
        else:
            return f"{RED}{value}{RESET}"

# ─── Broadcast Analysis ─────────────────────────────────────────────────────
signals_data = safe_load_json(SIGNALS_FILE)
if isinstance(signals_data, list):
    active_signals = signals_data
    signals_data = {"active_signals": signals_data, "meta": {}}
else:
    active_signals = signals_data.get("active_signals", [])
total_signals = len(active_signals)

consumed_count = sum(1 for s in active_signals if s.get("consumed_by"))
unconsumed_count = total_signals - consumed_count
consumed_pct = int((consumed_count / total_signals * 100)) if total_signals > 0 else 0

# Signals not consumed and older than 24h
stale_count = 0
for s in active_signals:
    if not s.get("consumed_by") and age_hours(s.get("timestamp", "")) > 24:
        stale_count += 1

last_signal_ts = ""
if active_signals:
    last_signal_ts = active_signals[-1].get("timestamp", "")

# ─── Mailbox Analysis ───────────────────────────────────────────────────────
mailbox_total = 0
mailbox_with_msgs = 0
mailbox_unread = 0
mailbox_backlog = 0  # unread messages older than 48h

if os.path.isdir(MAILBOX_DIR):
    for fname in sorted(os.listdir(MAILBOX_DIR)):
        if not fname.endswith(".json"):
            continue
        mailbox_total += 1
        data = safe_load_json(os.path.join(MAILBOX_DIR, fname))
        if isinstance(data, list):
            messages = data
        else:
            messages = data.get("messages", [])
        if messages:
            mailbox_with_msgs += 1
        for msg in messages:
            if not msg.get("read", False):
                mailbox_unread += 1
                if age_hours(msg.get("timestamp", "")) > 48:
                    mailbox_backlog += 1

# ─── Feedback Loop Analysis ─────────────────────────────────────────────────
results_data = safe_load_json(RESULTS_FILE)
campaigns_count = len(results_data.get("campaigns", {}).get("entries", []))
content_count = len(results_data.get("content", {}).get("entries", []))
whatsapp_count = len(results_data.get("whatsapp", {}).get("entries", []))
sales_count = len(results_data.get("sales", {}).get("entries", []))
offers_count = len(results_data.get("offers", {}).get("entries", []))
results_last_updated = results_data.get("meta", {}).get("last_updated", "N/A")

# ─── Opportunities Analysis ─────────────────────────────────────────────────
opp_pending = 0
opp_executed = 0
opp_high = 0

if os.path.isfile(OPPORTUNITIES_FILE):
    with open(OPPORTUNITIES_FILE, "r") as f:
        content = f.read()

    in_pending = False
    in_executed = False
    current_priority = None

    for line in content.split("\n"):
        stripped = line.strip()
        if "## Pendentes" in stripped:
            in_pending = True
            in_executed = False
        elif "## Executad" in stripped:
            in_pending = False
            in_executed = True
        elif stripped.startswith("## ") and not stripped.startswith("### "):
            in_pending = False
            in_executed = False

        if stripped.startswith("### OPP-"):
            if in_pending:
                opp_pending += 1
            elif in_executed:
                opp_executed += 1

        if "**Prioridade:**" in stripped and "ALTA" in stripped:
            if in_pending:
                opp_high += 1

# ─── Patterns Analysis ──────────────────────────────────────────────────────
pattern_files = 0
if os.path.isdir(PATTERNS_DIR):
    pattern_files = len([f for f in os.listdir(PATTERNS_DIR) if f.endswith(".md") and f != "README.md"])

# ─── Health Score ────────────────────────────────────────────────────────────
# Score components (0-100 each):
scores = []

# 1. Signal consumption rate (consumed/total)
if total_signals > 0:
    scores.append(consumed_pct)
else:
    scores.append(100)  # No signals = nothing to consume = healthy

# 2. No stale signals (>24h unconsumed)
if total_signals > 0:
    stale_pct = 100 - int(stale_count / total_signals * 100)
    scores.append(stale_pct)
else:
    scores.append(100)

# 3. Mailbox health (no backlog >48h)
if mailbox_unread > 0:
    backlog_pct = 100 - int(mailbox_backlog / max(mailbox_unread, 1) * 100)
    scores.append(backlog_pct)
else:
    scores.append(100)

# 4. Feedback loop populated (has data to learn from)
fl_domains = sum(1 for x in [campaigns_count, content_count, whatsapp_count, sales_count] if x > 0)
fl_score = int(fl_domains / 4 * 100)
scores.append(fl_score)

# 5. Opportunities not stagnating (executed vs pending ratio)
if opp_pending > 0:
    opp_score = max(0, 100 - (opp_pending * 10))  # Each pending deducts 10
    scores.append(opp_score)
else:
    scores.append(100)

# 6. Pattern library exists
pattern_score = min(100, pattern_files * 20)  # Each file = 20 points, max 100
scores.append(pattern_score)

health_score = int(sum(scores) / len(scores))

if health_score >= 70:
    status_emoji = "\U0001f7e2"  # green circle
    status_text = "OPERATIONAL"
    status_color = GREEN
elif health_score >= 50:
    status_emoji = "\U0001f7e1"  # yellow circle
    status_text = "DEGRADED"
    status_color = YELLOW
else:
    status_emoji = "\U0001f534"  # red circle
    status_text = "CRITICAL"
    status_color = RED

# ─── Agent Protocol Compliance ───────────────────────────────────────────────
# Count mailboxes as agents with protocol (they have a mailbox = registered)
agents_with_protocol = mailbox_total
agents_total = mailbox_total

# ─── Last Check Time ────────────────────────────────────────────────────────
now = datetime.now()
now_str = now.strftime("%Y-%m-%d %H:%M")
last_check = signals_data.get("meta", {}).get("last_updated", now_str)

# ─── Render Dashboard ───────────────────────────────────────────────────────
W = 56  # inner width

def box_top():
    return f"{CYAN}{BOLD}\u2554{'═' * W}\u2557{RESET}"

def box_mid():
    return f"{CYAN}\u2560{'═' * W}\u2563{RESET}"

def box_bot():
    return f"{CYAN}\u255a{'═' * W}\u255d{RESET}"

def box_line(text="", align="left"):
    """Render a line inside the box. Handles ANSI color codes in length calc."""
    # Strip ANSI codes for length calculation
    import re
    clean = re.sub(r'\033\[[0-9;]*m', '', text)
    padding = W - len(clean)
    if padding < 0:
        padding = 0
    if align == "center":
        left_pad = padding // 2
        right_pad = padding - left_pad
        return f"{CYAN}\u2551{RESET}{' ' * left_pad}{text}{' ' * right_pad}{CYAN}\u2551{RESET}"
    else:
        return f"{CYAN}\u2551{RESET}  {text}{' ' * (padding - 2)}{CYAN}\u2551{RESET}"

def section_header(title):
    return box_line(f"{BOLD}{WHITE}{title}{RESET}")

def metric_line(prefix, label, value, color=""):
    val_str = f"{color}{value}{RESET}" if color else str(value)
    return box_line(f"  {DIM}{prefix}{RESET} {label:<18s} {val_str}")

# Print dashboard
print()
print(box_top())
print(box_line(f"{BOLD}{WHITE}SEGUNDA-FEIRA  —  NERVOUS SYSTEM STATUS{RESET}", "center"))
print(box_line(f"{DIM}{now_str}{RESET}", "center"))
print(box_mid())
print(box_line())

# ── BROADCAST
print(section_header("BROADCAST"))
consumed_color = GREEN if consumed_pct >= 70 else (YELLOW if consumed_pct >= 40 else RED)
stale_color = GREEN if stale_count == 0 else (YELLOW if stale_count <= 2 else RED)
print(metric_line("├──", "Sinais ativos:", str(total_signals), BLUE))
print(metric_line("├──", "Consumidos:", f"{consumed_count} ({consumed_pct}%)", consumed_color))
print(metric_line("└──", "Nao consumidos:", f"{unconsumed_count} (>24h: {stale_count})", stale_color))
print(box_line())

# ── MAILBOXES
print(section_header("MAILBOXES"))
unread_color = GREEN if mailbox_unread == 0 else (YELLOW if mailbox_unread <= 5 else RED)
backlog_color = GREEN if mailbox_backlog == 0 else RED
print(metric_line("├──", "Total:", str(mailbox_total), BLUE))
print(metric_line("├──", "Com mensagens:", str(mailbox_with_msgs), YELLOW if mailbox_with_msgs > 0 else GREEN))
print(metric_line("├──", "Nao lidas:", str(mailbox_unread), unread_color))
print(metric_line("└──", "Backlog (>48h):", str(mailbox_backlog), backlog_color))
print(box_line())

# ── FEEDBACK LOOP
print(section_header("FEEDBACK LOOP"))
print(metric_line("├──", "Campanhas:", str(campaigns_count), GREEN if campaigns_count > 0 else DIM))
print(metric_line("├──", "Posts tracked:", str(content_count), GREEN if content_count > 0 else DIM))
print(metric_line("├──", "WhatsApp seqs:", str(whatsapp_count), GREEN if whatsapp_count > 0 else DIM))
print(metric_line("├──", "Vendas:", str(sales_count), GREEN if sales_count > 0 else DIM))
print(metric_line("└──", "Ofertas:", str(offers_count), GREEN if offers_count > 0 else DIM))
print(box_line())

# ── PATTERNS
print(section_header("PATTERNS"))
print(metric_line("└──", "Pattern files:", str(pattern_files), GREEN if pattern_files >= 3 else YELLOW))
print(box_line())

# ── OPPORTUNITIES
print(section_header("OPPORTUNITIES"))
pending_color = GREEN if opp_pending == 0 else (YELLOW if opp_pending <= 5 else RED)
high_color = GREEN if opp_high == 0 else (YELLOW if opp_high <= 2 else RED)
print(metric_line("├──", "Pendentes:", str(opp_pending), pending_color))
print(metric_line("├──", "Executadas:", str(opp_executed), GREEN if opp_executed > 0 else DIM))
print(metric_line("└──", "Prioridade ALTA:", str(opp_high), high_color))
print(box_line())

# ── HEALTH
print(section_header("HEALTH"))
score_color = GREEN if health_score >= 70 else (YELLOW if health_score >= 50 else RED)
print(metric_line("├──", "Last updated:", str(last_check), DIM))
print(metric_line("├──", "Score:", f"{health_score}%", score_color))
print(metric_line("└──", "Agents w/ proto:", f"{agents_with_protocol}/{agents_total}", GREEN))
print(box_line())

# ── STATUS
print(box_line(f"{BOLD}{status_color}STATUS: {status_emoji} {status_text}{RESET}", "center"))
print(box_line())

# ── Score Breakdown (compact)
print(box_mid())
print(box_line(f"{DIM}Score breakdown: signals={consumed_pct}% stale={scores[1]}% mailbox={scores[2]}%{RESET}"))
print(box_line(f"{DIM}  feedback={fl_score}% opps={scores[4]}% patterns={pattern_score}%{RESET}"))
print(box_bot())
print()

PYTHON_SCRIPT
