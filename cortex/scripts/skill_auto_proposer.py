#!/usr/bin/env python3
"""
skill_auto_proposer.py — Detecta padrões repetidos e propõe skills novas

Adaptado de hermes-agent/agent/curator.py (NousResearch).
- Hermes faz inactivity-triggered review com fork agent
- SF faz batch analítico via episódios + heurísticas

Lógica:
1. Lê episódios dos últimos N dias
2. Agrupa por similaridade de summary (Jaccard de tokens)
3. Para cada cluster com ≥3 ocorrências em <7 dias:
   - Sumariza o workflow comum
   - Gera draft de skill em ~/.claude/skills/_proposed/
   - Envia mailbox para @spec-engineer revisar

Uso:
    python3 ~/cortex/scripts/skill_auto_proposer.py            # detecta e gera drafts
    python3 ~/cortex/scripts/skill_auto_proposer.py --dry-run  # só detecta, não cria
    python3 ~/cortex/scripts/skill_auto_proposer.py --days 7   # janela ajustada

Origem: hermes-agent curator.py + Segunda-feira consciousness engine.
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOME = Path.home()
EPISODIC_DIR = HOME / "consciousness" / "memory" / "episodic"
SKILLS_DIR = HOME / ".claude" / "skills"
PROPOSED_DIR = SKILLS_DIR / "_proposed"
MAILBOX = HOME / "broadcast" / "mailbox" / "spec-engineer.json"
STATE_FILE = HOME / ".claude" / ".skill-proposer-state.json"

EXCLUDED_AGENTS = {
    "autonomous-smoke", "brainstem", "consciousness", "@autonomous-smoke",
    "@brainstem", "@consciousness", "@@brainstem", "@@consciousness",
}

# Padrões que indicam episódio rotineiro (relatório de agente, não workflow novo).
# Skills devem capturar coisas que se REPETEM mas AINDA NÃO foram codificadas.
# Relatório rotineiro de agente já é parte do agente — não vira skill.
ROUTINE_EPISODE_PATTERNS = [
    # People-ops daily/weekly reports
    r"\bdaily\s+(standup|status|report|health)\b",
    r"\bweekly\s+(report|review|summary)\b",
    r"\bdormancy\s+\d{4}-W\d+\b",  # Dormancy 2026-W21
    r"\bATIVO=\d+",  # padrão de dormancy report
    # Dev sprint reports
    r"\bsprint\s+\w+\s*(concluíd|finaliz|completed)",
    r"\bSprint\s+[A-Z]\s+\w+",  # Sprint A/B/C de projeto X
    r"\bwarnings?\s+\d+|\berros?\s+\d+\s+arquivos",
    r"\btsc\s+\d+\s+erros?",  # tsc 0 erros, lint 0 warnings
    # Cost-watchdog patterns
    r"\btotal\s+sessão\b",
    r"\bpadrão\s+\w+\s+sessão\b",
    r"\bBash:\d+\s+Edit:\d+",
    # Traffic campaign reports
    r"Campanha\s+['\"][A-Z\-]+['\"]",  # Campanha 'RUDNEI-K-DARKPOST-V1'
    r"CPL\s+R\$[\d\.]+",  # CPL R$0.00
    # Generic noise
    r"^\[via Task\]",  # episódios via Task tool sem contexto
    r"^Tarefa completada(:|$)",  # placeholder genérico
]

STOPWORDS = {
    "a", "ao", "aos", "as", "com", "da", "das", "de", "do", "dos", "e", "em",
    "na", "nas", "no", "nos", "o", "os", "para", "por", "que", "se", "um",
    "uma", "uns", "umas", "the", "a", "an", "of", "to", "in", "on", "at",
    "via", "tarefa", "completada", "concluída", "desconhecida", "iniciada",
    "agente", "agent", "task", "feature", "novo", "novos", "nova", "novas",
    "via", "is", "are", "be", "this", "that", "and", "or", "but",
}


def is_routine_episode(summary: str) -> bool:
    """Detecta se o episódio é um relatório rotineiro de agente (não workflow novo)."""
    if not summary:
        return True
    for pattern in ROUTINE_EPISODE_PATTERNS:
        if re.search(pattern, summary, re.IGNORECASE):
            return True
    return False


def tokenize(text: str) -> set:
    """Tokens normalizados, sem stopwords e curtos."""
    if not text:
        return set()
    tokens = re.findall(r"[a-záàâãéêíóôõúçñ]{4,}", text.lower())
    return {t for t in tokens if t not in STOPWORDS}


def jaccard(a: set, b: set) -> float:
    """Similaridade Jaccard entre dois conjuntos."""
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def load_episodes(days: int) -> list:
    """Carrega episódios dos últimos N dias."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    episodes = []
    if not EPISODIC_DIR.exists():
        return episodes
    for jsonl in EPISODIC_DIR.glob("*.jsonl"):
        agent = jsonl.stem
        if agent in EXCLUDED_AGENTS:
            continue
        try:
            with jsonl.open() as f:
                for line in f:
                    try:
                        ep = json.loads(line.strip())
                    except json.JSONDecodeError:
                        continue
                    ts = ep.get("timestamp")
                    if not ts:
                        continue
                    try:
                        ep_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        continue
                    if ep_dt < cutoff:
                        continue
                    summary = ep.get("summary", "")
                    if not summary or "tarefa desconhecida" in summary.lower():
                        continue
                    if is_routine_episode(summary):
                        continue  # relatório rotineiro de agente ≠ workflow novo
                    episodes.append({
                        "id": ep.get("id"),
                        "agent": agent,
                        "timestamp": ts,
                        "summary": summary,
                        "tokens": tokenize(summary),
                        "result": (ep.get("outcome") or {}).get("result"),
                        "heuristic": (ep.get("lessons") or {}).get("heuristic", ""),
                    })
        except OSError:
            continue
    return episodes


def cluster_by_similarity(episodes: list, threshold: float = 0.35) -> list:
    """Agrupa episódios por similaridade Jaccard de summary."""
    clusters = []
    used = set()
    for i, ep in enumerate(episodes):
        if i in used:
            continue
        cluster = [ep]
        used.add(i)
        for j in range(i + 1, len(episodes)):
            if j in used:
                continue
            sim = jaccard(ep["tokens"], episodes[j]["tokens"])
            if sim >= threshold:
                cluster.append(episodes[j])
                used.add(j)
        if len(cluster) >= 3:
            clusters.append(cluster)
    return clusters


def common_tokens(cluster: list, top_n: int = 8) -> list:
    """Tokens mais comuns no cluster (excluindo stopwords)."""
    counter = Counter()
    for ep in cluster:
        counter.update(ep["tokens"])
    return [t for t, _ in counter.most_common(top_n)]


def generate_skill_slug(cluster: list) -> str:
    """Gera slug para a skill proposta a partir dos tokens dominantes."""
    common = common_tokens(cluster, 4)
    base = "-".join(common[:4]) if common else "padrão-detectado"
    return f"auto-{base[:60]}"


def generate_skill_draft(cluster: list, slug: str) -> str:
    """Gera markdown da skill proposta."""
    agents_freq = Counter(ep["agent"] for ep in cluster)
    primary_agent = agents_freq.most_common(1)[0][0]
    common = common_tokens(cluster, 8)
    sample_summaries = [ep["summary"][:200] for ep in cluster[:3]]
    heuristics = [ep["heuristic"] for ep in cluster if ep["heuristic"]]

    timespan_start = min(ep["timestamp"] for ep in cluster)
    timespan_end = max(ep["timestamp"] for ep in cluster)

    return f"""---
name: {slug}
description: SKILL PROPOSTA AUTOMATICAMENTE — padrão detectado {len(cluster)}x em {timespan_start[:10]}..{timespan_end[:10]}. Tokens dominantes: {", ".join(common)}.
status: proposed
proposed_at: {datetime.now().isoformat()}
proposed_by: skill_auto_proposer.py
based_on_episodes: {len(cluster)}
primary_agent: {primary_agent}
axis: meta
harnesses:
  claude-code: full
---

# /{slug}

> ⚠️ Skill PROPOSTA AUTOMATICAMENTE. Revise antes de promover para `~/.claude/skills/`.

## Padrão detectado

Detectados **{len(cluster)} episódios similares** entre {timespan_start[:10]} e {timespan_end[:10]}.

**Agente predominante:** @{primary_agent} ({agents_freq[primary_agent]}x)

**Tokens dominantes:** {", ".join(common)}

## Amostras (3 episódios representativos)

{chr(10).join(f'- "{s}"' for s in sample_summaries)}

## Heurísticas extraídas

{chr(10).join(f'- {h[:200]}' for h in heuristics[:5]) if heuristics else "_(nenhuma heurística capturada nos episódios)_"}

## Ação proposta para o CEO

Esta skill foi proposta automaticamente porque o padrão se repetiu {len(cluster)} vezes. Possíveis decisões:

1. **PROMOVER** → renomear arquivo, remover `_proposed/`, mover para `~/.claude/skills/{slug}.md`
2. **REFATORAR** → reescrever description + pipeline com base no padrão real
3. **CONSOLIDAR** → fundir com skill existente se houver sobreposição
4. **REJEITAR** → mover para `~/.claude/_archive/skills-rejected/`

## Pipeline (esqueleto — preencher manualmente)

```
1. {{passo 1 do workflow comum}}
2. {{passo 2}}
3. {{passo 3}}
```

## Multi-LLM

Como o padrão envolve @{primary_agent}, herdar o tier desse agente como default. Override conforme necessidade.

## Episódios fonte

{chr(10).join(f"- {ep['id']} ({ep['timestamp']})" for ep in cluster[:10])}
{f"... e mais {len(cluster) - 10} episódios" if len(cluster) > 10 else ""}

---

_Gerado por `skill_auto_proposer.py`. Para regenerar: `python3 ~/cortex/scripts/skill_auto_proposer.py`._
"""


def notify_spec_engineer(proposals: list):
    """Cria mensagem mailbox para @spec-engineer revisar."""
    MAILBOX.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if MAILBOX.exists():
        try:
            existing = json.loads(MAILBOX.read_text())
            if not isinstance(existing, list):
                existing = [existing]
        except (json.JSONDecodeError, OSError):
            existing = []
    msg = {
        "id": f"msg_{int(datetime.now().timestamp())}",
        "from": "@skill-auto-proposer",
        "to": "@spec-engineer",
        "type": "request",
        "subject": f"{len(proposals)} skills propostas automaticamente — revisar",
        "body": (
            f"Detector encontrou {len(proposals)} padrão(ões) repetido(s) em episódios recentes "
            f"e gerou drafts em ~/.claude/skills/_proposed/. Revisar para PROMOVER, REFATORAR, "
            f"CONSOLIDAR ou REJEITAR."
        ),
        "priority": "normal",
        "data": {
            "proposed_dir": str(PROPOSED_DIR),
            "proposals": [{"slug": p["slug"], "episode_count": p["count"]} for p in proposals],
        },
        "timestamp": datetime.now().isoformat(),
        "read": False,
        "thread_id": None,
    }
    existing.append(msg)
    MAILBOX.write_text(json.dumps(existing, indent=2, ensure_ascii=False))


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_run": None, "total_runs": 0, "total_proposed": 0}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Detector de padrões + propositor de skills")
    parser.add_argument("--days", type=int, default=7,
                        help="Janela de análise (dias). Default 7.")
    parser.add_argument("--threshold", type=float, default=0.35,
                        help="Similaridade Jaccard mínima. Default 0.35.")
    parser.add_argument("--min-occurrences", type=int, default=3,
                        help="Mínimo de ocorrências para virar skill. Default 3.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Só detecta, não cria arquivos nem mailbox.")
    parser.add_argument("--json", action="store_true",
                        help="Output estruturado.")
    args = parser.parse_args()

    print(f"🔍 Analisando episódios dos últimos {args.days} dias...", file=sys.stderr)
    episodes = load_episodes(args.days)
    print(f"   {len(episodes)} episódios com summary não-trivial", file=sys.stderr)

    if not episodes:
        print("Nenhum episódio para analisar.", file=sys.stderr)
        return 0

    clusters = cluster_by_similarity(episodes, threshold=args.threshold)
    clusters = [c for c in clusters if len(c) >= args.min_occurrences]
    print(f"   {len(clusters)} cluster(s) com ≥{args.min_occurrences} ocorrências", file=sys.stderr)

    if not clusters:
        if args.json:
            print(json.dumps({"clusters": 0, "proposals": []}))
        else:
            print("Nenhum padrão repetido suficiente para propor skill.")
        return 0

    PROPOSED_DIR.mkdir(parents=True, exist_ok=True)
    proposals = []
    for cluster in clusters:
        slug = generate_skill_slug(cluster)
        path = PROPOSED_DIR / f"{slug}.md"
        proposal = {
            "slug": slug,
            "count": len(cluster),
            "path": str(path),
            "primary_agent": Counter(ep["agent"] for ep in cluster).most_common(1)[0][0],
            "tokens": common_tokens(cluster, 6),
            "timespan": [
                min(ep["timestamp"] for ep in cluster),
                max(ep["timestamp"] for ep in cluster),
            ],
        }
        proposals.append(proposal)

        if not args.dry_run:
            draft = generate_skill_draft(cluster, slug)
            path.write_text(draft, encoding="utf-8")

    if not args.dry_run and proposals:
        notify_spec_engineer(proposals)
        state = load_state()
        state["last_run"] = datetime.now().isoformat()
        state["total_runs"] = state.get("total_runs", 0) + 1
        state["total_proposed"] = state.get("total_proposed", 0) + len(proposals)
        save_state(state)

    if args.json:
        print(json.dumps({"clusters": len(proposals), "proposals": proposals}, indent=2, ensure_ascii=False))
    else:
        print(f"\n📋 {len(proposals)} skill(s) proposta(s):\n")
        for p in proposals:
            print(f"  /{p['slug']}")
            print(f"     {p['count']} episódios · @{p['primary_agent']} predominante")
            print(f"     Tokens: {', '.join(p['tokens'][:6])}")
            print(f"     Arquivo: {p['path']}")
            print()
        if not args.dry_run:
            print(f"✅ Drafts em {PROPOSED_DIR}/")
            print(f"📬 Mailbox @spec-engineer atualizada")
            print(f"\nPróximo passo: revisar drafts e PROMOVER (mover para ~/.claude/skills/) ou rejeitar.")
        else:
            print("(--dry-run: nenhum arquivo criado)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
