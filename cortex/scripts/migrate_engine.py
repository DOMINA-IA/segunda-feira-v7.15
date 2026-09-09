#!/usr/bin/env python3
"""
CORTEX Migration Engine — Converte memórias existentes para formato CORTEX.

Lê arquivos de ~/.claude/projects/-HOME-/memory/
e converte para ~/cortex/vault/ com frontmatter CORTEX completo.
"""

import os
import re
import yaml
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path.home() / ".claude/projects/-HOME-/memory"
VAULT_DIR = Path.home() / "cortex/vault"

# Mapeamento de tipo de memória → tipo CORTEX + pasta
TYPE_MAP = {
    "user": ("meta", "meta"),
    "feedback": ("feedback", "feedback"),
    "project": ("project", "projects"),
    "reference": ("meta", "meta"),
}

# Mapeamento inteligente: nome do arquivo → domínio + agentes + tags
DOMAIN_HINTS = {
    "meta-ads": {"domain": ["traffic"], "agents": ["traffic"], "tags": ["meta-ads", "campanhas"]},
    "trafego": {"domain": ["traffic"], "agents": ["traffic"], "tags": ["tráfego", "sobral"]},
    "instagram": {"domain": ["content"], "agents": ["content"], "tags": ["instagram", "posts"]},
    "CLIENTE_EXEMPLO": {"domain": ["content", "dev"], "agents": ["content", "dev"], "tags": ["CLIENTE_EXEMPLO", "plataforma"]},
    "criativos": {"domain": ["traffic", "content"], "agents": ["traffic", "content", "creative-director"], "tags": ["criativos", "ads"]},
    "whatsapp": {"domain": ["dev"], "agents": ["dev", "whatsapp-specialist"], "tags": ["whatsapp", "bot"]},
    "voice": {"domain": ["dev"], "agents": ["dev", "voice-ai-specialist"], "tags": ["voice", "tts"]},
    "video": {"domain": ["content"], "agents": ["content", "video-producer"], "tags": ["vídeo", "pipeline"]},
    "clienteexemplo": {"domain": ["traffic", "dev"], "agents": ["traffic", "dev"], "tags": ["clienteexemplo", "CLIENTE_EXEMPLO"]},
    "deploy": {"domain": ["dev", "devops"], "agents": ["dev", "devops"], "tags": ["deploy", "hostinger"]},
    "infra": {"domain": ["dev", "devops"], "agents": ["dev", "devops"], "tags": ["infra", "vps"]},
    "hostinger": {"domain": ["dev", "devops"], "agents": ["dev", "devops"], "tags": ["hostinger", "deploy"]},
    "eduzz": {"domain": ["dev", "traffic"], "agents": ["dev"], "tags": ["eduzz", "webhook"]},
    "lp": {"domain": ["dev", "cro"], "agents": ["dev", "cro-specialist"], "tags": ["landing-page"]},
    "agentes": {"domain": ["meta"], "agents": ["sf-master"], "tags": ["agentes", "framework"]},
    "consciousness": {"domain": ["meta"], "agents": ["sf-master"], "tags": ["consciousness", "engine"]},
    "inema": {"domain": ["meta"], "agents": ["inema-scout"], "tags": ["inema", "knowledge"]},
    "playbook": {"domain": ["traffic"], "agents": ["traffic"], "tags": ["playbook"]},
    "CLIENTE_EXEMPLO": {"domain": ["dev"], "agents": ["dev"], "tags": ["CLIENTE_EXEMPLO", "delivery"]},
    "desafio": {"domain": ["traffic", "content"], "agents": ["traffic", "content", "launch-strategist"], "tags": ["desafio", "lançamento"]},
    "evento": {"domain": ["traffic", "content"], "agents": ["traffic", "content"], "tags": ["evento", "presencial"]},
    "CLIENTE_EXEMPLO": {"domain": ["dev"], "agents": ["dev"], "tags": ["CLIENTE_EXEMPLO", "dashboard"]},
    "carousel": {"domain": ["dev"], "agents": ["dev"], "tags": ["carousel", "css"]},
    "content-studio": {"domain": ["content"], "agents": ["content"], "tags": ["content-studio"]},
    "utm": {"domain": ["traffic", "dev"], "agents": ["traffic", "dev"], "tags": ["utm", "tracking"]},
    "empresa": {"domain": ["meta"], "agents": [], "tags": ["domina-ia", "ceo"]},
    "preferencias": {"domain": ["meta"], "agents": [], "tags": ["preferências", "ceo"]},
    "automacoes": {"domain": ["dev", "devops"], "agents": ["dev", "devops", "automation-architect"], "tags": ["automação", "cron"]},
    "daemon": {"domain": ["dev"], "agents": ["dev", "devops"], "tags": ["daemon", "telegram"]},
    "channels": {"domain": ["dev"], "agents": ["dev"], "tags": ["telegram", "channels"]},
    "mcp": {"domain": ["dev"], "agents": ["dev"], "tags": ["mcp", "servers"]},
    "rename": {"domain": ["meta"], "agents": ["sf-master"], "tags": ["rename", "framework"]},
    "CLIENTE_EXEMPLO": {"domain": ["dev"], "agents": ["dev"], "tags": ["CLIENTE_EXEMPLO", "academy"]},
    "crm": {"domain": ["dev"], "agents": ["dev", "closer"], "tags": ["crm", "pipeline"]},
    "dominantes": {"domain": ["dev"], "agents": ["dev"], "tags": ["dominantes", "plataforma"]},
    "webgpu": {"domain": ["dev"], "agents": ["dev"], "tags": ["webgpu", "futuro"]},
    "offer": {"domain": ["traffic"], "agents": ["offer-engineer"], "tags": ["oferta"]},
    "kit-empresario": {"domain": ["traffic", "dev"], "agents": ["traffic", "dev", "offer-engineer"], "tags": ["kit", "low-ticket"]},
    "mentoria": {"domain": ["meta"], "agents": [], "tags": ["mentoria", "autopilot"]},
    "skins": {"domain": ["dev"], "agents": ["dev"], "tags": ["voice-app", "skins", "orb"]},
    "apresentacao": {"domain": ["dev", "content"], "agents": ["dev", "content"], "tags": ["slides", "pdf"]},
    "skills": {"domain": ["meta"], "agents": ["sf-master"], "tags": ["skills"]},
    "catalogo": {"domain": ["content"], "agents": ["content"], "tags": ["modelos", "visual"]},
}

# Decay por tipo CORTEX
DECAY_RATES = {
    "project": 0.05,
    "infra": 0.15,
    "pattern": 0.03,
    "playbook": 0.02,
    "feedback": 0.08,
    "rule": 0.01,
    "meta": 0.01,
    "agent": 0.01,
}


def detect_cortex_type(filename, old_type):
    """Detecta o tipo CORTEX baseado no nome do arquivo e tipo original."""
    name = filename.lower()

    # Detecção por nome
    if "feedback" in name:
        return "feedback", "feedback"
    if "rules-" in name:
        return "pattern", "patterns"
    if "playbook" in name:
        return "playbook", "playbooks"
    if "infra" in name or "hostinger" in name or "vps" in name:
        return "infra", "infra"
    if any(p in name for p in ["clienteexemplo", "CLIENTE_EXEMPLO", "desafio", "evento", "kit-empresario", "CLIENTE_EXEMPLO", "CLIENTE_EXEMPLO", "dominantes"]):
        return "project", "projects"
    if "projeto" in name or "project" in name:
        return "project", "projects"

    # Fallback pelo tipo original da memória
    cortex_type, vault_dir = TYPE_MAP.get(old_type, ("meta", "meta"))
    return cortex_type, vault_dir


def detect_hints(filename):
    """Detecta domínio, agentes e tags baseado no nome do arquivo."""
    name = filename.lower().replace(".md", "")
    hints = {"domain": [], "agents": [], "tags": []}

    for keyword, hint in DOMAIN_HINTS.items():
        if keyword in name:
            hints["domain"] = list(set(hints["domain"] + hint["domain"]))
            hints["agents"] = list(set(hints["agents"] + hint["agents"]))
            hints["tags"] = list(set(hints["tags"] + hint["tags"]))

    return hints


def parse_old_memory(filepath):
    """Parse uma memória existente com frontmatter."""
    content = filepath.read_text(encoding="utf-8")

    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
    if not fm_match:
        return {"frontmatter": {}, "body": content}

    try:
        frontmatter = yaml.safe_load(fm_match.group(1)) or {}
    except yaml.YAMLError:
        frontmatter = {}

    body = fm_match.group(2).strip()
    return {"frontmatter": frontmatter, "body": body}


def migrate_file(filepath):
    """Migra um arquivo de memória para formato CORTEX."""
    filename = filepath.name
    parsed = parse_old_memory(filepath)
    old_fm = parsed["frontmatter"]
    body = parsed["body"]

    # Detectar tipo e pasta destino
    old_type = old_fm.get("type", "meta")
    cortex_type, vault_subdir = detect_cortex_type(filename, old_type)

    # Detectar hints de domínio/agentes/tags
    hints = detect_hints(filename)

    # Gerar ID
    note_id = filename.replace(".md", "")

    # Construir frontmatter CORTEX
    new_fm = {
        "id": note_id,
        "title": old_fm.get("name", old_fm.get("title", note_id.replace("-", " ").title())),
        "type": cortex_type,
        "domain": hints["domain"] or old_fm.get("domain", []),
        "agents": hints["agents"] or old_fm.get("agents", []),
        "tags": hints["tags"] or old_fm.get("tags", []),
        "status": "active",
        "created": str(old_fm.get("created", datetime.now().strftime("%Y-%m-%d"))),
        "last_verified": datetime.now().strftime("%Y-%m-%d"),
        "decay_rate": DECAY_RATES.get(cortex_type, 0.05),
        "links": [],
        "migrated_from": str(filepath),
        "old_description": old_fm.get("description", ""),
    }

    # Construir conteúdo
    content = "---\n"
    content += yaml.dump(new_fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    content += "---\n\n"
    content += body

    # Salvar
    dest_dir = VAULT_DIR / vault_subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename

    dest_path.write_text(content, encoding="utf-8")
    return dest_path, cortex_type


def main():
    if not MEMORY_DIR.exists():
        print(f"❌ Diretório de memórias não encontrado: {MEMORY_DIR}")
        return

    # Listar todos os .md (exceto MEMORY.md)
    files = [f for f in MEMORY_DIR.glob("*.md") if f.name != "MEMORY.md"]

    # Também pegar subdiretórios (arquivo/)
    for subdir in MEMORY_DIR.iterdir():
        if subdir.is_dir():
            files.extend(subdir.glob("*.md"))

    if not files:
        print("Nenhum arquivo para migrar.")
        return

    print(f"📄 Migrando {len(files)} arquivos...\n")

    stats = {}
    migrated = 0

    for filepath in sorted(files):
        try:
            dest_path, cortex_type = migrate_file(filepath)
            stats[cortex_type] = stats.get(cortex_type, 0) + 1
            rel_dest = str(dest_path).replace(str(Path.home()), "~")
            print(f"  ✅ {filepath.name} → {rel_dest} ({cortex_type})")
            migrated += 1
        except Exception as e:
            print(f"  ❌ {filepath.name} — Erro: {e}")

    print(f"\n📊 Resumo da migração:")
    print(f"   Total migrado: {migrated}/{len(files)}")
    for t, c in sorted(stats.items()):
        print(f"   {t}: {c}")


if __name__ == "__main__":
    main()
