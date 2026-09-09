#!/usr/bin/env python3
"""
dedup-check.py — Verifica se nota nova seria duplicata de existente no CORTEX.

Uso (exit codes):
  0 = OK, prosseguir com ingest (nenhuma duplicata, ou usuário forçou)
  1 = Encontrou duplicata, abortar (modo --strict)
  2 = Encontrou duplicata, mas warn-only (default)

Algoritmo:
  - Title overlap (Jaccard de tokens >3 chars):  peso 0.4
  - Tags overlap (Jaccard exato):                peso 0.3
  - Body keyword overlap:                        peso 0.3
  - Score >= 0.8 = duplicata muito provável
  - Score 0.6-0.79 = sugestão de update
  - Score < 0.6 = nota nova

Implementa: Adaptive Memory Updates inspirado em Mem0.
"""

import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

VAULT_DIR = Path.home() / "cortex" / "vault"
DUPLICATE_THRESHOLD = 0.5
SUGGEST_THRESHOLD = 0.3


def parse_args(argv):
    """Parse argumentos --title, --tags, --body, --type, --strict."""
    args = {"title": "", "tags": [], "body": "", "type": "", "strict": False}
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--title" and i + 1 < len(argv):
            args["title"] = argv[i + 1]
            i += 2
        elif a == "--tags" and i + 1 < len(argv):
            j = i + 1
            while j < len(argv) and not argv[j].startswith("--"):
                args["tags"].append(argv[j])
                j += 1
            i = j
        elif a == "--body" and i + 1 < len(argv):
            args["body"] = argv[i + 1]
            i += 2
        elif a == "--type" and i + 1 < len(argv):
            args["type"] = argv[i + 1]
            i += 2
        elif a == "--strict":
            args["strict"] = True
            i += 1
        else:
            i += 1
    return args


def tokenize(text, min_len=3):
    """Extrai tokens de palavras com >= min_len chars (lowercase)."""
    if not text:
        return set()
    return {w.lower() for w in re.findall(r"\w+", text) if len(w) >= min_len}


def jaccard(set_a, set_b):
    """Similaridade Jaccard entre dois conjuntos."""
    if not set_a and not set_b:
        return 0.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union else 0.0


def parse_note(filepath):
    """Extrai título, tags, body de uma nota markdown usando PyYAML quando disponível."""
    try:
        content = filepath.read_text()
    except Exception:
        return None

    if not content.startswith("---"):
        return {"slug": filepath.stem, "title": "", "tags": [], "body": content[:2000]}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {"slug": filepath.stem, "title": "", "tags": [], "body": content[:2000]}

    fm = {}
    if HAS_YAML:
        try:
            fm = yaml.safe_load(parts[1]) or {}
        except Exception:
            fm = {}

    title = str(fm.get("title", "")) if fm else ""
    tags = fm.get("tags", []) if fm else []
    if not isinstance(tags, list):
        tags = []
    # Filtrar tags inválidas (auto-link targets que vazaram em parse antigo)
    tags = [str(t) for t in tags if isinstance(t, str) and not t.startswith("target:")]

    return {
        "slug": filepath.stem,
        "title": title,
        "tags": tags,
        "body": parts[2][:2000],
    }


def score_similarity(new_note, existing_note):
    """Score 0-1 entre 2 notas. Peso maior pro título (sinal mais forte)."""
    title_sim = jaccard(
        tokenize(new_note["title"]),
        tokenize(existing_note["title"])
    )
    tags_sim = jaccard(
        set(t.lower() for t in new_note["tags"]),
        set(t.lower() for t in existing_note["tags"])
    )
    body_sim = jaccard(
        tokenize(new_note["body"]),
        tokenize(existing_note["body"])
    )
    # Título é sinal mais confiável: peso 0.6
    return 0.6 * title_sim + 0.2 * tags_sim + 0.2 * body_sim


def main():
    args = parse_args(sys.argv)

    if not args["title"]:
        # Sem título, não dá pra checar — prosseguir silenciosamente
        sys.exit(0)

    new_note = {
        "title": args["title"],
        "tags": args["tags"],
        "body": args["body"],
    }

    # Scan vault para candidatos
    matches = []
    for md in VAULT_DIR.rglob("*.md"):
        if md.name == "README.md":
            continue
        existing = parse_note(md)
        if not existing:
            continue
        score = score_similarity(new_note, existing)
        if score >= SUGGEST_THRESHOLD:
            matches.append((score, existing["slug"], existing["title"]))

    matches.sort(reverse=True)

    if not matches:
        # Nenhuma similaridade significativa — prosseguir
        sys.exit(0)

    # Encontrou candidatos
    duplicates = [m for m in matches if m[0] >= DUPLICATE_THRESHOLD]
    suggestions = [m for m in matches if SUGGEST_THRESHOLD <= m[0] < DUPLICATE_THRESHOLD]

    print(f"\n⚠️  CORTEX dedup-check — Notas similares encontradas:\n")

    if duplicates:
        print(f"  🔴 PROVÁVEL DUPLICATA (score >= {DUPLICATE_THRESHOLD}):")
        for score, slug, title in duplicates[:3]:
            print(f"    [{score:.2f}] {slug}")
            print(f"           título: {title[:80]}")

    if suggestions:
        print(f"\n  🟡 Pode ser update de existente (score {SUGGEST_THRESHOLD}-{DUPLICATE_THRESHOLD}):")
        for score, slug, title in suggestions[:3]:
            print(f"    [{score:.2f}] {slug}")
            print(f"           título: {title[:80]}")

    print(f"\n  💡 Considere usar 'refresh.sh' ou editar nota existente em vez de criar nova.")
    print(f"     Para forçar criação mesmo assim, adicione flag --skip-dedup ao ingest.\n")

    if duplicates and args["strict"]:
        sys.exit(1)
    elif duplicates:
        sys.exit(2)  # warn-only
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
