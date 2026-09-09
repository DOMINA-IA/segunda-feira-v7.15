#!/usr/bin/env python3
"""
CORTEX Decision Engine — Proatividade + Outcome Tracking.

Dois módulos:
1. Decision Tracker — registra decisões com checkpoint de verificação
2. Decision Engine — analisa estado do negócio e gera alertas/sugestões

Arquivos:
- ~/cortex/decisions/active.json — decisões pendentes de verificação
- ~/cortex/decisions/history.json — decisões verificadas (outcome)
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

DECISIONS_DIR = Path.home() / "cortex" / "decisions"
ACTIVE_FILE = DECISIONS_DIR / "active.json"
HISTORY_FILE = DECISIONS_DIR / "history.json"
PULSE_FILE = Path.home() / "cortex" / "pulse" / "latest.json"
SIGNALS_FILE = Path.home() / "broadcast" / "signals.json"

DECISIONS_DIR.mkdir(parents=True, exist_ok=True)


# ─── Decision Tracker ───────────────────────────────────────

def track_decision(description, metric=None, baseline=None, expected=None, verify_days=2, project=None):
    """Registra uma decisão com checkpoint de verificação."""
    try:
        data = json.loads(ACTIVE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"decisions": []}

    decision = {
        "id": f"dec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": description,
        "project": project,
        "metric": metric,
        "baseline": baseline,
        "expected": expected,
        "actual": None,
        "made_at": datetime.now().strftime("%Y-%m-%d"),
        "verify_at": (datetime.now() + timedelta(days=verify_days)).strftime("%Y-%m-%d"),
        "status": "pending",
        "verdict": None,
    }

    data["decisions"].append(decision)
    ACTIVE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Decisão registrada: {decision['id']}")
    print(f"  Verificar em: {decision['verify_at']}")
    return decision


def verify_decision(decision_id, actual_value, verdict="success"):
    """Marca decisão como verificada com resultado."""
    try:
        data = json.loads(ACTIVE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Arquivo de decisões não encontrado")
        return

    # Encontrar decisão
    found = None
    for d in data["decisions"]:
        if d["id"] == decision_id:
            d["actual"] = actual_value
            d["verdict"] = verdict
            d["status"] = "verified"
            d["verified_at"] = datetime.now().strftime("%Y-%m-%d")
            found = d
            break

    if not found:
        print(f"Decisão não encontrada: {decision_id}")
        return

    ACTIVE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # Mover para histórico
    try:
        history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        history = {"decisions": []}

    history["decisions"].append(found)
    HISTORY_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")

    # Remover do ativo
    data["decisions"] = [d for d in data["decisions"] if d["id"] != decision_id]
    ACTIVE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Decisão verificada: {verdict} (actual: {actual_value})")
    return found


def get_overdue_decisions():
    """Retorna decisões vencidas (prazo de verificação passou)."""
    try:
        data = json.loads(ACTIVE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    now = datetime.now()
    overdue = []
    for d in data.get("decisions", []):
        if d.get("status") != "pending":
            continue
        try:
            verify_date = datetime.strptime(d["verify_at"], "%Y-%m-%d")
            if verify_date <= now:
                overdue.append(d)
        except (ValueError, KeyError):
            pass

    return overdue


def get_decision_stats():
    """Estatísticas de decisões."""
    try:
        history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        history = {"decisions": []}

    total = len(history.get("decisions", []))
    success = sum(1 for d in history.get("decisions", []) if d.get("verdict") == "success")
    failure = sum(1 for d in history.get("decisions", []) if d.get("verdict") == "failure")

    try:
        active = json.loads(ACTIVE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        active = {"decisions": []}

    pending = len([d for d in active.get("decisions", []) if d.get("status") == "pending"])

    return {
        "total_verified": total,
        "success": success,
        "failure": failure,
        "success_rate": round(success / total * 100, 1) if total > 0 else 0,
        "pending": pending,
        "overdue": len(get_overdue_decisions()),
    }


# ─── Decision Engine (Proatividade) ─────────────────────────

def run_decision_engine():
    """Analisa estado do negócio e gera alertas proativos."""
    alerts = []

    # 1. Decisões vencidas
    overdue = get_overdue_decisions()
    for d in overdue:
        alerts.append({
            "type": "DECISION_OVERDUE",
            "priority": "high",
            "message": f"Decisão vencida: \"{d['description'][:60]}\" — verificar resultado agora",
            "action": f"python3 ~/cortex/scripts/decision_engine.py verify {d['id']} VALOR success|failure",
        })

    # 2. Checar pulse para anomalias
    try:
        pulse = json.loads(PULSE_FILE.read_text(encoding="utf-8"))

        # CPL alto?
        ads = pulse.get("meta_ads", {})
        if ads.get("cpl"):
            try:
                cpl = float(ads["cpl"].replace(",", "."))
                if cpl > 15:
                    alerts.append({
                        "type": "CPL_HIGH",
                        "priority": "high",
                        "axis": "ops",
                        "message": f"CPL alto: R${cpl:.2f} — considerar pausar ou otimizar",
                        "action": "python3 ~/projetos/utm-manager/meta_ads.py alertas",
                    })
            except ValueError:
                pass

        # Muitos sinais ativos?
        signals = pulse.get("signals", {})
        if signals.get("active_count", 0) > 5:
            alerts.append({
                "type": "SIGNALS_BACKLOG",
                "priority": "normal",
                "axis": "meta",
                "message": f"{signals['active_count']} sinais ativos não consumidos",
                "action": "cat ~/broadcast/signals.json",
            })

    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # 3. WIP com itens antigos (>7 dias)
    try:
        from session_tracker import WIP_FILE
        wip = json.loads(WIP_FILE.read_text(encoding="utf-8"))
        for item in wip.get("items", []):
            if item.get("status") != "pending":
                continue
            try:
                created = datetime.fromisoformat(item["created"])
                if (datetime.now() - created).days > 7:
                    alerts.append({
                        "type": "WIP_STALE",
                        "priority": "normal",
                        "message": f"Item pendente há {(datetime.now() - created).days} dias: \"{item['description'][:50]}\"",
                        "action": "Concluir ou remover do WIP",
                    })
            except (ValueError, KeyError):
                pass
    except Exception:
        pass

    return alerts


def format_alerts_for_injection(alerts):
    """Formata alertas para injeção no contexto, agrupados por eixo META vs OPS."""
    if not alerts:
        return ""

    # Agrupar por axis (default meta se ausente)
    by_axis = {"meta": [], "ops": []}
    for a in alerts:
        axis = a.get("axis", "meta")
        by_axis.setdefault(axis, []).append(a)

    lines = []
    for axis_label, prefix in (("meta", "📐 META"), ("ops", "🎯 OPS")):
        bucket = by_axis.get(axis_label, [])
        if not bucket:
            continue
        high = [a for a in bucket if a["priority"] == "high"]
        normal = [a for a in bucket if a["priority"] == "normal"]
        lines.append(f"[CORTEX Alerts {prefix} — {len(bucket)} item(s)]")
        for a in high:
            lines.append(f"  !! {a['message']}")
        for a in normal[:3]:
            lines.append(f"  -- {a['message']}")

    return "\n".join(lines)


# ─── CLI ─────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  decision_engine.py track \"descrição\" [--metric X] [--baseline Y] [--expected Z] [--days N] [--project P]")
        print("  decision_engine.py verify DECISION_ID ACTUAL_VALUE success|failure")
        print("  decision_engine.py overdue")
        print("  decision_engine.py stats")
        print("  decision_engine.py alerts")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "track" and len(sys.argv) >= 3:
        desc = sys.argv[2]
        kwargs = {}
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--metric" and i + 1 < len(sys.argv):
                kwargs["metric"] = sys.argv[i + 1]; i += 2
            elif sys.argv[i] == "--baseline" and i + 1 < len(sys.argv):
                kwargs["baseline"] = sys.argv[i + 1]; i += 2
            elif sys.argv[i] == "--expected" and i + 1 < len(sys.argv):
                kwargs["expected"] = sys.argv[i + 1]; i += 2
            elif sys.argv[i] == "--days" and i + 1 < len(sys.argv):
                kwargs["verify_days"] = int(sys.argv[i + 1]); i += 2
            elif sys.argv[i] == "--project" and i + 1 < len(sys.argv):
                kwargs["project"] = sys.argv[i + 1]; i += 2
            else:
                i += 1
        track_decision(desc, **kwargs)

    elif cmd == "verify" and len(sys.argv) >= 5:
        verify_decision(sys.argv[2], sys.argv[3], sys.argv[4])

    elif cmd == "overdue":
        overdue = get_overdue_decisions()
        if overdue:
            print(f"{len(overdue)} decisões vencidas:")
            for d in overdue:
                print(f"  [{d['id']}] {d['description'][:60]} (venceu: {d['verify_at']})")
        else:
            print("Nenhuma decisão vencida.")

    elif cmd == "stats":
        stats = get_decision_stats()
        print(f"Decisões: {stats['total_verified']} verificadas ({stats['success_rate']}% sucesso)")
        print(f"  Pendentes: {stats['pending']} | Vencidas: {stats['overdue']}")

    elif cmd == "alerts":
        alerts = run_decision_engine()
        if alerts:
            print(format_alerts_for_injection(alerts))
        else:
            print("Nenhum alerta ativo.")
