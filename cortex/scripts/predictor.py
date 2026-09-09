#!/usr/bin/env python3
"""
CORTEX Predictor — Antecipa necessidades baseado em padrões.

Analisa session logs e detecta padrões recorrentes do CEO:
- Que tipo de tarefa faz em cada dia da semana
- Que dados pede após certos eventos
- Sequências de ações que se repetem

Gera sugestões proativas para a próxima sessão.
"""

import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict

SESSIONS_DIR = Path.home() / "cortex" / "sessions"
PREDICTIONS_FILE = Path.home() / "cortex" / "pulse" / "predictions.json"


def load_sessions(days=30):
    """Carrega sessões dos últimos N dias."""
    sessions = []
    cutoff = datetime.now() - timedelta(days=days)

    for f in sorted(SESSIONS_DIR.glob("*.json")):
        if f.name == "latest.json":
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            ts = datetime.fromisoformat(data.get("timestamp", ""))
            if ts > cutoff:
                data["_weekday"] = ts.strftime("%A")
                data["_hour"] = ts.hour
                data["_date"] = ts.strftime("%Y-%m-%d")
                sessions.append(data)
        except (json.JSONDecodeError, ValueError, KeyError):
            continue

    return sessions


def detect_weekly_patterns(sessions):
    """Detecta padrões por dia da semana."""
    weekday_agents = defaultdict(list)
    weekday_projects = defaultdict(list)
    weekday_actions = defaultdict(list)

    for s in sessions:
        day = s.get("_weekday", "")
        for agent in s.get("agents_used", []):
            weekday_agents[day].append(agent)
        for project in s.get("projects_touched", []):
            weekday_projects[day].append(project)
        for action in s.get("actions_performed", []):
            label = action.split(":")[0] if ":" in action else action[:20]
            weekday_actions[day].append(label)

    patterns = {}
    for day in weekday_agents:
        top_agents = Counter(weekday_agents[day]).most_common(3)
        top_projects = Counter(weekday_projects[day]).most_common(3)
        top_actions = Counter(weekday_actions[day]).most_common(3)

        if top_agents:
            patterns[day] = {
                "typical_agents": [a[0] for a in top_agents],
                "typical_projects": [p[0] for p in top_projects],
                "typical_actions": [a[0] for a in top_actions],
            }

    return patterns


def detect_sequences(sessions):
    """Detecta sequências de ações que se repetem."""
    # Pegar pares de ações consecutivas (entre sessões)
    pairs = Counter()
    for i in range(len(sessions) - 1):
        current_actions = sessions[i].get("actions_performed", [])
        next_actions = sessions[i + 1].get("actions_performed", [])

        for ca in current_actions[:3]:
            ca_label = ca.split(":")[0] if ":" in ca else ca[:20]
            for na in next_actions[:3]:
                na_label = na.split(":")[0] if ":" in na else na[:20]
                pairs[(ca_label, na_label)] += 1

    # Retornar pares que aparecem 2+ vezes
    return {f"{a} → {b}": count for (a, b), count in pairs.most_common(10) if count >= 2}


def generate_predictions():
    """Gera predições para a próxima sessão."""
    sessions = load_sessions(30)
    if len(sessions) < 3:
        return {"predictions": [], "session_count": len(sessions), "message": "Poucas sessões para predição (mínimo 3)"}

    # Padrões semanais
    weekly = detect_weekly_patterns(sessions)
    sequences = detect_sequences(sessions)

    # Gerar predições para HOJE
    today = datetime.now().strftime("%A")
    predictions = []

    if today in weekly:
        pattern = weekly[today]
        if pattern.get("typical_agents"):
            predictions.append({
                "type": "agent_prediction",
                "message": f"Hoje ({today}) você costuma usar: {', '.join('@' + a for a in pattern['typical_agents'][:3])}",
                "confidence": min(0.9, 0.3 + len(sessions) * 0.02),
            })
        if pattern.get("typical_projects"):
            predictions.append({
                "type": "project_prediction",
                "message": f"Projetos típicos de {today}: {', '.join(pattern['typical_projects'][:3])}",
                "confidence": min(0.8, 0.3 + len(sessions) * 0.015),
            })

    # Baseado na última sessão (sequência)
    if sessions:
        last = sessions[-1]
        last_actions = last.get("actions_performed", [])
        for action in last_actions[:2]:
            label = action.split(":")[0] if ":" in action else action[:20]
            for seq, count in sequences.items():
                if seq.startswith(label):
                    next_action = seq.split(" → ")[1]
                    predictions.append({
                        "type": "sequence_prediction",
                        "message": f"Após \"{label}\", você costuma fazer \"{next_action}\" ({count}x observado)",
                        "confidence": min(0.7, 0.2 + count * 0.15),
                    })

    # Pendentes da última sessão
    if sessions:
        last_pending = sessions[-1].get("left_pending", [])
        for item in last_pending[:2]:
            predictions.append({
                "type": "pending_reminder",
                "message": f"Pendente da última sessão: {item}",
                "confidence": 0.95,
            })

    result = {
        "generated_at": datetime.now().isoformat(),
        "session_count": len(sessions),
        "predictions": predictions,
        "weekly_patterns": weekly,
        "sequences": dict(list(sequences.items())[:5]),
    }

    PREDICTIONS_FILE.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def format_predictions_for_injection():
    """Formata predições para injeção no hook."""
    if not PREDICTIONS_FILE.exists():
        return ""

    try:
        data = json.loads(PREDICTIONS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return ""

    predictions = data.get("predictions", [])
    if not predictions:
        return ""

    # Filtrar por confiança > 0.5
    good = [p for p in predictions if p.get("confidence", 0) >= 0.5]
    if not good:
        return ""

    lines = ["[CORTEX Predict — sugestões baseadas em padrões]"]
    for p in good[:3]:
        conf = int(p.get("confidence", 0) * 100)
        lines.append(f"  [{conf}%] {p['message']}")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "inject":
        print(format_predictions_for_injection())
    else:
        result = generate_predictions()
        print(f"Predições geradas ({result['session_count']} sessões analisadas):")
        for p in result.get("predictions", []):
            conf = int(p.get("confidence", 0) * 100)
            print(f"  [{conf}%] {p['message']}")
        if not result.get("predictions"):
            print(f"  {result.get('message', 'Nenhuma predição')}")
