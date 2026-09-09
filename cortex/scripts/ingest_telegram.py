#!/usr/bin/env python3
"""
INEMA Indexer — converte 34 canais Telegram (3.8GB) em notas CORTEX consultáveis.

Estratégia: 1 nota por canal (não por mensagem) — preserva o sinal sem poluir o vault.
Cada nota inclui: estatísticas, top links, palavras-chave, ponteiro para o raw md.

Uso:
  python3 ~/cortex/scripts/ingest_telegram.py            # ingere todos os canais
  python3 ~/cortex/scripts/ingest_telegram.py INEMA_VOZ  # canal específico
"""

import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HOME = Path.home()
SCRAPER_OUT = HOME / "projetos" / "telegram-scraper" / "output"
VAULT = HOME / "cortex" / "vault" / "feedback"
SUMMARY = SCRAPER_OUT / "summary.json"

CHANNEL_DOMAINS = {
    "VOZ": "voice", "VIBE": "ai-tools", "CCODE": "claude-code",
    "VIDEOS": "video", "AGENTES": "agents", "LLMs": "llms",
    "N8N": "automation", "MKT": "marketing", "IA": "ai",
    "IMAGENS": "image-gen", "AVATARES": "avatar", "VISION": "vision",
    "BMAD": "framework", "DEV": "dev", "TDS": "framework",
    "Codex": "codex", "INFRA": "infra", "TOOLS": "tools",
    "Educ": "education", "Prompts": "prompts", "VIP": "premium",
    "FTD": "framework", "FREE": "free-tier", "Google": "google-ai",
    "Make": "automation", "MUSICAL": "audio", "ROBOT": "robotics",
    "GAMES": "games", "Teste": "test", "PLUS": "premium",
    "TIA": "ai", "YOUTUBE": "youtube", "ADULTO": "adult", "CONSULT": "consulting",
}

WORDS_PT_STOP = {
    "a", "o", "e", "de", "da", "do", "em", "para", "que", "com", "um", "uma",
    "os", "as", "no", "na", "se", "por", "mais", "ou", "como", "ao", "dos",
    "das", "ser", "tem", "este", "esta", "isso", "tudo", "aqui", "ai", "ja",
    "https", "http", "www", "com", "br", "the", "to", "of", "and", "is", "in",
    "for", "you", "it", "this", "that", "with", "are", "be", "i", "we", "as",
    "at", "by", "or", "from", "can", "have", "if", "so", "but", "not", "on",
    "an", "all", "your", "my", "me", "use", "do", "es", "lo", "la",
}


def slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9_-]", "-", text.lower())
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:60]


def extract_top_keywords(text: str, n: int = 20) -> list[str]:
    """Extrai palavras-chave mais frequentes (3+ chars, não-stopwords)."""
    words = re.findall(r"[a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ0-9_-]{3,}", text.lower())
    filtered = [w for w in words if w not in WORDS_PT_STOP and len(w) >= 4]
    return [w for w, _ in Counter(filtered).most_common(n)]


def extract_top_links(links_text: str, n: int = 15) -> list[str]:
    """Extrai links mais relevantes (priorizando github, hf, n8n, papers)."""
    if not links_text:
        return []
    lines = [l.strip() for l in links_text.splitlines() if l.strip().startswith("http")]
    seen = set()
    priority = []
    other = []
    for url in lines:
        # Limpar duplicatas
        clean = url.split("?")[0].split("#")[0]
        if clean in seen:
            continue
        seen.add(clean)
        if any(kw in url for kw in ["github.com", "huggingface.co", "n8n.io", "arxiv.org", "anthropic.com", "openai.com", "claude.ai"]):
            priority.append(url)
        else:
            other.append(url)
    return (priority + other)[:n]


def build_note_for_channel(channel_dir: Path, channel_meta: dict | None) -> str | None:
    """Gera o conteúdo .md da nota CORTEX para um canal."""
    name = channel_dir.name
    short = name.replace("INEMA_", "")
    domain = CHANNEL_DOMAINS.get(short, "knowledge")
    slug = f"inema-kb-{slugify(short)}"

    msgs_md = channel_dir / "messages.md"
    links_txt = channel_dir / "links.txt"

    if not msgs_md.exists():
        return None

    md_text = msgs_md.read_text(encoding="utf-8", errors="ignore")
    links_text = links_txt.read_text(encoding="utf-8", errors="ignore") if links_txt.exists() else ""

    keywords = extract_top_keywords(md_text, 25)
    top_links = extract_top_links(links_text, 15)

    msg_count = channel_meta.get("messages", 0) if channel_meta else 0
    new_count = channel_meta.get("new_messages", 0) if channel_meta else 0
    file_count = channel_meta.get("files", 0) if channel_meta else 0
    raw_size_mb = round(sum(f.stat().st_size for f in channel_dir.rglob("*") if f.is_file()) / 1024 / 1024, 1)

    today = datetime.now().strftime("%Y-%m-%d")
    last_scrape = channel_meta.get("scrape_date", today) if channel_meta else today

    tags = ["inema", "telegram-kb", domain] + keywords[:5]
    tags_yaml = "\n".join(f"  - {t}" for t in tags)

    links_md = "\n".join(f"  - {url}" for url in top_links) if top_links else "  - (sem links)"
    keywords_md = ", ".join(keywords[:25])

    body = f"""---
title: "INEMA KB — {short}"
description: "Snapshot do canal Telegram {name} ({msg_count} mensagens, {raw_size_mb}MB). {new_count} novas no último scrape."
type: feedback
domain: {domain}
agents:
  - inema-scout
  - sf-master
tags:
{tags_yaml}
status: active
created: {today}
last_verified: {today}
---

# INEMA KB — {short}

**Canal Telegram:** `{name}`
**Mensagens totais:** {msg_count} ({new_count} novas no último scrape de {last_scrape})
**Arquivos:** {file_count} | **Tamanho raw:** {raw_size_mb}MB
**Domínio inferido:** {domain}

## Top Keywords (frequência no canal)

{keywords_md}

## Top Links (priorizando github / huggingface / n8n / papers)

{links_md}

## Onde está o raw

- Mensagens: `~/projetos/telegram-scraper/output/{name}/messages.md`
- Mensagens (JSON): `~/projetos/telegram-scraper/output/{name}/messages.json`
- Links completos: `~/projetos/telegram-scraper/output/{name}/links.txt`
- Mídia (se houver): `~/projetos/telegram-scraper/output/{name}/media/`

## Como consultar

Esta nota é apenas o índice. Para conteúdo profundo do canal, use:

```bash
# Buscar por termo
grep -i "TERMO" ~/projetos/telegram-scraper/output/{name}/messages.md

# Listar últimas mensagens
tail -200 ~/projetos/telegram-scraper/output/{name}/messages.md

# Re-mining via inema-scout
# claude /agents inema-scout — depois pergunte sobre {short}
```
"""
    return slug, body


def main():
    if not SUMMARY.exists():
        print(f"ERRO: summary.json não encontrado em {SUMMARY}")
        sys.exit(1)

    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    groups_meta = {g["name"].replace(".", "_"): g for g in summary.get("groups", [])}

    target = sys.argv[1] if len(sys.argv) > 1 else None

    VAULT.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0
    for channel_dir in sorted(SCRAPER_OUT.iterdir()):
        if not channel_dir.is_dir() or not channel_dir.name.startswith("INEMA_"):
            continue
        if target and channel_dir.name != target:
            continue

        meta = groups_meta.get(channel_dir.name) or groups_meta.get(channel_dir.name.replace("_", "."))
        result = build_note_for_channel(channel_dir, meta)
        if not result:
            print(f"  ⏭️  {channel_dir.name}: sem messages.md, pulando")
            skipped += 1
            continue

        slug, body = result
        note_path = VAULT / f"{slug}.md"
        note_path.write_text(body, encoding="utf-8")
        print(f"  ✅ {slug}.md ({len(body)} chars)")
        created += 1

    print(f"\n📊 INEMA Indexer:")
    print(f"   Notas criadas/atualizadas: {created}")
    print(f"   Canais pulados: {skipped}")
    print(f"   Vault: {VAULT}")
    print(f"\nPróximo passo: python3 ~/cortex/scripts/cortex_engine.py build-index")


if __name__ == "__main__":
    main()
