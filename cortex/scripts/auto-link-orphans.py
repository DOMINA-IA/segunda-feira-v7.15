#!/usr/bin/env python3
"""
auto-link-orphans.py — Conecta notas orphan no vault CORTEX por similaridade.

Para cada nota sem links (orphan), busca notas com tags/domain/keywords em comum
e adiciona links bidirecionais automaticamente.

Uso: python3 auto-link-orphans.py [--dry-run] [--min-overlap 2]
"""

import json
import os
import re
import sys
from pathlib import Path

VAULT_DIR = Path.home() / "cortex" / "vault"
INDEX_FILE = Path.home() / "cortex" / "index" / "search-index.json"

DRY_RUN = "--dry-run" in sys.argv
MIN_OVERLAP = 2

for i, arg in enumerate(sys.argv):
    if arg == "--min-overlap" and i + 1 < len(sys.argv):
        MIN_OVERLAP = int(sys.argv[i + 1])


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extrai frontmatter YAML simples e retorna (metadata, body)."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    fm_text = parts[1].strip()
    body = parts[2]
    metadata = {}

    current_key = None
    current_list = None

    for line in fm_text.split("\n"):
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # List item under current key
        if line_stripped.startswith("- ") and current_key:
            if current_list is None:
                current_list = []
                metadata[current_key] = current_list
            item = line_stripped[2:].strip()
            if ":" in item and not item.startswith("target"):
                # Sub-dict in list (links format)
                if isinstance(current_list, list) and current_list and isinstance(current_list[-1], dict):
                    k, v = item.split(":", 1)
                    current_list[-1][k.strip()] = v.strip()
                else:
                    current_list.append(item)
            elif item.startswith("target:"):
                current_list.append({"target": item.split(":", 1)[1].strip()})
            else:
                current_list.append(item)
            continue

        # Sub-key in list item (like "  type: related")
        if line.startswith("  ") and ":" in line_stripped and current_list and isinstance(current_list[-1], dict):
            k, v = line_stripped.split(":", 1)
            current_list[-1][k.strip()] = v.strip()
            continue

        # Top-level key
        if ":" in line_stripped and not line_stripped.startswith("-"):
            k, v = line_stripped.split(":", 1)
            k = k.strip()
            v = v.strip()
            current_key = k
            current_list = None
            if v:
                metadata[k] = v
            continue

    return metadata, body


def get_note_slug(filepath: Path) -> str:
    return filepath.stem


def get_existing_links(metadata: dict) -> set:
    links = metadata.get("links", [])
    if isinstance(links, list):
        return {l.get("target", l) if isinstance(l, dict) else l for l in links}
    return set()


def get_matchable_tokens(metadata: dict, body: str) -> set:
    """Extrai tokens para matching: tags + domain + keywords do index."""
    tokens = set()

    for key in ["tags", "domain", "keywords"]:
        val = metadata.get(key, [])
        if isinstance(val, list):
            tokens.update(str(v).lower().strip() for v in val)
        elif isinstance(val, str):
            tokens.update(v.strip().lower() for v in val.split(","))

    # Extract from title
    title = metadata.get("title", "")
    if isinstance(title, list):          # frontmatter com title em lista (falhava desde 31-Ago: TypeError)
        title = " ".join(str(x) for x in title)
    if title:
        tokens.update(w.lower() for w in re.findall(r'\w{4,}', title))

    return tokens


def add_link_to_note(filepath: Path, target_slug: str) -> bool:
    """Adiciona link ao frontmatter de uma nota."""
    content = filepath.read_text()

    # Check if link already exists
    if f"target: {target_slug}" in content:
        return False

    if "links: []" in content:
        # Replace empty list literal with populated list
        content = content.replace(
            "links: []",
            f"links:\n- target: {target_slug}\n  type: auto-linked",
            1
        )
    elif "links:" in content:
        # Append to existing links section
        content = content.replace(
            "links:\n",
            f"links:\n- target: {target_slug}\n  type: auto-linked\n",
            1
        )
    elif content.startswith("---"):
        # Add links section before closing ---
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm = parts[1].rstrip()
            content = f"---{fm}\nlinks:\n- target: {target_slug}\n  type: auto-linked\n---{parts[2]}"
    else:
        # No frontmatter — add one
        content = f"---\nlinks:\n- target: {target_slug}\n  type: auto-linked\n---\n{content}"

    filepath.write_text(content)
    return True


def main():
    # Load index for keyword data
    index_data = {}
    if INDEX_FILE.exists():
        with open(INDEX_FILE) as f:
            index_data = json.load(f)

    # Scan all notes
    notes = {}
    for md in VAULT_DIR.rglob("*.md"):
        if md.name == "README.md":
            continue
        slug = get_note_slug(md)
        content = md.read_text()
        metadata, body = parse_frontmatter(content)

        # Enrich with index data
        idx = index_data.get(slug, {})
        for key in ["tags", "domain", "keywords"]:
            if key in idx and key not in metadata:
                metadata[key] = idx[key]

        notes[slug] = {
            "path": md,
            "metadata": metadata,
            "tokens": get_matchable_tokens(metadata, body),
            "links": get_existing_links(metadata),
        }

    # Find orphans
    orphans = {slug: n for slug, n in notes.items() if not n["links"]}
    print(f"Notas totais: {len(notes)}")
    print(f"Orphans: {len(orphans)}")
    print()

    links_created = 0
    linked_orphans = 0

    for orphan_slug, orphan in orphans.items():
        if not orphan["tokens"]:
            continue

        best_matches = []
        for other_slug, other in notes.items():
            if other_slug == orphan_slug:
                continue
            overlap = orphan["tokens"] & other["tokens"]
            if len(overlap) >= MIN_OVERLAP:
                best_matches.append((other_slug, len(overlap), overlap))

        # Sort by overlap, take top 3
        best_matches.sort(key=lambda x: x[1], reverse=True)
        top = best_matches[:3]

        if top:
            linked_orphans += 1
            for target_slug, overlap_count, shared in top:
                if DRY_RUN:
                    print(f"  {orphan_slug} → {target_slug} (overlap: {overlap_count}, shared: {list(shared)[:4]})")
                else:
                    # Bidirecional
                    if add_link_to_note(orphan["path"], target_slug):
                        links_created += 1
                    target_note = notes.get(target_slug)
                    if target_note and add_link_to_note(target_note["path"], orphan_slug):
                        links_created += 1

    print(f"\nOrphans linkados: {linked_orphans}")
    print(f"Links criados: {links_created}")
    if DRY_RUN:
        print("[DRY-RUN] Nenhuma alteração feita")


if __name__ == "__main__":
    main()
