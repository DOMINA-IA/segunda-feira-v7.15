#!/usr/bin/env python3
"""Adiciona frontmatter CORTEX às rules migradas para on-demand."""

import yaml
from pathlib import Path
from datetime import datetime

RULES_DIR = Path.home() / "cortex/vault/rules"

# Mapeamento: rule → triggers (keywords que ativam a injeção)
RULE_CONFIG = {
    "workflow-execution.md": {
        "title": "Workflow Execution — SDC, QA Loop, Spec Pipeline",
        "triggers": ["story", "sdc", "workflow", "qa-loop", "spec", "brownfield", "*draft", "*develop", "*validate", "*execute-epic", "qa gate", "phase"],
        "agents": ["dev", "qa", "pm", "po", "sm", "architect", "sf-master"],
        "domain": ["dev"],
        "tags": ["sdc", "workflow", "qa-loop", "spec-pipeline", "brownfield"],
    },
    "story-lifecycle.md": {
        "title": "Story Lifecycle — Status, Validação, QA Gate",
        "triggers": ["story", "stories", "draft", "ready", "inprogress", "inreview", "done", "acceptance criteria", "qa gate", "validate", "*draft", "*validate-story"],
        "agents": ["dev", "qa", "po", "sm", "sf-master"],
        "domain": ["dev"],
        "tags": ["story", "lifecycle", "validation", "qa-gate"],
    },
    "coderabbit-integration.md": {
        "title": "CodeRabbit Integration — Self-Healing Config",
        "triggers": ["coderabbit", "code review", "self-healing", "lint", "severity", "critical", "review automático"],
        "agents": ["dev", "qa"],
        "domain": ["dev"],
        "tags": ["coderabbit", "code-review", "self-healing"],
    },
    "ids-principles.md": {
        "title": "IDS Principles — REUSE > ADAPT > CREATE",
        "triggers": ["ids", "reuse", "adapt", "create", "entity registry", "duplicate", "existing pattern", "reutilizar"],
        "agents": ["dev", "architect", "qa", "sf-master"],
        "domain": ["dev"],
        "tags": ["ids", "reuse", "patterns", "registry"],
    },
    "external-api-patterns.md": {
        "title": "External API Patterns — SYNC > CACHE > REAL-TIME",
        "triggers": ["api externa", "external api", "rate limit", "sync", "real-time", "dashboard", "asaas", "webhook", "api integration"],
        "agents": ["dev", "architect", "data-engineer"],
        "domain": ["dev"],
        "tags": ["api", "sync", "rate-limit", "integration"],
    },
    "model-routing.md": {
        "title": "Roteamento de Modelos — Opus/Sonnet/Haiku",
        "triggers": ["model routing", "roteamento", "opus", "sonnet", "haiku", "modelo", "custo token", "economia modelo"],
        "agents": ["sf-master"],
        "domain": ["meta"],
        "tags": ["model-routing", "opus", "sonnet", "haiku", "economia"],
    },
    "mcp-usage.md": {
        "title": "MCP Server Usage Rules",
        "triggers": ["mcp", "playwright", "docker", "exa", "context7", "apify", "mcp server", "docker-gateway"],
        "agents": ["dev", "devops"],
        "domain": ["dev"],
        "tags": ["mcp", "playwright", "docker", "tools"],
    },
    "token-economy.md": {
        "title": "Token Economy — 3 Tiers, Context Fork",
        "triggers": ["token economy", "economia token", "context fork", "custo", "tier", "token budget"],
        "agents": ["sf-master"],
        "domain": ["meta"],
        "tags": ["tokens", "economia", "context-fork", "budget"],
    },
    "creativity-protocol.md": {
        "title": "Protocolo de Criatividade Combinatória",
        "triggers": ["criatividade", "criativo", "campanha nova", "ângulo novo", "conteúdo novo", "lançamento", "analogia", "inversão", "creative"],
        "agents": ["content", "copywriter", "creative-director", "offer-engineer", "traffic"],
        "domain": ["content", "traffic"],
        "tags": ["criatividade", "protocolo", "analogia", "inversão"],
    },
    "initiative-protocol.md": {
        "title": "Protocolo de Iniciativa — Agentes Proativos",
        "triggers": ["proativo", "iniciativa", "autonomia", "proactive", "detectar", "oportunidade", "ação autônoma"],
        "agents": ["sf-master"],
        "domain": ["meta"],
        "tags": ["proativo", "iniciativa", "autonomia"],
    },
    "handoff-protocol.md": {
        "title": "Protocolo de Handoff — Passagem de Bastão",
        "triggers": ["handoff", "passagem", "bastão", "delegar", "próximo agente", "transferir"],
        "agents": ["sf-master"],
        "domain": ["meta"],
        "tags": ["handoff", "delegação", "passagem"],
    },
}

now = datetime.now().strftime("%Y-%m-%d")

for filename, config in RULE_CONFIG.items():
    filepath = RULES_DIR / filename
    if not filepath.exists():
        print(f"  ⚠️  {filename} não encontrado")
        continue

    content = filepath.read_text(encoding="utf-8")

    # Remover frontmatter existente se houver
    import re
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if fm_match:
        body = content[fm_match.end():]
    else:
        body = content

    # Criar frontmatter CORTEX
    fm = {
        "id": filename.replace(".md", ""),
        "title": config["title"],
        "type": "rule",
        "domain": config["domain"],
        "agents": config["agents"],
        "tags": config["tags"],
        "triggers": config["triggers"],
        "status": "active",
        "created": now,
        "last_verified": now,
        "decay_rate": 0.01,
        "on_demand": True,
        "links": [],
    }

    new_content = "---\n"
    new_content += yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    new_content += "---\n\n"
    new_content += body

    filepath.write_text(new_content, encoding="utf-8")
    print(f"  ✅ {filename} — {len(config['triggers'])} triggers configurados")

print(f"\n✅ 11 rules com frontmatter CORTEX")
