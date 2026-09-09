#!/usr/bin/env python3
"""
cortex_pagerank.py — PageRank sobre o grafo de notas CORTEX

Ranqueia notas por importância usando:
- PageRank clássico (damping 0.85) sobre links [[name]]
- Boost por frequência de acesso (se disponível)
- Decay temporal exponencial

Output:
- Top N load-bearing (proteger)
- Bottom N orphans (candidatos a archive)
- Métricas agregadas por eixo (META/OPS)

Uso:
    python3 ~/cortex/scripts/cortex_pagerank.py
    python3 ~/cortex/scripts/cortex_pagerank.py --top 50 --bottom 50
    python3 ~/cortex/scripts/cortex_pagerank.py --output ~/cortex/reports/pagerank.json

Origem: ruflo agent-pagerank-analyzer adaptado para CORTEX.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta

VAULT = Path.home() / "cortex" / "vault"
REPORTS_DIR = Path.home() / "cortex" / "reports"
WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def collect_notes() -> dict:
    """Walk vault, collect all notes with slug + outlinks + frontmatter."""
    notes = {}
    for md in VAULT.rglob("*.md"):
        # skip índices e symlinks duplicados
        if "/_index_by_axis/" in str(md):
            continue
        if md.is_symlink():
            continue
        slug = md.stem
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        outlinks = set(m.group(1).strip() for m in WIKILINK.finditer(text))
        outlinks.discard(slug)  # self-link not counted
        # Parse minimal frontmatter
        axis = "unknown"
        date_str = None
        fm = FRONTMATTER.match(text)
        if fm:
            body = fm.group(1)
            for line in body.split("\n"):
                line = line.strip()
                if line.startswith("axis:"):
                    axis = line.split(":", 1)[1].strip()
                elif line.startswith("date:") or line.startswith("created:"):
                    date_str = line.split(":", 1)[1].strip().strip('"\'')
        notes[slug] = {
            "path": str(md),
            "outlinks": outlinks,
            "axis": axis,
            "date": date_str,
            "size": md.stat().st_size,
            "mtime": md.stat().st_mtime,
        }
    return notes


def compute_pagerank(notes: dict, damping: float = 0.85, max_iter: int = 100,
                     epsilon: float = 1e-6) -> dict:
    """Standard PageRank computation."""
    slugs = list(notes.keys())
    n = len(slugs)
    if n == 0:
        return {}
    # Build inverse graph: who links TO each note
    inlinks = defaultdict(set)
    for slug, data in notes.items():
        for target in data["outlinks"]:
            if target in notes:
                inlinks[target].add(slug)
    # Initialize
    scores = {s: 1.0 / n for s in slugs}
    base = (1.0 - damping) / n
    for iteration in range(max_iter):
        new_scores = {}
        for slug in slugs:
            inbound = inlinks.get(slug, set())
            contrib = sum(
                scores[src] / max(1, len(notes[src]["outlinks"]))
                for src in inbound if src in notes
            )
            new_scores[slug] = base + damping * contrib
        # Check convergence
        delta = sum(abs(new_scores[s] - scores[s]) for s in slugs)
        scores = new_scores
        if delta < epsilon:
            break
    return scores


def apply_decay(scores: dict, notes: dict, half_life_days: int = 365) -> dict:
    """Aplicar decay temporal exponencial baseado em mtime."""
    now = datetime.now().timestamp()
    decay_per_sec = math.log(2) / (half_life_days * 86400)
    adjusted = {}
    for slug, score in scores.items():
        age_sec = now - notes[slug]["mtime"]
        decay = math.exp(-decay_per_sec * age_sec)
        adjusted[slug] = score * decay
    return adjusted


def main():
    parser = argparse.ArgumentParser(description="PageRank sobre CORTEX vault")
    parser.add_argument("--top", type=int, default=50)
    parser.add_argument("--bottom", type=int, default=50)
    parser.add_argument("--damping", type=float, default=0.85)
    parser.add_argument("--max-iter", type=int, default=100)
    parser.add_argument("--epsilon", type=float, default=1e-6)
    parser.add_argument("--half-life", type=int, default=365,
                        help="Half-life em dias para decay temporal")
    parser.add_argument("--no-decay", action="store_true")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    print("📊 Coletando notas...", file=sys.stderr)
    notes = collect_notes()
    print(f"   {len(notes)} notas únicas (excluindo symlinks/index)", file=sys.stderr)

    if len(notes) == 0:
        print("⚠️  Nenhuma nota encontrada", file=sys.stderr)
        return 1

    print(f"🔄 PageRank iterativo (damping={args.damping})...", file=sys.stderr)
    raw_scores = compute_pagerank(notes, args.damping, args.max_iter, args.epsilon)

    if not args.no_decay:
        print(f"⏳ Aplicando decay temporal (half-life={args.half_life}d)...", file=sys.stderr)
        scores = apply_decay(raw_scores, notes, args.half_life)
    else:
        scores = raw_scores

    sorted_notes = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)

    # Axis breakdown
    axis_counts = defaultdict(lambda: {"count": 0, "total_score": 0.0})
    for slug, score in scores.items():
        axis = notes[slug]["axis"]
        axis_counts[axis]["count"] += 1
        axis_counts[axis]["total_score"] += score
    axis_breakdown = {
        ax: {
            "count": data["count"],
            "avg_score": data["total_score"] / data["count"] if data["count"] else 0
        }
        for ax, data in axis_counts.items()
    }

    # Build inlinks for output
    inlinks = defaultdict(set)
    for slug, data in notes.items():
        for tgt in data["outlinks"]:
            if tgt in notes:
                inlinks[tgt].add(slug)

    top = [
        {
            "slug": slug,
            "score": round(score, 6),
            "inlinks": len(inlinks[slug]),
            "outlinks": len(notes[slug]["outlinks"]),
            "axis": notes[slug]["axis"],
            "path": notes[slug]["path"],
        }
        for slug, score in sorted_notes[:args.top]
    ]
    bottom = [
        {
            "slug": slug,
            "score": round(score, 6),
            "inlinks": len(inlinks[slug]),
            "outlinks": len(notes[slug]["outlinks"]),
            "axis": notes[slug]["axis"],
            "path": notes[slug]["path"],
            "is_orphan": len(inlinks[slug]) == 0 and len(notes[slug]["outlinks"]) == 0,
        }
        for slug, score in sorted_notes[-args.bottom:]
    ]

    result = {
        "computed_at": datetime.now().isoformat(),
        "total_notes": len(notes),
        "damping": args.damping,
        "decay_applied": not args.no_decay,
        "half_life_days": args.half_life if not args.no_decay else None,
        "axis_breakdown": axis_breakdown,
        "top_loadbearing": top,
        "bottom_candidates_archive": bottom,
    }

    # Output
    output_path = args.output or (REPORTS_DIR / f"pagerank-{datetime.now().strftime('%Y-%m-%d')}.json")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Relatório salvo: {output_path}", file=sys.stderr)

    # Quick summary on stdout
    print(f"\n📈 TOP 10 LOAD-BEARING (proteger):")
    for entry in top[:10]:
        print(f"  {entry['score']:.4f}  in={entry['inlinks']:3d}  [{entry['axis']:5s}]  {entry['slug'][:80]}")
    print(f"\n📉 BOTTOM 10 (candidatos a archive):")
    for entry in bottom[:10]:
        mark = " 👻" if entry.get("is_orphan") else ""
        print(f"  {entry['score']:.4f}  in={entry['inlinks']:3d}  [{entry['axis']:5s}]  {entry['slug'][:75]}{mark}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
