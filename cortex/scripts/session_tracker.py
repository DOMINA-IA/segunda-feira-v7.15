#!/usr/bin/env python3
"""
CORTEX Session Tracker — Memória inter-sessão.

Dois modos:
1. SAVE (hook Stop): analisa transcript e salva resumo da sessão
2. LOAD (hook UserPromptSubmit): injeta contexto da última sessão

Arquivos:
- ~/cortex/sessions/YYYY-MM-DD_HH-MM.json — log de cada sessão
- ~/cortex/sessions/latest.json — ponteiro para última sessão
"""

import sys
import json
import re
import os
from pathlib import Path
from datetime import datetime

SESSIONS_DIR = Path.home() / "cortex" / "sessions"
LATEST_FILE = SESSIONS_DIR / "latest.json"
WIP_FILE = Path.home() / "cortex" / "wip" / "active.json"

SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

# Lista de agentes válidos para filtrar @<word> capturado pelo regex.
# Sem isso, emails como @${REDIGIDO} ou @gmail.com viram "agentes" no Predict.
VALID_AGENTS = {
    # META
    'sf-master', 'people-ops', 'mestre-do-conselho', 'workflow-orchestrator',
    'advogado-do-diabo', 'security-auditor', 'fabio-soares',
    'prompt-engineer', 'vibe-coder', 'rag-architect', 'automation-architect',
    'knowledge-builder', 'cost-optimizer', 'swarm-simulator',
    'tool-curator', 'inema-scout', 'dev',
    'architect', 'pm', 'po', 'sm', 'qa', 'devops', 'data-engineer',
    'assistant', 'fin-assist', 'autonomous', 'cost-watchdog', 'claude',
    # OPS
    'traffic', 'content', 'copywriter', 'creative-director', 'video-producer',
    'offer-engineer', 'launch-strategist', 'challenge-funnel',
    'market-intel', 'cro-specialist', 'growth-hacker', 'cold-outreach',
    'whatsapp-specialist', 'voice-ai-specialist',
    'analyst', 'contract-analyst',
    'closer', 'cs-retention', 'cs', 'fin-plat', 'cfo', 'commercial', 'mentor',
    'ops', 'ops-monitor', 'sales', 'sdr', 'ux-design-expert', 'product',
    'collector', 'events', 'chief', 'advisory-board', 'squad-creator',
}


def save_session(transcript: str):
    """Analisa transcript e salva resumo estruturado da sessão."""
    if len(transcript) < 200:
        return  # Sessão muito curta, não vale salvar

    now = datetime.now()
    session_id = now.strftime("%Y-%m-%d_%H-%M")

    # Detectar agentes usados — filtrar contra VALID_AGENTS para evitar
    # capturar emails (@${REDIGIDO}), handles externos (@gmail.com)
    # e termos coloquiais. Antes esse regex sujou o CORTEX Predict com falsos.
    raw_at_mentions = set(re.findall(r'@([\w-]+)', transcript.lower()))
    agents_found = sorted(raw_at_mentions & VALID_AGENTS)

    # Detectar ações realizadas (heurísticas simples)
    actions = []
    action_patterns = [
        (r'(?:criou|criado|criada|criamos|criei)\s+(.{10,60})', "criou"),
        (r'(?:deploy|deployed|publicou|publicado)\s*(?:em|no|na)?\s*(.{5,40})', "deploy"),
        (r'(?:corrigiu|corrigido|fix|fixed|resolvido|resolveu)\s+(.{10,60})', "fix"),
        (r'(?:pausou|pausado|pausada)\s+(.{10,40})', "pausou"),
        (r'(?:ativou|ativado|ativada|lançou)\s+(.{10,40})', "ativou"),
        (r'(?:atualizou|atualizado|atualizada)\s+(.{10,60})', "atualizou"),
        (r'(?:configurou|configurado|configurada)\s+(.{10,60})', "configurou"),
        (r'(?:instalou|instalado)\s+(.{10,40})', "instalou"),
        (r'(?:migrou|migrado|migração)\s+(.{10,60})', "migrou"),
        (r'(?:otimizou|otimizado|otimizada)\s+(.{10,60})', "otimizou"),
    ]

    transcript_lower = transcript.lower()

    # NOTE 2026-05-22: extração heurística de ações/pendências/decisões DESLIGADA.
    # Regex `(?:precisa|pendente|criou|deploy)\s+(.{10,80})` capturava substrings
    # arbitrárias do meio de copywriting, citações e discussões — populando
    # CORTEX Session/WIP com lixo textual ("fazer sem fazer", "permission_modedefaulteffort").
    # Reabilitar apenas quando substituído por extrator estruturado:
    #   (a) listas markdown `- [ ] ...` explícitas, OU
    #   (b) integração com TaskList do Claude Code (tarefas reais).
    pending = []
    decisions = []

    # Detectar projetos mencionados
    projects_mentioned = []
    project_keywords = ["clienteexemplo", "kit empresário", "ai first", "desafio", "CLIENTE_EXEMPLO", "dominantes",
                        "CLIENTE_EXEMPLO", "segunda-feira", "cortex", "evento", "CLIENTE_EXEMPLO", "CLIENTE_EXEMPLO"]
    for kw in project_keywords:
        if kw in transcript_lower:
            projects_mentioned.append(kw)

    # Estimar duração (heurística: ~200 palavras/minuto de conversa)
    word_count = len(transcript.split())
    estimated_minutes = max(5, word_count // 200)

    session = {
        "session_id": session_id,
        "timestamp": now.isoformat(),
        "estimated_duration_min": estimated_minutes,
        "agents_used": agents_found[:10],
        "projects_touched": projects_mentioned[:5],
        "actions_performed": actions[:8],
        "decisions_made": decisions[:5],
        "left_pending": pending[:5],
        "word_count": word_count,
    }

    # Salvar sessão
    session_file = SESSIONS_DIR / f"{session_id}.json"
    session_file.write_text(json.dumps(session, indent=2, ensure_ascii=False), encoding="utf-8")

    # Atualizar ponteiro latest
    LATEST_FILE.write_text(json.dumps(session, indent=2, ensure_ascii=False), encoding="utf-8")

    # Atualizar WIP com itens pendentes
    if pending:
        update_wip(pending, session_id, projects_mentioned)

    return session


def update_wip(pending_items, session_id, projects):
    """Adiciona itens pendentes ao WIP tracker."""
    WIP_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        wip = json.loads(WIP_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        wip = {"items": [], "last_updated": ""}

    for item in pending_items:
        wip["items"].append({
            "description": item,
            "from_session": session_id,
            "projects": projects,
            "created": datetime.now().isoformat(),
            "status": "pending",
        })

    # Manter apenas os últimos 20 itens pendentes
    wip["items"] = [i for i in wip["items"] if i.get("status") == "pending"][-20:]
    wip["last_updated"] = datetime.now().isoformat()

    WIP_FILE.write_text(json.dumps(wip, indent=2, ensure_ascii=False), encoding="utf-8")


def load_session_context():
    """Retorna contexto da última sessão para injeção."""
    if not LATEST_FILE.exists():
        return ""

    try:
        session = json.loads(LATEST_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return ""

    # Calcular quanto tempo atrás foi
    try:
        session_time = datetime.fromisoformat(session["timestamp"])
        delta = datetime.now() - session_time
        hours_ago = delta.total_seconds() / 3600

        if hours_ago > 168:  # Mais de 1 semana
            return ""  # Muito antiga, não relevante
        elif hours_ago > 24:
            time_label = f"{int(hours_ago / 24)} dias atrás"
        elif hours_ago > 1:
            time_label = f"{int(hours_ago)}h atrás"
        else:
            time_label = f"{int(hours_ago * 60)}min atrás"
    except (ValueError, KeyError):
        time_label = "recentemente"

    lines = [f"[CORTEX Session — última sessão: {time_label}]"]

    agents = session.get("agents_used", [])
    if agents:
        lines.append(f"  Agentes: {', '.join('@' + a for a in agents[:5])}")

    projects = session.get("projects_touched", [])
    if projects:
        lines.append(f"  Projetos: {', '.join(projects[:5])}")

    actions = session.get("actions_performed", [])
    if actions:
        lines.append(f"  Feito: {'; '.join(actions[:4])}")

    pending = session.get("left_pending", [])
    if pending:
        lines.append(f"  Pendente: {'; '.join(pending[:3])}")

    decisions = session.get("decisions_made", [])
    if decisions:
        lines.append(f"  Decisões: {'; '.join(decisions[:3])}")

    return "\n".join(lines)


def load_wip_context():
    """Retorna itens WIP para injeção."""
    if not WIP_FILE.exists():
        return ""

    try:
        wip = json.loads(WIP_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return ""

    items = [i for i in wip.get("items", []) if i.get("status") == "pending"]
    if not items:
        return ""

    lines = [f"[CORTEX WIP — {len(items)} itens pendentes]"]
    for item in items[:5]:
        lines.append(f"  - {item['description']}")

    return "\n".join(lines)


# CLI
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: session_tracker.py save|load|wip|list")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "save":
        transcript = sys.stdin.read()
        session = save_session(transcript)
        if session:
            print(f"Sessão salva: {session['session_id']} ({len(session['actions_performed'])} ações, {len(session['left_pending'])} pendentes)")

    elif cmd == "load":
        ctx = load_session_context()
        if ctx:
            print(ctx)

    elif cmd == "wip":
        ctx = load_wip_context()
        if ctx:
            print(ctx)

    elif cmd == "list":
        sessions = sorted(SESSIONS_DIR.glob("*.json"))
        sessions = [s for s in sessions if s.name != "latest.json"]
        for s in sessions[-10:]:
            data = json.loads(s.read_text())
            print(f"  {data.get('session_id', s.stem)} — {len(data.get('actions_performed', []))} ações, {len(data.get('left_pending', []))} pendentes")
