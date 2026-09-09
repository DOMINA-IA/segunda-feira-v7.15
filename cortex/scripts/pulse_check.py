#!/usr/bin/env python3
"""
CORTEX Pulse Check — Coleta dados em tempo real do negócio.

Roda 2x/dia via cron (09:00 e 18:00 BRT) ou sob demanda.
Coleta: Meta Ads, serviços VPS, leads, sinais.
Salva em ~/cortex/pulse/latest.json para injeção no hook.
"""

import json
import subprocess
import os
from pathlib import Path
from datetime import datetime

PULSE_DIR = Path.home() / "cortex" / "pulse"
PULSE_FILE = PULSE_DIR / "latest.json"
UTM_MANAGER = next((d for d in (Path.home() / "projetos" / "utm-manager", Path.home() / "utm-manager")
                    if (d / "meta_ads.py").exists()), Path.home() / "projetos" / "utm-manager")  # movido em 29-Jun; pulso ficou em "error" 908x
FEEDBACK_LOOP = Path.home() / "feedback-loop" / "results.json"
SIGNALS_FILE = Path.home() / "broadcast" / "signals.json"
WIP_FILE = Path.home() / "cortex" / "wip" / "active.json"

PULSE_DIR.mkdir(parents=True, exist_ok=True)


PY = next((p for p in ("/usr/local/bin/python3", "/usr/local/bin/python3") if Path(p).exists()), "python3")
# "python3" do daemon era o 3.9 do CommandLineTools, sem `requests` → "Meta Ads error" 908x desde 07-Ago.


def collect_meta_ads():
    """Coleta métricas rápidas do Meta Ads."""
    try:
        result = subprocess.run(
            [PY, str(UTM_MANAGER / "meta_ads.py"), "insights", "--dias", "3"],
            capture_output=True, text=True, timeout=30,
            cwd=str(UTM_MANAGER)
        )
        output = result.stdout or ""

        # Extrair CPL, spend, leads do output
        import re
        cpl_match = re.search(r'CPL[:\s]*R?\$?\s*([\d.,]+)', output)
        spend_match = re.search(r'(?:Investido|Spend|Gasto)[:\s]*R?\$?\s*([\d.,]+)', output)
        leads_match = re.search(r'(?:Leads|Resultados)[:\s]*(\d+)', output)

        return {
            "status": "ok",
            "cpl": cpl_match.group(1) if cpl_match else None,
            "spend": spend_match.group(1) if spend_match else None,
            "leads": int(leads_match.group(1)) if leads_match else None,
            "raw_preview": output[:300] if output else "Sem dados",
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def collect_signals():
    """Coleta sinais ativos do Nervous System."""
    try:
        data = json.loads(SIGNALS_FILE.read_text(encoding="utf-8"))
        # Sinais de sistema não precisam de consumo manual — excluir da contagem
        SYSTEM_SIGNAL_TYPES = {"BRAIN_ALERT", "CONSOLIDATION_COMPLETE"}
        if isinstance(data, list):
            active = [s for s in data
                      if not s.get("consumed_by")
                      and s.get("type") not in SYSTEM_SIGNAL_TYPES]
        else:
            active = [s for s in data.get("signals", [])
                      if not s.get("consumed")
                      and s.get("type") not in SYSTEM_SIGNAL_TYPES]
        # ALERT não pode ficar diluído na contagem: em 04-Set-2026 um ALERT de
        # sessão Telegram expirada ficou 14h invisível porque o Pulse só mostrava
        # "Sinais ativos: N". Alerta que não se distingue de rotina não é alerta.
        alerts = [
            {"agent": s.get("agent", "?"),
             "action": (s.get("action") or "")[:300],
             "ts": (s.get("ts") or "")[:16]}
            for s in active if s.get("type") == "ALERT"
        ]
        return {
            "active_count": len(active),
            "types": list(set(s.get("type", "unknown") for s in active[:10])),
            "alerts": alerts[:3],
        }
    except Exception:
        return {"active_count": 0, "types": [], "alerts": []}


def collect_wip():
    """Coleta itens WIP pendentes."""
    try:
        wip = json.loads(WIP_FILE.read_text(encoding="utf-8"))
        items = [i for i in wip.get("items", []) if i.get("status") == "pending"]
        return {
            "pending_count": len(items),
            "items": [i["description"][:60] for i in items[:5]],
        }
    except Exception:
        return {"pending_count": 0, "items": []}


def collect_feedback_summary():
    """Coleta resumo do feedback loop."""
    try:
        data = json.loads(FEEDBACK_LOOP.read_text(encoding="utf-8"))
        campaigns = data.get("campaigns", {}).get("entries", [])
        return {
            "total_campaigns": len(campaigns),
            "latest": campaigns[-1].get("name", "?") if campaigns else None,
        }
    except Exception:
        return {"total_campaigns": 0, "latest": None}


def collect_decisions_pending():
    """Coleta decisões aguardando verificação."""
    decisions_file = Path.home() / "cortex" / "decisions" / "active.json"
    try:
        data = json.loads(decisions_file.read_text(encoding="utf-8"))
        pending = [d for d in data.get("decisions", [])
                   if d.get("status") == "pending" and d.get("verify_at")]

        overdue = []
        now = datetime.now()
        for d in pending:
            try:
                verify_date = datetime.strptime(d["verify_at"], "%Y-%m-%d")
                if verify_date <= now:
                    overdue.append(d["description"][:60])
            except (ValueError, KeyError):
                pass

        return {
            "pending_count": len(pending),
            "overdue_count": len(overdue),
            "overdue": overdue[:3],
        }
    except Exception:
        return {"pending_count": 0, "overdue_count": 0, "overdue": []}


def run_pulse():
    """Executa pulse check completo."""
    pulse = {
        "timestamp": datetime.now().isoformat(),
        "meta_ads": collect_meta_ads(),
        "signals": collect_signals(),
        "wip": collect_wip(),
        "feedback": collect_feedback_summary(),
        "decisions": collect_decisions_pending(),
    }

    # Salvar
    PULSE_FILE.write_text(json.dumps(pulse, indent=2, ensure_ascii=False), encoding="utf-8")

    # Também salvar histórico
    history_file = PULSE_DIR / f"pulse_{datetime.now().strftime('%Y-%m-%d_%H')}.json"
    history_file.write_text(json.dumps(pulse, indent=2, ensure_ascii=False), encoding="utf-8")

    # Limpar histórico antigo (manter últimos 14 dias)
    for old_file in sorted(PULSE_DIR.glob("pulse_*.json"))[:-336]:  # 14 dias x 24h
        old_file.unlink()

    return pulse


def format_pulse_for_injection():
    """Formata pulse para injeção no hook."""
    if not PULSE_FILE.exists():
        return ""

    try:
        pulse = json.loads(PULSE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return ""

    # Verificar frescor (max 12h)
    try:
        ts = datetime.fromisoformat(pulse["timestamp"])
        hours_old = (datetime.now() - ts).total_seconds() / 3600
        if hours_old > 12:
            return ""  # Dados muito antigos
    except (ValueError, KeyError):
        return ""

    lines = ["[CORTEX Pulse — estado do negócio]"]

    # Meta Ads
    ads = pulse.get("meta_ads", {})
    if ads.get("status") == "ok":
        parts = []
        if ads.get("cpl"):
            parts.append(f"CPL: R${ads['cpl']}")
        if ads.get("leads"):
            parts.append(f"Leads: {ads['leads']}")
        if ads.get("spend"):
            parts.append(f"Spend: R${ads['spend']}")
        if parts:
            lines.append(f"  Meta Ads (3d): {' | '.join(parts)}")

    # Decisões vencidas
    decisions = pulse.get("decisions", {})
    if decisions.get("overdue_count", 0) > 0:
        lines.append(f"  Decisões vencidas: {decisions['overdue_count']} — verificar resultados")

    # Sinais
    signals = pulse.get("signals", {})
    for a in signals.get("alerts", []):
        lines.append(f"  \U0001F6A8 ALERTA {a['agent']} ({a['ts']}): {a['action']}")
    if signals.get("active_count", 0) > 0:
        n_alert = len(signals.get("alerts", []))
        resto = signals["active_count"] - n_alert
        if resto > 0:
            lines.append(f"  Sinais ativos: {resto}" + (f" (+{n_alert} alerta(s) acima)" if n_alert else ""))

    if len(lines) <= 1:
        return ""  # Nada relevante

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "inject":
        print(format_pulse_for_injection())
    else:
        pulse = run_pulse()
        print(f"Pulse check: {datetime.now().strftime('%H:%M')}")
        print(f"  Meta Ads: {pulse['meta_ads'].get('status')}")
        print(f"  Sinais: {pulse['signals'].get('active_count')} ativos")
        print(f"  WIP: {pulse['wip'].get('pending_count')} pendentes")
        print(f"  Decisões: {pulse['decisions'].get('pending_count')} pendentes ({pulse['decisions'].get('overdue_count')} vencidas)")
