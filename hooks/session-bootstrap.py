#!/usr/bin/env python3
"""session-bootstrap.py — Contexto no primeiro segundo da sessão (SessionStart).

O que faz uma instalação madura ser mais eficiente não é só permissão: cada mensagem
chega com briefing injetado (router CORTEX). Quem ainda não tem o CORTEX começa do
zero toda sessão. Este hook dá o mínimo que qualquer projeto tem:

  - onde estou (repo, branch, último commit, arquivos sujos)
  - o que o projeto diz de si (README / CLAUDE.md / AGENTS.md: 1ª linha)
  - stories com tarefa aberta (docs/stories)
  - o que ficou pendente na última sessão (~/.claude/.last-preflight.json)
  - quanta autonomia já foi conquistada (livro-razão do autonomy-gate)

Sai em stdout → vira contexto adicional da sessão. Sempre exit 0; no máximo ~25 linhas.
"""
import json
import subprocess
import sys
import time
from pathlib import Path


def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""


def main():
    cwd = Path.cwd()
    lines = [f"[Segunda-feira bootstrap — {cwd.name}]"]
    if sh("git rev-parse --is-inside-work-tree 2>/dev/null") == "true":
        branch = sh("git branch --show-current")
        last = sh("git log -1 --format='%h %ad %s' --date=short")
        dirty = sh("git status --short | wc -l").strip()
        lines.append(f"  git: {branch} · último commit {last} · {dirty} arquivo(s) sem commit")
    else:
        lines.append("  git: NÃO é repositório — autonomia fica em 'ask' até ter git (sem git não há como reverter)")
    for f in ("README.md", "CLAUDE.md", "AGENTS.md"):
        p = cwd / f
        if p.exists():
            first = next((l.strip("# ").strip() for l in p.read_text(errors="ignore").splitlines() if l.strip()), "")
            lines.append(f"  {f}: {first[:90]}")
    stories_dir = cwd / "docs" / "stories"
    if stories_dir.exists():
        stories = sorted(stories_dir.glob("*.md"))
        abertas = [s.name for s in stories if "[ ]" in s.read_text(errors="ignore")][:3]
        lines.append(f"  stories: {len(stories)} · com tarefa aberta: {', '.join(abertas) or 'nenhuma'}")
    pf = Path.home() / ".claude" / ".last-preflight.json"
    if pf.exists() and time.time() - pf.stat().st_mtime < 7 * 86400:
        try:
            d = json.loads(pf.read_text())
            pend = d.get("findings") or d.get("pendencias") or []
            if pend:
                lines.append(f"  pendente da última sessão: {str(pend[0])[:100]}")
        except Exception:
            pass
    led = Path.home() / ".claude" / ".autonomy-ledger.json"
    if led.exists():
        try:
            d = json.loads(led.read_text())
            conf = [k for k, v in d.get("classes", {}).items()
                    if sum(1 for r in v.get("recent", [])[-20:] if r == 1) >= 5 and 0 not in v.get("recent", [])[-20:]]
            lines.append("  autonomia conquistada: " + (", ".join(conf) or
                         "nenhuma classe ainda (execute e aprove; após 5 OK sem falha a classe libera sozinha)"))
        except Exception:
            pass
    lines.append("  regra: leitura livre · escrita/git/scripts liberam com histórico · produção sempre pergunta · destrutivo nunca")
    print("\n".join(lines[:25]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
