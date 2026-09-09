#!/usr/bin/env python3
"""
heuristic-efficacy — Heurística injetada de fato reduz retrabalho?

Motivação (Sprint 3, Grupo F — D2.5, elo "medir" do ciclo write→read→medir):
o router (~/brain/thalamus/router.py) injeta heurísticas validadas no prompt
via ~/cortex/scripts/heuristics_inject.py, e o hook trajectory-logger.py loga
a sequência real de tool calls de cada sessão em
~/.claude/.session-state/{session}-trajectory.jsonl. Até o Sprint 3 ninguém
cruzava os dois — não sabíamos se a heurística injetada reduzia retrabalho.

Desde a instrumentação (heuristics_inject.py, Sprint 3), toda injeção grava
uma linha em ~/cortex/heuristics-injected.jsonl com {ts, session, kind,
agent_ou_relevance, ids}. Este script cruza esse log com os arquivos de
trajetória por session_id: separa sessões COM injeção vs SEM injeção e
compara médias de retrabalho entre os dois grupos.

Proxies de retrabalho extraídos da trajetória (sem heurística nenhuma —
puramente contagem):
  - edits_repetidos : Edit/Write/MultiEdit no MESMO arquivo mais de 1x
  - bash_repetidos  : Bash com o MESMO comando (truncado a 80 chars) mais de 1x
  - tamanho         : total de tool calls rastreadas na sessão

Análise OFFLINE, sob demanda — sem cron por enquanto (dataset ainda pequeno).
Zero dependências externas.

Uso: python3 heuristic-efficacy.py [--json]
"""

import json
import sys
from collections import Counter
from pathlib import Path

HOME = Path.home()
INJECTED_LOG = HOME / "cortex" / "heuristics-injected.jsonl"
STATE_DIR = HOME / ".claude" / ".session-state"
MIN_SESSIONS = 10  # abaixo disso, "dados insuficientes" naquele grupo


def _load_jsonl(path):
    """Lê um JSONL tolerando linhas corrompidas/vazias — nunca crasha o script."""
    recs = []
    if not path.exists():
        return recs
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            recs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return recs


def sessions_with_injection():
    """Set de session_ids que tiveram ao menos uma heurística injetada."""
    recs = _load_jsonl(INJECTED_LOG)
    return {r.get("session") for r in recs if r.get("session")}


def trajectory_files():
    """Mapeia session_id → Path do respectivo *-trajectory.jsonl."""
    if not STATE_DIR.exists():
        return {}
    out = {}
    for p in STATE_DIR.glob("*-trajectory.jsonl"):
        session_id = p.name[: -len("-trajectory.jsonl")]
        out[session_id] = p
    return out


def rework_metrics(traj_path):
    """Extrai as 3 métricas de retrabalho de uma sessão a partir do trajectory.jsonl."""
    entries = _load_jsonl(traj_path)
    files = Counter()
    cmds = Counter()
    for e in entries:
        tool = e.get("tool", "")
        if tool in ("Edit", "Write", "MultiEdit") and e.get("file"):
            files[e["file"]] += 1
        elif tool == "Bash" and e.get("cmd"):
            cmds[e["cmd"]] += 1

    return {
        "edits_repetidos": sum(c - 1 for c in files.values() if c > 1),
        "bash_repetidos": sum(c - 1 for c in cmds.values() if c > 1),
        "tamanho": len(entries),
    }


def _avg(values):
    return round(sum(values) / len(values), 2) if values else 0.0


def main():
    as_json = "--json" in sys.argv

    injected_sessions = sessions_with_injection()
    traj_by_session = trajectory_files()

    com_injecao, sem_injecao = [], []
    for session_id, path in traj_by_session.items():
        m = rework_metrics(path)
        (com_injecao if session_id in injected_sessions else sem_injecao).append(m)

    n_com, n_sem = len(com_injecao), len(sem_injecao)
    insuficiente = n_com < MIN_SESSIONS or n_sem < MIN_SESSIONS

    stats = {
        grupo: {
            "edits_repetidos_media": _avg([m["edits_repetidos"] for m in dados]),
            "bash_repetidos_media": _avg([m["bash_repetidos"] for m in dados]),
            "tamanho_medio": _avg([m["tamanho"] for m in dados]),
        }
        for grupo, dados in (("com_injecao", com_injecao), ("sem_injecao", sem_injecao))
    }

    result = {
        "sessoes_com_injecao": n_com,
        "sessoes_sem_injecao": n_sem,
        "minimo_por_grupo": MIN_SESSIONS,
        "dados_insuficientes": insuficiente,
        **stats,
    }

    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print("═══ HEURISTIC EFFICACY — heurística injetada reduz retrabalho? ═══")
    print(f"Sessões COM injeção: {n_com} | Sessões SEM injeção: {n_sem} "
          f"(mínimo {MIN_SESSIONS}/grupo para comparar)")
    print()

    if insuficiente:
        print("⚠️  dados insuficientes — aguardando mais sessões nos dois grupos.")
        print("    (heuristics-injected.jsonl e as trajetórias ainda não acumularam histórico suficiente)")
        return 0

    print(f"{'Métrica':<28}{'COM injeção':>14}{'SEM injeção':>14}{'Δ':>10}")
    print("-" * 66)
    for key, label in (
        ("edits_repetidos_media", "Edits repetidos/sessão"),
        ("bash_repetidos_media", "Bash repetidos/sessão"),
        ("tamanho_medio", "Tamanho médio (tool calls)"),
    ):
        com = stats["com_injecao"][key]
        sem = stats["sem_injecao"][key]
        delta = round(com - sem, 2)
        print(f"{label:<28}{com:>14}{sem:>14}{delta:>+10}")

    print()
    print("Δ negativo = grupo COM injeção teve MENOS retrabalho (heurística ajudou).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
