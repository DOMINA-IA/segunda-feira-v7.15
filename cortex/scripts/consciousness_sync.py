#!/usr/bin/env python3
"""
Consciousness → CORTEX Sync Engine

Lê heurísticas e fatos do Consciousness Engine e:
1. Cria/atualiza notas pattern no CORTEX vault
2. Cria links learned_from entre episódios e padrões
3. Atualiza notas existentes com fatos consolidados

Roda após consolidação noturna ou sob demanda.
"""

import json
import yaml
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

CORTEX_HOME = Path.home() / "cortex"
VAULT_DIR = CORTEX_HOME / "vault"
CONSCIOUSNESS_HOME = Path.home() / "consciousness"

# Fontes de dados do Consciousness Engine
HEURISTICS_FILE = CONSCIOUSNESS_HOME / "memory" / "procedural" / "heuristics.jsonl"
KNOWLEDGE_GRAPH = CONSCIOUSNESS_HOME / "memory" / "semantic" / "knowledge-graph.json"
EPISODIC_DIR = CONSCIOUSNESS_HOME / "memory" / "episodic"


def load_heuristics():
    """Carrega heurísticas do Consciousness Engine."""
    heuristics = []
    if not HEURISTICS_FILE.exists():
        return heuristics

    for line in HEURISTICS_FILE.read_text(encoding="utf-8").strip().split("\n"):
        if not line.strip():
            continue
        try:
            h = json.loads(line)
            heuristics.append(h)
        except json.JSONDecodeError:
            continue

    return heuristics


def load_knowledge_graph():
    """Carrega fatos consolidados do knowledge graph."""
    if not KNOWLEDGE_GRAPH.exists():
        return {"facts": [], "entities": []}

    try:
        return json.loads(KNOWLEDGE_GRAPH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, KeyError):
        return {"facts": [], "entities": []}


def load_recent_episodes(days=7):
    """Carrega episódios recentes por agente."""
    episodes = []
    if not EPISODIC_DIR.exists():
        return episodes

    cutoff = datetime.now().timestamp() - (days * 86400)

    for agent_file in EPISODIC_DIR.glob("*.jsonl"):
        agent_name = agent_file.stem
        for line in agent_file.read_text(encoding="utf-8").strip().split("\n"):
            if not line.strip():
                continue
            try:
                ep = json.loads(line)
                ep["_agent"] = agent_name
                # Verificar se é recente
                ts = ep.get("timestamp", "")
                if ts:
                    try:
                        ep_time = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                        if ep_time > cutoff:
                            episodes.append(ep)
                    except (ValueError, TypeError):
                        episodes.append(ep)  # Se não conseguir parsear data, incluir
                else:
                    episodes.append(ep)
            except json.JSONDecodeError:
                continue

    return episodes


def heuristic_to_note(heuristic):
    """Converte uma heurística em nota CORTEX."""
    # Extrair dados
    agent = heuristic.get("agent", "unknown").replace("@", "")
    rule = heuristic.get("rule", heuristic.get("heuristic", ""))
    context = heuristic.get("context", "")
    source_episodes = heuristic.get("source_episodes", [])
    created = heuristic.get("created", datetime.now().strftime("%Y-%m-%d"))

    if not rule:
        return None

    # Gerar ID
    slug = re.sub(r'[^a-z0-9]+', '-', rule[:60].lower()).strip('-')
    note_id = f"heuristic-{agent}-{slug}"

    # Construir frontmatter
    fm = {
        "id": note_id,
        "title": f"Heurística @{agent}: {rule[:80]}",
        "type": "pattern",
        "domain": ["meta"],
        "agents": [agent],
        "tags": ["heurística", "consciousness", agent],
        "status": "active",
        "created": str(created),
        "last_verified": datetime.now().strftime("%Y-%m-%d"),
        "decay_rate": 0.03,
        "links": [],
        "source": "consciousness-engine",
    }

    # Body
    body = f"# Heurística @{agent}\n\n"
    body += f"> {rule}\n\n"
    if context:
        body += f"**Contexto:** {context}\n\n"
    if source_episodes:
        body += "**Extraída de:** " + ", ".join(str(e) for e in source_episodes[:5]) + "\n"

    return note_id, fm, body


def fact_to_update(fact):
    """Tenta mapear um fato consolidado para uma nota existente."""
    subject = fact.get("subject", "")
    predicate = fact.get("predicate", "")
    obj = fact.get("object", "")

    if not subject or not predicate:
        return None

    return {
        "subject": subject,
        "predicate": predicate,
        "object": obj,
        "confidence": fact.get("confidence", 0.5),
    }


def sync():
    """Executa o sync completo."""
    print("🧠 Consciousness → CORTEX Sync")
    print("")

    # 1. Heurísticas → notas pattern
    heuristics = load_heuristics()
    print(f"  Heurísticas encontradas: {len(heuristics)}")

    created = 0
    for h in heuristics:
        result = heuristic_to_note(h)
        if not result:
            continue

        note_id, fm, body = result
        filepath = VAULT_DIR / "patterns" / f"{note_id}.md"

        # Não sobrescrever se já existe
        if filepath.exists():
            continue

        content = "---\n"
        content += yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
        content += "---\n\n"
        content += body

        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")
        created += 1
        print(f"    ✅ Criada: {note_id}")

    print(f"  Notas criadas de heurísticas: {created}")

    # 2. Knowledge graph → verificar fatos
    kg = load_knowledge_graph()
    facts = kg.get("facts", [])
    print(f"  Fatos no knowledge graph: {len(facts)}")

    if facts:
        # Salvar resumo de fatos como nota meta
        facts_note = VAULT_DIR / "meta" / "consciousness-facts.md"
        fm = {
            "id": "consciousness-facts",
            "title": "Fatos Consolidados — Consciousness Engine",
            "type": "meta",
            "domain": ["meta"],
            "agents": ["sf-master"],
            "tags": ["consciousness", "fatos", "knowledge-graph"],
            "status": "active",
            "created": datetime.now().strftime("%Y-%m-%d"),
            "last_verified": datetime.now().strftime("%Y-%m-%d"),
            "decay_rate": 0.05,
            "links": [],
            "source": "consciousness-engine",
        }

        body = "# Fatos Consolidados — Consciousness Engine\n\n"
        body += f"> Última sincronização: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

        for fact in facts[:50]:  # Max 50 fatos
            mapped = fact_to_update(fact)
            if mapped:
                conf = mapped["confidence"]
                indicator = "✅" if conf > 0.7 else "⚠️" if conf > 0.4 else "❓"
                body += f"- {indicator} **{mapped['subject']}** {mapped['predicate']} {mapped['object']} [confidence: {conf}]\n"

        content = "---\n"
        content += yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
        content += "---\n\n"
        content += body

        facts_note.write_text(content, encoding="utf-8")
        print(f"  ✅ Nota de fatos atualizada: consciousness-facts.md")

    # 3. Episódios recentes → estatísticas
    episodes = load_recent_episodes(days=7)
    print(f"  Episódios recentes (7 dias): {len(episodes)}")

    if episodes:
        # Agrupar por agente
        by_agent = defaultdict(list)
        for ep in episodes:
            by_agent[ep.get("_agent", "unknown")].append(ep)

        # Contar resultados
        success = sum(1 for ep in episodes if ep.get("result") == "success")
        failure = sum(1 for ep in episodes if ep.get("result") == "failure")
        total = len(episodes)

        print(f"  Resumo: {success} sucesso, {failure} falha, {total - success - failure} outros")
        for agent, eps in sorted(by_agent.items()):
            print(f"    @{agent}: {len(eps)} episódios")

    # 4. Rebuild índices
    print("\n🔄 Reconstruindo índices CORTEX...")
    import subprocess
    subprocess.run(
        ["python3", str(CORTEX_HOME / "scripts" / "cortex_engine.py"), "build-index"],
        capture_output=True
    )
    print("✅ Sync completo")


if __name__ == "__main__":
    sync()
