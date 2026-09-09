#!/usr/bin/env python3
"""
CORTEX Auto-Linker — Detecta e cria relações automáticas entre notas.

Estratégias:
1. Notas do mesmo domínio → related
2. Feedback que menciona projeto → learned_from
3. Playbooks mencionados em patterns → extends
4. Infra mencionada em projetos → depends_on
5. Rules que referenciam patterns → extends
"""

import json
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path.home() / "cortex/scripts"))
from cortex_engine import scan_vault, parse_note, add_link, build_all_indexes

VAULT_DIR = Path.home() / "cortex/vault"


def find_mentions(note, all_ids):
    """Encontra IDs de outras notas mencionados no body ou tags."""
    body = note["body"].lower()
    fm = note["frontmatter"]
    mentions = set()

    for other_id in all_ids:
        if other_id == note["id"]:
            continue

        # Buscar menção direta do ID no body
        # Converter hífens para variações (com e sem)
        patterns = [
            other_id,
            other_id.replace("-", " "),
            other_id.replace("-", "_"),
        ]

        for p in patterns:
            if p in body:
                mentions.add(other_id)
                break

    return mentions


def auto_link_strategy():
    """Detecta e cria links automáticos."""
    notes = scan_vault()
    all_ids = {n["id"] for n in notes}
    notes_by_id = {n["id"]: n for n in notes}

    links_created = 0
    link_plan = []

    # 1. Feedback → Projeto (learned_from)
    feedback_notes = [n for n in notes if n["frontmatter"].get("type") == "feedback"]
    project_notes = [n for n in notes if n["frontmatter"].get("type") == "project"]

    for fb in feedback_notes:
        fb_name = fb["id"].lower()
        fb_body = fb["body"].lower()

        for proj in project_notes:
            proj_tags = [str(t).lower() for t in proj["frontmatter"].get("tags", [])]
            proj_name = proj["id"].lower()

            # Se feedback menciona nome do projeto
            for tag in proj_tags:
                if tag in fb_name or tag in fb_body:
                    link_plan.append((fb["id"], proj["id"], "learned_from"))
                    break

    # 2. Projeto → Infra (depends_on) — projetos que mencionam VPS, deploy
    infra_notes = [n for n in notes if n["frontmatter"].get("type") == "infra"]

    for proj in project_notes:
        proj_body = proj["body"].lower()
        for infra in infra_notes:
            infra_tags = [str(t).lower() for t in infra["frontmatter"].get("tags", [])]
            for tag in infra_tags:
                if tag in proj_body and tag not in ["dev", "devops"]:
                    link_plan.append((proj["id"], infra["id"], "depends_on"))
                    break

    # 3. Pattern → Playbook (extends) — patterns baseados em playbooks
    pattern_notes = [n for n in notes if n["frontmatter"].get("type") == "pattern"]
    playbook_notes = [n for n in notes if n["frontmatter"].get("type") == "playbook"]

    for pat in pattern_notes:
        pat_body = pat["body"].lower()
        for pb in playbook_notes:
            pb_tags = [str(t).lower() for t in pb["frontmatter"].get("tags", [])]
            pb_name = pb["id"].replace("-", " ")
            if pb_name in pat_body or any(t in pat_body for t in pb_tags if len(t) > 4):
                link_plan.append((pat["id"], pb["id"], "extends"))

    # 4. Notas com mesmos agentes e domínio → related (top connections only)
    for i, n1 in enumerate(notes):
        agents1 = set(n1["frontmatter"].get("agents", []))
        domain1 = set(n1["frontmatter"].get("domain", []) if isinstance(n1["frontmatter"].get("domain"), list) else [])

        for n2 in notes[i+1:]:
            if n1["id"] == n2["id"]:
                continue
            agents2 = set(n2["frontmatter"].get("agents", []))
            domain2 = set(n2["frontmatter"].get("domain", []) if isinstance(n2["frontmatter"].get("domain"), list) else [])

            # Se compartilham 2+ agentes E 1+ domínio
            common_agents = agents1 & agents2
            common_domain = domain1 & domain2

            if len(common_agents) >= 2 and len(common_domain) >= 1:
                # Evitar links redundantes (se já tem link mais específico)
                existing = [(l[0], l[1]) for l in link_plan]
                if (n1["id"], n2["id"]) not in existing and (n2["id"], n1["id"]) not in existing:
                    link_plan.append((n1["id"], n2["id"], "related"))

    # Deduplicate
    seen = set()
    unique_plan = []
    for src, tgt, lt in link_plan:
        key = (src, tgt, lt)
        if key not in seen and src != tgt:
            seen.add(key)
            unique_plan.append((src, tgt, lt))

    # Executar links
    print(f"\n🔗 Auto-Linker — {len(unique_plan)} links detectados\n")

    for src, tgt, link_type in unique_plan:
        # Verificar se link já existe
        src_note = notes_by_id.get(src)
        if src_note:
            existing_links = src_note["frontmatter"].get("links", [])
            already_exists = any(
                isinstance(l, dict) and l.get("target") == tgt and l.get("type") == link_type
                for l in existing_links
            )
            if already_exists:
                continue

        print(f"  {src} --[{link_type}]--> {tgt}")
        add_link(src, tgt, link_type)
        links_created += 1

    print(f"\n✅ {links_created} links criados")
    return links_created


if __name__ == "__main__":
    created = auto_link_strategy()
    if created > 0:
        print("\n🔄 Reconstruindo índices...")
        build_all_indexes()
