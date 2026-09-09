#!/usr/bin/env python3
"""
CORTEX Engine — O coração do sistema de conhecimento do Segunda-feira.

Responsável por:
- Parse de notas (frontmatter YAML + corpo markdown)
- Construção e manutenção de índices
- Busca por keywords, tags e domínio
- Cálculo de freshness (decay temporal)
- Geração de briefings por agente
- Health check do vault
"""

import os
import sys
import json
import yaml
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import math

# ─── Configuração ───────────────────────────────────────────────

CORTEX_HOME = Path.home() / "cortex"
VAULT_DIR = CORTEX_HOME / "vault"
INDEX_DIR = CORTEX_HOME / "index"
BRIEFINGS_DIR = CORTEX_HOME / "briefings"
TEMPLATES_DIR = CORTEX_HOME / "templates"

LINK_TYPES = [
    "depends_on", "extends", "supersedes", "contradicts",
    "instance_of", "learned_from", "related"
]

DEFAULT_DECAY_RATES = {
    "infra": 0.15,
    "project": 0.05,
    "pattern": 0.03,
    "playbook": 0.02,
    "rule": 0.01,
    "feedback": 0.08,
    "agent": 0.01,
    "meta": 0.01,
}

# ─── Parse de Notas ─────────────────────────────────────────────

def parse_note(filepath):
    """Extrai frontmatter YAML e corpo de uma nota CORTEX."""
    filepath = Path(filepath)
    if not filepath.exists():
        return None

    content = filepath.read_text(encoding="utf-8")

    # Extrair frontmatter entre ---
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
    if not fm_match:
        return {
            "id": filepath.stem,
            "path": str(filepath),
            "frontmatter": {},
            "body": content,
            "raw": content,
        }

    try:
        frontmatter = yaml.safe_load(fm_match.group(1)) or {}
    except yaml.YAMLError:
        frontmatter = {}

    body = fm_match.group(2).strip()

    # Garantir campos obrigatórios
    note_id = frontmatter.get("id", filepath.stem)

    return {
        "id": note_id,
        "path": str(filepath),
        "frontmatter": frontmatter,
        "body": body,
        "raw": content,
    }


def scan_vault():
    """Escaneia todas as notas .md no vault.

    Ignora:
    - symlinks (vistas por axis em _index_by_axis/ não devem duplicar)
    - diretórios meta de framework (_index_by_axis, _archive, .obsidian)
    """
    notes = []
    seen_inodes = set()
    IGNORE_DIRS = {'_index_by_axis', '_archive', '.obsidian', '.git', '.trash'}
    for md_file in VAULT_DIR.rglob("*.md"):
        # ignorar se em diretório protegido
        if any(part in IGNORE_DIRS for part in md_file.parts):
            continue
        # ignorar symlinks (já são apontamentos, não notas)
        if md_file.is_symlink():
            continue
        # dedup por inode (paranóia extra contra symlinks que escapem)
        try:
            inode = md_file.stat().st_ino
            if inode in seen_inodes:
                continue
            seen_inodes.add(inode)
        except OSError:
            continue
        note = parse_note(md_file)
        if note:
            notes.append(note)
    return notes


# ─── Freshness (Decay Temporal) ─────────────────────────────────

def calculate_freshness(note):
    """Calcula o score de freshness baseado no decay temporal.

    FÓRMULA CANÔNICA (ver cortex/vault/concepts/cortex-formula-canonica-freshness.md):
        freshness = exp(-decay_rate * weeks_elapsed)

    Onde:
      - decay_rate: por tipo (DEFAULT_DECAY_RATES) ou override em frontmatter
      - weeks_elapsed: (now - last_verified).days / 7.0
      - last_verified aceita "YYYY-MM-DD" ou ISO datetime completo

    Retorna None se nota não tem data válida (undated) — sinaliza para
    health_check separar em bucket próprio em vez de contaminar "aging".
    """
    fm = note["frontmatter"]

    # Data de referência: last_verified ou created
    ref_date_str = fm.get("last_verified") or fm.get("created")
    if not ref_date_str:
        return None  # Sem data — bucket "undated", não "aging"

    try:
        if isinstance(ref_date_str, datetime):
            ref_date = ref_date_str
        else:
            s = str(ref_date_str).strip()
            # Aceitar tanto "YYYY-MM-DD" quanto ISO completo "YYYY-MM-DDTHH:MM:SS..."
            try:
                ref_date = datetime.strptime(s, "%Y-%m-%d")
            except ValueError:
                # Tentar ISO; pegar só a parte da data (drop timezone)
                date_part = s.split("T")[0]
                ref_date = datetime.strptime(date_part, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None  # Data inválida — undated

    # Normalizar para naive datetime (drop tzinfo se houver)
    if ref_date.tzinfo is not None:
        ref_date = ref_date.replace(tzinfo=None)

    # Calcular semanas desde última verificação
    now = datetime.now()
    weeks_elapsed = (now - ref_date).days / 7.0

    # Taxa de decay baseada no tipo
    note_type = fm.get("type", "meta")
    status = fm.get("status", "active")

    decay_rate = fm.get("decay_rate")
    if decay_rate is None:
        decay_rate = DEFAULT_DECAY_RATES.get(note_type, 0.05)
        # Projetos pausados decaem mais rápido
        if note_type == "project" and status == "paused":
            decay_rate = 0.10

    # Freshness = e^(-decay * weeks) — decay exponencial (canônica)
    freshness = math.exp(-decay_rate * weeks_elapsed)
    return round(max(0.0, min(1.0, freshness)), 3)


# ─── Construção de Índices ──────────────────────────────────────

def build_graph(notes):
    """Constrói o grafo de relações entre notas."""
    graph = {"nodes": [], "edges": []}

    for note in notes:
        fm = note["frontmatter"]
        graph["nodes"].append({
            "id": note["id"],
            "title": fm.get("title", note["id"]),
            "type": fm.get("type", "unknown"),
            "domain": fm.get("domain", []),
            "status": fm.get("status", "active"),
        })

        for link in fm.get("links", []):
            if isinstance(link, dict):
                graph["edges"].append({
                    "source": note["id"],
                    "target": link.get("target", ""),
                    "type": link.get("type", "related"),
                })

    return graph


def build_tags_index(notes):
    """Constrói índice invertido de tags."""
    tags_index = defaultdict(list)

    for note in notes:
        fm = note["frontmatter"]
        tags = fm.get("tags", [])
        if isinstance(tags, list):
            for tag in tags:
                tags_index[tag].append({
                    "id": note["id"],
                    "title": fm.get("title", note["id"]),
                    "path": note["path"],
                })

    return dict(tags_index)


def build_agents_scope(notes):
    """Mapa de agente → notas relevantes."""
    scope = defaultdict(list)

    for note in notes:
        fm = note["frontmatter"]
        agents = fm.get("agents", [])
        if isinstance(agents, list):
            for agent in agents:
                agent_name = agent.replace("@", "")
                # Para scope, usar 0.5 quando undated (mantém compat com briefings)
                fresh_score = calculate_freshness(note)
                scope[agent_name].append({
                    "id": note["id"],
                    "title": fm.get("title", note["id"]),
                    "type": fm.get("type", "unknown"),
                    "freshness": fresh_score if fresh_score is not None else 0.5,
                    "undated": fresh_score is None,
                    "path": note["path"],
                })

        # Também indexar por domínio → agentes típicos
        domains = fm.get("domain", [])
        if isinstance(domains, str):
            domains = [domains]

    return dict(scope)


def build_freshness_index(notes):
    """Índice de freshness de cada nota."""
    freshness = {}

    for note in notes:
        fm = note["frontmatter"]
        score = calculate_freshness(note)
        alert_threshold = fm.get("alert_threshold", 0.5)
        undated = score is None

        freshness[note["id"]] = {
            "score": score if score is not None else None,  # explícito: None = undated
            "undated": undated,
            "last_verified": str(fm.get("last_verified", "")),
            "created": str(fm.get("created", "")),
            "decay_rate": fm.get("decay_rate", DEFAULT_DECAY_RATES.get(fm.get("type", "meta"), 0.05)),
            "alert_threshold": alert_threshold,
            "needs_review": (score is not None and score < alert_threshold),
            "stale": (score is not None and score < 0.2),
            "path": note["path"],
        }

    return freshness


def build_search_index(notes):
    """Índice para busca por keywords."""
    search = {}

    for note in notes:
        fm = note["frontmatter"]

        # Extrair keywords do título, tags, body
        keywords = set()

        title = fm.get("title", note["id"])
        keywords.update(title.lower().split())

        for tag in fm.get("tags", []):
            keywords.add(str(tag).lower())

        for domain in (fm.get("domain", []) if isinstance(fm.get("domain", []), list) else [fm.get("domain", "")]):
            keywords.add(str(domain).lower())

        # Primeiras 500 palavras do corpo
        body_words = note["body"].lower().split()[:500]
        keywords.update(body_words)

        # Remover stopwords básicas
        stopwords = {"o", "a", "de", "do", "da", "em", "e", "que", "para", "com", "um", "uma",
                      "os", "as", "dos", "das", "no", "na", "por", "se", "ao", "ou", "mas",
                      "the", "is", "in", "to", "of", "and", "for", "on", "with", "at", "by",
                      "-", "—", "#", "##", "###", "|", "", "```", "---"}
        keywords = {k for k in keywords if k not in stopwords and len(k) > 2}

        # Search-index: usar 0.5 para undated (BM25 boost neutro)
        fresh_score = calculate_freshness(note)
        search[note["id"]] = {
            "title": title,
            "type": fm.get("type", "unknown"),
            "tags": fm.get("tags", []),
            "domain": fm.get("domain", []),
            "keywords": list(keywords),
            "freshness": fresh_score if fresh_score is not None else 0.5,
            "undated": fresh_score is None,
            "path": note["path"],
        }

    return search


def build_all_indexes():
    """Reconstrói todos os índices do CORTEX."""
    notes = scan_vault()

    if not notes:
        print("⚠️  Vault vazio — nenhuma nota encontrada.")
        return

    graph = build_graph(notes)
    tags = build_tags_index(notes)
    agents_scope = build_agents_scope(notes)
    freshness = build_freshness_index(notes)
    search = build_search_index(notes)

    # Health
    health = compute_health(notes, freshness, graph)

    # Salvar índices
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    indexes = {
        "graph.json": graph,
        "tags.json": tags,
        "agents-scope.json": agents_scope,
        "freshness.json": freshness,
        "search-index.json": search,
        "health.json": health,
    }

    for filename, data in indexes.items():
        filepath = INDEX_DIR / filename
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    print(f"✅ Índices construídos — {len(notes)} notas indexadas")
    print(f"   📊 graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
    print(f"   🏷️  tags: {len(tags)} tags únicas")
    print(f"   👤 agents: {len(agents_scope)} agentes com escopo")
    print(f"   🕐 freshness: {sum(1 for v in freshness.values() if v['needs_review'])} precisam revisão")

    return indexes


# ─── Busca ──────────────────────────────────────────────────────

def query(search_term, max_results=10):
    """Busca BM25 — ranqueia por relevância × freshness com IDF."""
    search_index_path = INDEX_DIR / "search-index.json"
    if not search_index_path.exists():
        print("⚠️  Índice não existe. Execute build-index.sh primeiro.")
        return []

    search_index = json.loads(search_index_path.read_text(encoding="utf-8"))

    terms = search_term.lower().split()
    N = len(search_index)  # Total de documentos
    if N == 0:
        return []

    # BM25 parameters
    k1 = 1.5   # Term frequency saturation
    b = 0.75   # Length normalization

    # Calcular tamanho médio dos documentos (quantidade de keywords)
    doc_lengths = {nid: len(e.get("keywords", [])) for nid, e in search_index.items()}
    avgdl = sum(doc_lengths.values()) / N if N > 0 else 1

    # Pré-calcular IDF para cada termo da query
    idf = {}
    for term in terms:
        # Contar em quantos docs o termo aparece
        df = 0
        for entry in search_index.values():
            keywords = entry.get("keywords", [])
            title = entry.get("title", "").lower()
            tags = [str(t).lower() for t in entry.get("tags", [])]
            if term in title or term in tags or any(term in k for k in keywords):
                df += 1
        # IDF com smoothing: log((N - df + 0.5) / (df + 0.5) + 1)
        idf[term] = math.log((N - df + 0.5) / (df + 0.5) + 1)

    results = []

    for note_id, entry in search_index.items():
        keywords = entry.get("keywords", [])
        title = entry.get("title", "").lower()
        tags = [str(t).lower() for t in entry.get("tags", [])]
        dl = doc_lengths.get(note_id, 1)

        bm25_score = 0

        for term in terms:
            # Calcular term frequency (TF) com pesos por localização
            tf = 0
            if term in title:
                tf += 5  # Título vale 5x
            if term in tags:
                tf += 3  # Tags valem 3x
            # Keywords (body)
            tf += sum(1 for k in keywords if term in k)

            if tf > 0:
                # BM25 formula: IDF * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl/avgdl))
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * dl / avgdl)
                bm25_score += idf.get(term, 0) * (numerator / denominator)

        if bm25_score > 0:
            freshness = entry.get("freshness", 0.5)
            # Freshness boost: multiplica por (0.5 + 0.5 * freshness)
            final_score = bm25_score * (0.5 + 0.5 * freshness)

            results.append({
                "id": note_id,
                "title": entry.get("title", note_id),
                "type": entry.get("type", ""),
                "score": round(final_score, 2),
                "freshness": freshness,
                "tags": entry.get("tags", []),
                "path": entry.get("path", ""),
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:max_results]


def query_by_agent(agent_name):
    """Retorna todas as notas relevantes para um agente."""
    scope_path = INDEX_DIR / "agents-scope.json"
    if not scope_path.exists():
        return []

    scope = json.loads(scope_path.read_text(encoding="utf-8"))
    agent_name = agent_name.replace("@", "")
    return scope.get(agent_name, [])


def query_by_tag(tag):
    """Retorna todas as notas com uma tag específica."""
    tags_path = INDEX_DIR / "tags.json"
    if not tags_path.exists():
        return []

    tags = json.loads(tags_path.read_text(encoding="utf-8"))
    return tags.get(tag, [])


# ─── Health Check ───────────────────────────────────────────────

def compute_health(notes, freshness_index, graph):
    """Calcula métricas de saúde do vault."""
    total = len(notes)
    if total == 0:
        return {"total": 0, "status": "empty"}

    # Freshness categories (exclui undated — bucket próprio)
    def _has_score(v):
        return v.get("score") is not None and not v.get("undated", False)
    fresh = sum(1 for v in freshness_index.values() if _has_score(v) and v["score"] > 0.7)
    aging = sum(1 for v in freshness_index.values() if _has_score(v) and 0.3 <= v["score"] <= 0.7)
    stale = sum(1 for v in freshness_index.values() if _has_score(v) and v["score"] < 0.3)
    undated = sum(1 for v in freshness_index.values() if v.get("undated", False))
    needs_review = sum(1 for v in freshness_index.values() if v["needs_review"])

    # Orphans (notas sem links de ou para)
    linked_ids = set()
    for edge in graph["edges"]:
        linked_ids.add(edge["source"])
        linked_ids.add(edge["target"])
    node_ids = {n["id"] for n in graph["nodes"]}
    orphans = node_ids - linked_ids

    # Contradições
    contradictions = [e for e in graph["edges"] if e["type"] == "contradicts"]

    # Superseded (notas substituídas que ainda existem)
    superseded_targets = {e["target"] for e in graph["edges"] if e["type"] == "supersedes"}

    return {
        "total": total,
        "fresh": fresh,
        "aging": aging,
        "stale": stale,
        "undated": undated,
        "needs_review": needs_review,
        "orphans": list(orphans),
        "orphan_count": len(orphans),
        "contradictions": len(contradictions),
        "superseded": list(superseded_targets),
        "superseded_count": len(superseded_targets),
        # Health score: % de notas com score conhecido E fresh
        "health_score": round((fresh / (total - undated)) * 100, 1) if (total - undated) > 0 else 0,
        "timestamp": datetime.now().isoformat(),
        "stale_notes": [
            {"id": k, "score": v["score"], "path": v["path"]}
            for k, v in freshness_index.items() if v["stale"]
        ],
        "review_notes": [
            {"id": k, "score": v["score"], "path": v["path"]}
            for k, v in freshness_index.items() if v["needs_review"] and not v["stale"]
        ],
        "undated_notes": [
            {"id": k, "path": v["path"]}
            for k, v in freshness_index.items() if v.get("undated", False)
        ],
    }


def print_health():
    """Exibe relatório de saúde do vault."""
    health_path = INDEX_DIR / "health.json"
    if not health_path.exists():
        print("⚠️  Health não calculado. Execute build-index.sh primeiro.")
        return

    h = json.loads(health_path.read_text(encoding="utf-8"))

    print(f"""
📊 CORTEX Health Report
{'─' * 45}
Total de notas:     {h['total']}
Fresh (>0.7):       {h['fresh']} ✅
Aging (0.3-0.7):    {h['aging']} ⚠️
Stale (<0.3):       {h['stale']} 🔴
Undated (sem data): {h.get('undated', 0)} ❓
Orphans:            {h['orphan_count']} 👻
Contradições:       {h['contradictions']} ⚡
Superseded:         {h['superseded_count']} 📋
{'─' * 45}
Health Score:       {h['health_score']}% (excluindo undated)
{'─' * 45}""")

    if h.get("stale_notes"):
        print("\n🔴 Notas STALE (precisam atenção urgente):")
        for n in h["stale_notes"]:
            print(f"   - {n['id']} (freshness: {n['score']})")

    if h.get("review_notes"):
        print("\n⚠️  Notas para REVISÃO:")
        for n in h["review_notes"]:
            print(f"   - {n['id']} (freshness: {n['score']})")

    if h.get("orphans"):
        print("\n👻 Notas ORPHAN (sem links):")
        for o in h["orphans"]:
            print(f"   - {o}")

    print()


# ─── Briefings ──────────────────────────────────────────────────

def build_briefing(agent_name):
    """Gera briefing compacto para um agente."""
    notes = query_by_agent(agent_name)
    if not notes:
        return f"# Briefing @{agent_name}\n\nNenhuma nota atribuída a este agente.\n"

    # Agrupar por tipo
    by_type = defaultdict(list)
    for note_info in notes:
        by_type[note_info.get("type", "other")].append(note_info)

    lines = [f"# Briefing @{agent_name}", ""]
    lines.append(f"> Gerado: {datetime.now().strftime('%Y-%m-%d %H:%M')} | {len(notes)} notas relevantes")
    lines.append("")

    type_labels = {
        "project": "📁 Projetos",
        "infra": "🔧 Infraestrutura",
        "pattern": "🎯 Padrões",
        "playbook": "📚 Playbooks",
        "feedback": "📊 Feedback",
        "rule": "📜 Regras",
        "agent": "🤖 Agentes",
    }

    for note_type, type_notes in by_type.items():
        label = type_labels.get(note_type, f"📄 {note_type.title()}")
        lines.append(f"## {label}")
        lines.append("")

        for n in sorted(type_notes, key=lambda x: x.get("freshness", 0), reverse=True):
            freshness = n.get("freshness", 0)
            indicator = "✅" if freshness > 0.7 else "⚠️" if freshness > 0.3 else "🔴"

            # Ler nota completa para extrair resumo
            note_path = Path(n.get("path", ""))
            summary = ""
            if note_path.exists():
                full_note = parse_note(note_path)
                if full_note:
                    # Pegar primeiras 3 linhas não-vazias do body
                    body_lines = [l for l in full_note["body"].split("\n") if l.strip() and not l.startswith("#")]
                    summary = " ".join(body_lines[:3])[:200]

            lines.append(f"- {indicator} **{n.get('title', n['id'])}** (freshness: {freshness})")
            if summary:
                lines.append(f"  {summary}")
            lines.append("")

    return "\n".join(lines)


def build_all_briefings():
    """Gera briefings para todos os agentes com escopo definido."""
    scope_path = INDEX_DIR / "agents-scope.json"
    if not scope_path.exists():
        print("⚠️  Índice de agentes não existe. Execute build-index.sh primeiro.")
        return

    scope = json.loads(scope_path.read_text(encoding="utf-8"))
    BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)
    (BRIEFINGS_DIR / "meta").mkdir(exist_ok=True)
    (BRIEFINGS_DIR / "ops").mkdir(exist_ok=True)

    valid_name_re = re.compile(r"^[a-z][a-z0-9-]*$")

    META_AGENTS = {
        'sf-master', 'people-ops', 'mestre-do-conselho', 'workflow-orchestrator',
        'advogado-do-diabo', 'security-auditor', 'fabio-soares',
        'prompt-engineer', 'vibe-coder', 'rag-architect', 'automation-architect',
        'knowledge-builder', 'cost-optimizer', 'swarm-simulator',
        'tool-curator', 'inema-scout', 'dev',
        'architect', 'pm', 'po', 'sm', 'qa', 'devops', 'data-engineer',
        'assistant', 'fin-assist', 'autonomous', 'cost-watchdog', 'claude', 'all',
    }
    OPS_AGENTS = {
        'traffic', 'content', 'copywriter', 'creative-director', 'video-producer',
        'offer-engineer', 'launch-strategist', 'challenge-funnel',
        'market-intel', 'cro-specialist', 'growth-hacker', 'cold-outreach',
        'whatsapp-specialist', 'voice-ai-specialist',
        'analyst', 'contract-analyst',
        'closer', 'cs-retention', 'cs', 'fin-plat', 'cfo', 'commercial', 'mentor',
        'ops', 'ops-monitor', 'sales', 'sdr', 'ux-design-expert', 'product',
        'collector', 'events', 'chief', 'advisory-board', 'squad-creator',
    }

    def axis_of(agent):
        if agent in META_AGENTS: return "meta"
        if agent in OPS_AGENTS: return "ops"
        return "meta"  # default conservador

    count = 0
    skipped = 0
    for agent_name in scope:
        if not valid_name_re.match(agent_name):
            print(f"⚠️  Skipping invalid agent name: {agent_name!r}")
            skipped += 1
            continue
        axis = axis_of(agent_name)
        target_dir = BRIEFINGS_DIR / axis
        filepath = target_dir / f"{agent_name}.md"

        # Preservar Auto-Updates do briefing antigo (nova OU legacy localização)
        auto_updates_section = ""
        legacy_path = BRIEFINGS_DIR / f"{agent_name}.md"
        for existing in (filepath, legacy_path):
            if existing.exists() and existing.is_file():
                existing_content = existing.read_text(encoding="utf-8")
                if "## Auto-Updates" in existing_content:
                    idx = existing_content.find("## Auto-Updates")
                    auto_updates_section = "\n" + existing_content[idx:]
                    break

        briefing = build_briefing(agent_name)
        if auto_updates_section:
            briefing = briefing.rstrip() + "\n" + auto_updates_section
        filepath.write_text(briefing, encoding="utf-8")

        # Remover briefing legacy se ainda existe na raiz
        if legacy_path.exists() and legacy_path != filepath and not legacy_path.is_symlink():
            legacy_path.unlink()

        count += 1

    print(f"✅ {count} briefings gerados em {BRIEFINGS_DIR}/{{meta,ops}}/")
    if skipped:
        print(f"⚠️  {skipped} agent_name(s) ignorados por nome inválido")


# ─── Ingest (Criar Nota) ───────────────────────────────────────

def create_note(title, note_type, domain=None, agents=None, tags=None, body="", links=None, status="active"):
    """Cria uma nova nota CORTEX."""
    # Gerar ID a partir do título
    note_id = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

    # Determinar pasta
    type_to_dir = {
        "project": "projects",
        "infra": "infra",
        "pattern": "patterns",
        "playbook": "playbooks",
        "feedback": "feedback",
        "rule": "rules",
        "agent": "agents",
        "meta": "meta",
    }
    subdir = type_to_dir.get(note_type, "meta")
    filepath = VAULT_DIR / subdir / f"{note_id}.md"

    # Construir frontmatter
    fm = {
        "id": note_id,
        "title": title,
        "type": note_type,
        "status": status,
        "created": datetime.now().strftime("%Y-%m-%d"),
        "last_verified": datetime.now().strftime("%Y-%m-%d"),
    }

    if domain:
        fm["domain"] = domain if isinstance(domain, list) else [domain]
    if agents:
        fm["agents"] = agents if isinstance(agents, list) else [agents]
    if tags:
        fm["tags"] = tags if isinstance(tags, list) else [tags]
    if links:
        fm["links"] = links

    decay = DEFAULT_DECAY_RATES.get(note_type, 0.05)
    fm["decay_rate"] = decay

    # Construir arquivo
    content = "---\n"
    content += yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    content += "---\n\n"
    content += f"# {title}\n\n"
    content += body if body else ""

    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")

    print(f"✅ Nota criada: {filepath}")
    print(f"   ID: {note_id} | Tipo: {note_type} | Decay: {decay}/semana")

    return note_id


# ─── Link ───────────────────────────────────────────────────────

def add_link(source_id, target_id, link_type="related"):
    """Adiciona um link tipado entre duas notas."""
    if link_type not in LINK_TYPES:
        print(f"❌ Tipo de link inválido: {link_type}")
        print(f"   Tipos válidos: {', '.join(LINK_TYPES)}")
        return False

    # Encontrar nota source
    notes = scan_vault()
    source_note = None
    for note in notes:
        if note["id"] == source_id:
            source_note = note
            break

    if not source_note:
        print(f"❌ Nota não encontrada: {source_id}")
        return False

    # Ler arquivo original
    filepath = Path(source_note["path"])
    content = filepath.read_text(encoding="utf-8")

    fm = source_note["frontmatter"]
    links = fm.get("links", [])
    links.append({"target": target_id, "type": link_type})
    fm["links"] = links

    # Reconstruir arquivo
    body = source_note["body"]
    new_content = "---\n"
    new_content += yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    new_content += "---\n\n"
    new_content += body

    filepath.write_text(new_content, encoding="utf-8")
    print(f"✅ Link criado: {source_id} --[{link_type}]--> {target_id}")
    return True


# ─── Refresh ────────────────────────────────────────────────────

def refresh_note(note_id):
    """Marca uma nota como verificada (reseta freshness)."""
    notes = scan_vault()
    target = None
    for note in notes:
        if note["id"] == note_id:
            target = note
            break

    if not target:
        print(f"❌ Nota não encontrada: {note_id}")
        return False

    filepath = Path(target["path"])
    fm = target["frontmatter"]
    fm["last_verified"] = datetime.now().strftime("%Y-%m-%d")

    new_content = "---\n"
    new_content += yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    new_content += "---\n\n"
    new_content += target["body"]

    filepath.write_text(new_content, encoding="utf-8")
    print(f"✅ Nota verificada: {note_id} (freshness resetado)")
    return True


# ─── CLI ────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("""
CORTEX Engine — CLI

Uso:
  cortex_engine.py build-index           Reconstrói todos os índices
  cortex_engine.py build-briefings       Gera briefings por agente
  cortex_engine.py query "termo"         Busca por termo
  cortex_engine.py query-agent nome      Notas relevantes para agente
  cortex_engine.py query-tag tag         Notas com tag específica
  cortex_engine.py health                Relatório de saúde
  cortex_engine.py ingest                Criar nota (interativo)
  cortex_engine.py link src tgt tipo     Criar link entre notas
  cortex_engine.py refresh note_id       Marcar nota como verificada
  cortex_engine.py stats                 Estatísticas rápidas
        """)
        return

    cmd = sys.argv[1]

    if cmd == "build-index":
        build_all_indexes()

    elif cmd == "build-briefings":
        build_all_briefings()

    elif cmd == "query":
        if len(sys.argv) < 3:
            print("Uso: cortex_engine.py query \"termo de busca\"")
            return
        term = " ".join(sys.argv[2:])
        results = query(term)
        if not results:
            print(f"Nenhum resultado para: {term}")
            return
        print(f"\n🔍 Resultados para \"{term}\" ({len(results)} encontrados):\n")
        for r in results:
            f_indicator = "✅" if r["freshness"] > 0.7 else "⚠️" if r["freshness"] > 0.3 else "🔴"
            print(f"  {f_indicator} [{r['score']}] {r['title']} ({r['type']}) — freshness: {r['freshness']}")
            print(f"     📁 {r['path']}")
            if r["tags"]:
                print(f"     🏷️  {', '.join(str(t) for t in r['tags'])}")
            print()

    elif cmd == "query-agent":
        if len(sys.argv) < 3:
            print("Uso: cortex_engine.py query-agent nome")
            return
        agent = sys.argv[2]
        results = query_by_agent(agent)
        if not results:
            print(f"Nenhuma nota para @{agent}")
            return
        print(f"\n👤 Notas de @{agent} ({len(results)}):\n")
        for r in results:
            f_indicator = "✅" if r.get("freshness", 0) > 0.7 else "⚠️" if r.get("freshness", 0) > 0.3 else "🔴"
            print(f"  {f_indicator} {r.get('title', r['id'])} ({r.get('type', '?')}) — freshness: {r.get('freshness', '?')}")
        print()

    elif cmd == "query-tag":
        if len(sys.argv) < 3:
            print("Uso: cortex_engine.py query-tag tag")
            return
        tag = sys.argv[2]
        results = query_by_tag(tag)
        if not results:
            print(f"Nenhuma nota com tag: {tag}")
            return
        print(f"\n🏷️  Notas com tag \"{tag}\" ({len(results)}):\n")
        for r in results:
            print(f"  - {r.get('title', r['id'])}")
        print()

    elif cmd == "health":
        print_health()

    elif cmd == "ingest":
        # Parse argumentos
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--title", required=True)
        parser.add_argument("--type", required=True, choices=list(DEFAULT_DECAY_RATES.keys()))
        parser.add_argument("--domain", nargs="*", default=[])
        parser.add_argument("--agents", nargs="*", default=[])
        parser.add_argument("--tags", nargs="*", default=[])
        parser.add_argument("--body", default="")
        parser.add_argument("--status", default="active")
        args = parser.parse_args(sys.argv[2:])
        create_note(args.title, args.type, args.domain, args.agents, args.tags, args.body, status=args.status)

    elif cmd == "link":
        if len(sys.argv) < 5:
            print(f"Uso: cortex_engine.py link source_id target_id tipo")
            print(f"Tipos: {', '.join(LINK_TYPES)}")
            return
        add_link(sys.argv[2], sys.argv[3], sys.argv[4])

    elif cmd == "refresh":
        if len(sys.argv) < 3:
            print("Uso: cortex_engine.py refresh note_id")
            return
        refresh_note(sys.argv[2])

    elif cmd == "stats":
        notes = scan_vault()
        print(f"\n📊 CORTEX Stats")
        print(f"{'─' * 35}")
        print(f"Total de notas: {len(notes)}")
        types = defaultdict(int)
        for n in notes:
            types[n["frontmatter"].get("type", "unknown")] += 1
        for t, c in sorted(types.items()):
            print(f"  {t}: {c}")
        print()

    else:
        print(f"❌ Comando desconhecido: {cmd}")
        print("Execute sem argumentos para ver o help.")


if __name__ == "__main__":
    main()
