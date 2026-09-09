#!/usr/bin/env python3
"""
audit_ids.py — Audit de duplicação no framework Segunda-feira.

Detecta:
1. Agentes com descrições semanticamente próximas (Jaccard >= 0.4)
2. Skills com descrições sobrepostas (Jaccard >= 0.4)
3. Rules com triggers conflitantes (mesma keyword em múltiplas rules)

Zero dependencies. Roda em segundos.

Output: ~/cortex/reports/audit-ids-{YYYY-MM-DD}.md

Origem: passo E do framework-optimization-roadmap (10-Mai-2026).
"""

import re
import sys
from pathlib import Path
from datetime import datetime
from itertools import combinations

HOME = Path.home()
AGENTS_DIR = HOME / ".claude" / "agents"
SKILLS_DIR = HOME / ".claude" / "skills"
RULES_DIRS = [HOME / ".claude" / "rules", HOME / "cortex" / "vault" / "rules"]
REPORTS_DIR = HOME / "cortex" / "reports"

JACCARD_STRONG = 0.20  # overlap forte — candidato MERGE/REFACTOR
JACCARD_WEAK = 0.10    # overlap fraco — vale revisar mas pode ser KEEP-BOTH

STOPWORDS = {
    "para", "como", "que", "uma", "uso", "usar", "use", "com", "por", "the",
    "and", "of", "to", "in", "for", "is", "ou", "no", "na", "do", "da", "os",
    "as", "um", "se", "ao", "ser", "estar", "ter", "fazer", "agente", "skill",
    "framework", "este", "esta", "esse", "essa", "isso", "aqui", "também",
    "ainda", "agent", "tool", "command", "based", "gera", "cria", "criar",
    "gerar", "novo", "nova", "novas", "novos", "qualquer", "todo", "toda",
    "ele", "ela", "eles", "elas", "você", "voce", "seu", "sua", "seus", "suas",
    "está", "esta", "são", "foi", "será", "tem", "têm", "tinha", "deve",
}


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    block = text[3:end]
    out = {}
    current_key = None
    for line in block.split("\n"):
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([\w_-]+):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            current_key = key
            if val:
                out[key] = val.strip("'\"")
            else:
                out[key] = []
        elif line.startswith("- ") and current_key in out and isinstance(out[current_key], list):
            out[current_key].append(line[2:].strip().strip("'\""))
    return out


def tokenize(text: str) -> set:
    if not text:
        return set()
    text = text.lower()
    # Caracteres latinos minúsculos (a-z) + intervalo Unicode acentuados (à-ÿ exceto multiplicação ×)
    tokens = re.findall(r"[a-zà-öø-ÿ]{3,}", text)
    return {t for t in tokens if t not in STOPWORDS}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def load_md(directory: Path) -> list:
    items = []
    if not directory.exists():
        return items
    for f in directory.glob("*.md"):
        try:
            text = f.read_text(encoding="utf-8")
            fm = parse_frontmatter(text)
            name = fm.get("name") or fm.get("title") or f.stem
            desc = fm.get("description", "")
            triggers = fm.get("triggers", []) if isinstance(fm.get("triggers"), list) else []
            items.append({
                "file": f,
                "name": name,
                "description": desc,
                "triggers": triggers,
                "tokens": tokenize(desc),
            })
        except Exception:
            continue
    return items


def find_dupes(items: list, threshold: float) -> list:
    out = []
    for a, b in combinations(items, 2):
        score = jaccard(a["tokens"], b["tokens"])
        if score >= threshold:
            out.append({
                "a": a["name"],
                "b": b["name"],
                "score": round(score, 3),
                "a_desc": (a["description"] or "")[:100],
                "b_desc": (b["description"] or "")[:100],
            })
    out.sort(key=lambda d: -d["score"])
    return out


def find_trigger_conflicts(rules: list) -> list:
    trigger_map = {}
    for r in rules:
        for t in r.get("triggers", []):
            if not isinstance(t, str):
                continue
            t_norm = t.lower().strip()
            if not t_norm:
                continue
            trigger_map.setdefault(t_norm, []).append(r["name"])
    return [
        {"trigger": t, "rules": names}
        for t, names in trigger_map.items()
        if len(set(names)) > 1
    ]


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    agents = load_md(AGENTS_DIR)
    skills = load_md(SKILLS_DIR)
    rules = []
    for d in RULES_DIRS:
        rules.extend(load_md(d))

    agent_dupes_strong = find_dupes(agents, JACCARD_STRONG)
    agent_dupes_weak = [d for d in find_dupes(agents, JACCARD_WEAK) if d["score"] < JACCARD_STRONG]
    skill_dupes_strong = find_dupes(skills, JACCARD_STRONG)
    skill_dupes_weak = [d for d in find_dupes(skills, JACCARD_WEAK) if d["score"] < JACCARD_STRONG]
    trigger_conflicts = find_trigger_conflicts(rules)

    today = datetime.now().strftime("%Y-%m-%d")
    report_file = REPORTS_DIR / f"audit-ids-{today}.md"

    lines = [
        f"# Audit IDS — {today}",
        "",
        f"> Gerado por `~/cortex/scripts/audit_ids.py` | {datetime.now().isoformat()}",
        "",
        "## Inventário",
        f"- Agentes: **{len(agents)}**",
        f"- Skills: **{len(skills)}**",
        f"- Rules: **{len(rules)}**",
        f"- Threshold STRONG: {JACCARD_STRONG} | WEAK: {JACCARD_WEAK}",
        "",
        f"## Agentes — Overlap STRONG ({len(agent_dupes_strong)})",
        "",
    ]
    if agent_dupes_strong:
        lines.append("| Score | Agente A | Agente B |")
        lines.append("|-------|---------|---------|")
        for d in agent_dupes_strong[:20]:
            lines.append(f"| **{d['score']}** | `{d['a']}` | `{d['b']}` |")
        lines.append("")
        lines.append("### Detalhes")
        for d in agent_dupes_strong[:10]:
            lines.append(f"\n**{d['a']}** vs **{d['b']}** (score {d['score']})")
            lines.append(f"- A: {d['a_desc']}")
            lines.append(f"- B: {d['b_desc']}")
    else:
        lines.append("Nenhum overlap forte detectado.")

    lines.extend([
        "",
        f"## Agentes — Overlap WEAK ({len(agent_dupes_weak)})",
        "",
    ])
    if agent_dupes_weak:
        lines.append("| Score | Agente A | Agente B |")
        lines.append("|-------|---------|---------|")
        for d in agent_dupes_weak[:20]:
            lines.append(f"| {d['score']} | `{d['a']}` | `{d['b']}` |")
    else:
        lines.append("Nenhum overlap fraco.")

    lines.extend([
        "",
        f"## Skills — Overlap STRONG ({len(skill_dupes_strong)})",
        "",
    ])
    if skill_dupes_strong:
        lines.append("| Score | Skill A | Skill B |")
        lines.append("|-------|---------|---------|")
        for d in skill_dupes_strong[:30]:
            lines.append(f"| **{d['score']}** | `{d['a']}` | `{d['b']}` |")
        lines.append("")
        lines.append("### Detalhes (top 15)")
        for d in skill_dupes_strong[:15]:
            lines.append(f"\n**{d['a']}** vs **{d['b']}** (score {d['score']})")
            lines.append(f"- A: {d['a_desc']}")
            lines.append(f"- B: {d['b_desc']}")
    else:
        lines.append("Nenhum overlap forte detectado.")

    lines.extend([
        "",
        f"## Skills — Overlap WEAK ({len(skill_dupes_weak)})",
        "",
    ])
    if skill_dupes_weak:
        lines.append("| Score | Skill A | Skill B |")
        lines.append("|-------|---------|---------|")
        for d in skill_dupes_weak[:25]:
            lines.append(f"| {d['score']} | `{d['a']}` | `{d['b']}` |")
    else:
        lines.append("Nenhum overlap fraco.")

    lines.extend([
        "",
        f"## Trigger Conflicts em Rules ({len(trigger_conflicts)})",
        "",
    ])
    if trigger_conflicts:
        lines.append("| Trigger | Rules envolvidas |")
        lines.append("|---------|------------------|")
        for c in sorted(trigger_conflicts, key=lambda x: -len(x['rules']))[:25]:
            lines.append(f"| `{c['trigger']}` | {', '.join(c['rules'])} |")
    else:
        lines.append("Nenhum conflict detectado.")

    lines.extend([
        "",
        "## Decisão por Candidato",
        "",
        "Para cada candidato, marcar:",
        "- **MERGE** — combinar em um só (descrições muito próximas, escopo igual)",
        "- **KEEP-BOTH** — overlap aparente mas escopo diferente (ex: @dev vs @architect)",
        "- **REFACTOR** — extrair parte comum em terceiro (skill genérica + 2 specializations)",
        "",
        "## Próximos Passos",
        "",
        f"1. Revisar candidatos com score >= 0.5 (alta probabilidade de overlap real)",
        f"2. Marcar decisão por par",
        f"3. Aplicar MERGE em pelo menos 2 candidatos antes de fechar",
        "",
        f"## Como Rodar",
        "",
        "```bash",
        "python3 ~/cortex/scripts/audit_ids.py",
        "```",
        f"\nRoadmap: `~/cortex/vault/projects/framework-optimization-roadmap.md` (passo E)",
    ])

    report_file.write_text("\n".join(lines), encoding="utf-8")

    print(f"\n=== AUDIT IDS — {today} ===")
    print(f"Inventário: {len(agents)} agentes / {len(skills)} skills / {len(rules)} rules")
    print(f"Agentes STRONG ({JACCARD_STRONG}+): {len(agent_dupes_strong)}")
    print(f"Agentes WEAK ({JACCARD_WEAK}-{JACCARD_STRONG}): {len(agent_dupes_weak)}")
    print(f"Skills STRONG: {len(skill_dupes_strong)}")
    print(f"Skills WEAK: {len(skill_dupes_weak)}")
    print(f"Trigger conflicts: {len(trigger_conflicts)}")
    print(f"\nRelatório: {report_file}")

    if agent_dupes_strong:
        print(f"\nTop agente STRONG:")
        for d in agent_dupes_strong[:5]:
            print(f"  [{d['score']}] {d['a']} <-> {d['b']}")
    if skill_dupes_strong:
        print(f"\nTop skill STRONG:")
        for d in skill_dupes_strong[:8]:
            print(f"  [{d['score']}] {d['a']} <-> {d['b']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
