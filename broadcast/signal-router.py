#!/usr/bin/env python3
"""
signal-router.py — Roteia sinais de ~/broadcast/signals.json para mailboxes.

Construído em 09-Mai-2026 a partir do levantamento dos 31 agentes:
- 25/31 agentes pediram explicitamente "ser acionados via signals.json"
- Sem este router, sinais ficam acumulados (46 ativos hoje, alguns desde 12-Abr)

Mapeia signal.type → [agentes destino] e deposita mensagens nas mailboxes.
Marca sinais com "routed: true" + "routed_to" + "routed_at" para idempotência.

Execução:
  python3 ~/broadcast/signal-router.py            # roteia pendentes
  python3 ~/broadcast/signal-router.py --dry-run  # mostra o que rotearia
  python3 ~/broadcast/signal-router.py --stats    # estatísticas
"""

import json
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

BROADCAST = Path.home() / "broadcast"
SIGNALS_FILE = BROADCAST / "signals.json"
MAILBOX_DIR = BROADCAST / "mailbox"
LOG_FILE = BROADCAST / "signal-router.log"

ROUTES = {
    "BRAIN_ALERT": ["mestre-do-conselho", "advogado-do-diabo"],
    "CONSOLIDATION_COMPLETE": ["dev", "prompt-engineer", "growth-hacker",
                                "rag-architect", "knowledge-builder"],
    "REFLECT_COMPLETE": ["analyst", "prompt-engineer"],
    "council_decision": ["mestre-do-conselho"],
    "ALERT": ["security-auditor", "advogado-do-diabo"],
    "PROACTIVE_ACTION": ["advogado-do-diabo"],
    "EVALUATION_READY": ["analyst", "mestre-do-conselho"],

    "offer_changed": ["cold-outreach", "copywriter", "market-intel",
                       "contract-analyst", "fabio-soares", "challenge-funnel"],
    "creative_fatigue": ["traffic", "content", "creative-director"],
    "campaign_update": ["analyst", "traffic"],
    "performance_alert": ["analyst", "traffic"],
    "lead_qualified": ["whatsapp-specialist"],
    "new_tool_detected": ["tool-curator"],
    "workflow_failure": ["automation-architect"],
    "INEMA_MINING_COMPLETE": ["vibe-coder", "tool-curator"],
    "trend_detected": ["swarm-simulator", "challenge-funnel"],
    "lp_conversion_drop": ["cro-specialist"],
    "agent_deployed": ["security-auditor"],
    "webhook_created": ["security-auditor"],
    "challenge_phase_complete": ["launch-strategist"],
    "contract_review": ["contract-analyst"],
    "content_brief": ["video-producer"],
    "dub_request": ["voice-ai-specialist"],
    "knowledge_update": ["knowledge-builder"],
    "cost_alert": ["cost-optimizer"],
    "competitor_move": ["offer-engineer", "traffic"],
}


def load_signals():
    if not SIGNALS_FILE.exists():
        return []
    try:
        return json.load(SIGNALS_FILE.open())
    except json.JSONDecodeError:
        return []


def save_signals(data):
    backup = SIGNALS_FILE.with_suffix(".json.bak")
    if SIGNALS_FILE.exists():
        shutil.copy2(SIGNALS_FILE, backup)
    SIGNALS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def load_mailbox(agent):
    """Lê mailbox aceitando 3 formatos: canonical {agent,inbox,last_checked},
    legacy-list [...], OU legacy-dict {messages:[...]}.
    Retorna lista de mensagens."""
    mb = MAILBOX_DIR / f"{agent}.json"
    if not mb.exists():
        return []
    try:
        data = json.load(mb.open())
        if isinstance(data, list):
            return data
        if not isinstance(data, dict):
            return []
        # Canonical: "inbox" primeiro; legacy: "messages"
        return data.get("inbox") or data.get("messages") or []
    except (json.JSONDecodeError, OSError):
        return []


def save_mailbox(agent, msgs):
    """Escreve no formato canonical {agent, inbox, last_checked} — compat com send-mail.sh.
    Preserva last_checked existente quando possível."""
    mb = MAILBOX_DIR / f"{agent}.json"
    last_checked = None
    if mb.exists():
        try:
            existing = json.load(mb.open())
            if isinstance(existing, dict):
                last_checked = existing.get("last_checked")
        except json.JSONDecodeError:
            pass
    canonical = {
        "agent": f"@{agent}",
        "inbox": msgs,
        "last_checked": last_checked,
    }
    mb.write_text(json.dumps(canonical, indent=2, ensure_ascii=False))


def already_routed_to(msgs, signal_id):
    return any(m.get("data", {}).get("id") == signal_id for m in msgs
               if isinstance(m, dict))


SF_NOTIFY = Path.home() / "scripts" / "sf-notify.sh"


def macos_notify(title, msg, urgency="info"):
    """Dispara notificação macOS via sf-notify.sh (best-effort, falha silenciosa)."""
    if not SF_NOTIFY.exists():
        return
    import subprocess
    try:
        subprocess.run(
            ["bash", str(SF_NOTIFY), title[:60], msg[:200], urgency],
            timeout=3, capture_output=True
        )
    except Exception:
        pass


def make_message(agent, signal):
    sig_id = signal.get("id", "sig_unknown")
    sig_type = signal.get("type", "?")
    body = (signal.get("action") or signal.get("justification")
            or signal.get("payload") or "")
    return {
        "id": f"msg_{int(datetime.now().timestamp())}_{sig_id}",
        "from": "@signal-router",
        "to": f"@{agent}",
        "type": "info" if signal.get("risk", "low") == "low" else "alert",
        "subject": f"[{sig_type}] {body[:60]}",
        "body": body,
        "priority": "high" if sig_type in ("ALERT", "BRAIN_ALERT") else "normal",
        "data": signal,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "read": False,
        "thread_id": None,
    }


def log(msg):
    ts = datetime.now(timezone.utc).isoformat()
    with LOG_FILE.open("a") as f:
        f.write(f"[{ts}] {msg}\n")


MAX_AGE_HOURS = 72


def signal_age_hours(sig):
    ts = sig.get("timestamp") or sig.get("created_at") or sig.get("ts")
    if not ts:
        return 0
    try:
        d = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - d).total_seconds() / 3600
    except (ValueError, TypeError):
        return 0


def route(dry_run=False):
    signals = load_signals()
    if not signals:
        return {"total": 0, "routed": 0, "skipped": 0, "unmapped": 0,
                "expired": 0, "by_type": {}, "by_agent": {}}

    routed_count = 0
    skipped = 0
    unmapped = 0
    expired = 0
    by_type = defaultdict(int)
    by_agent = defaultdict(int)

    mailbox_cache = {}

    for sig in signals:
        if not isinstance(sig, dict):
            continue
        if sig.get("routed") or sig.get("expired"):
            skipped += 1
            continue

        age = signal_age_hours(sig)
        if age > MAX_AGE_HOURS:
            sig["expired"] = True
            sig["expired_at"] = datetime.now(timezone.utc).isoformat()
            sig["expired_reason"] = f"age={age:.1f}h > {MAX_AGE_HOURS}h"
            expired += 1
            continue

        sig_type = sig.get("type", "")
        targets = ROUTES.get(sig_type, [])
        if not targets:
            unmapped += 1
            continue

        sig_id = sig.get("id", f"sig_{int(datetime.now().timestamp())}")
        if "id" not in sig:
            sig["id"] = sig_id

        for agent in targets:
            if agent not in mailbox_cache:
                mailbox_cache[agent] = load_mailbox(agent)

            if already_routed_to(mailbox_cache[agent], sig_id):
                continue

            mailbox_cache[agent].append(make_message(agent, sig))
            by_agent[agent] += 1
            routed_count += 1

        sig["routed"] = True
        sig["routed_at"] = datetime.now(timezone.utc).isoformat()
        sig["routed_to"] = targets
        by_type[sig_type] += 1

        if not dry_run:
            risk = (sig.get("risk") or "").lower()
            priority_high = sig_type in ("ALERT", "BRAIN_ALERT", "PROACTIVE_ACTION") or risk == "high"
            if priority_high:
                action = (sig.get("action") or sig.get("justification") or sig.get("payload") or "")[:160]
                urgency = "critical" if risk == "high" else "alert"
                macos_notify(f"[{sig_type}] → {targets[0]}", action, urgency)

    if not dry_run:
        for agent, msgs in mailbox_cache.items():
            save_mailbox(agent, msgs)
        save_signals(signals)
        log(f"Roteados {routed_count} sinais para {len(mailbox_cache)} mailboxes")

    return {
        "total": len(signals),
        "routed": routed_count,
        "skipped": skipped,
        "unmapped": unmapped,
        "expired": expired,
        "by_type": dict(by_type),
        "by_agent": dict(by_agent),
    }


def stats():
    signals = load_signals()
    by_type = defaultdict(lambda: {"total": 0, "routed": 0, "pending": 0})
    for sig in signals:
        if not isinstance(sig, dict):
            continue
        t = sig.get("type", "?")
        by_type[t]["total"] += 1
        if sig.get("routed"):
            by_type[t]["routed"] += 1
        else:
            by_type[t]["pending"] += 1

    print(f"{'Tipo':<28} {'Total':<7} {'Roteados':<10} {'Pendentes':<10} {'Mapeado?':<8}")
    print("-" * 70)
    for t, c in sorted(by_type.items(), key=lambda x: -x[1]["total"]):
        mapped = "sim" if t in ROUTES else "NÃO"
        print(f"{t:<28} {c['total']:<7} {c['routed']:<10} {c['pending']:<10} {mapped:<8}")

    print("\nTipos mapeados sem sinais ainda:")
    seen = set(by_type.keys())
    unused = sorted(set(ROUTES.keys()) - seen)
    for t in unused:
        print(f"  {t} → {', '.join(ROUTES[t])}")


def main():
    args = sys.argv[1:]
    if "--stats" in args:
        stats()
        return
    if "--routes" in args:
        for t, agents in sorted(ROUTES.items()):
            print(f"{t:<28} → {', '.join(agents)}")
        return

    dry = "--dry-run" in args
    result = route(dry_run=dry)
    mode = "DRY-RUN" if dry else "EXECUTADO"
    print(f"[{mode}] Sinais: {result['total']} total | "
          f"{result['routed']} roteados | {result['skipped']} já-roteados | "
          f"{result['unmapped']} sem mapeamento | "
          f"{result['expired']} expirados (>{MAX_AGE_HOURS}h)")
    if result["by_type"]:
        print("Por tipo:", dict(result["by_type"]))
    if result["by_agent"]:
        print("Por agente:", dict(result["by_agent"]))


if __name__ == "__main__":
    main()
