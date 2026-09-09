#!/usr/bin/env python3
"""
eros-gate.py — Validador EROS automático

Hook PostToolUse que detecta entregas não-triviais e valida contra checklist EROS.
Bloqueia se score <4/5. Inspirado nos quality gates do ruflo-sparc.

Comportamento:
- Silencioso em entregas triviais (read, lint, format, navegação)
- Lê output do tool atual (via JSON stdin)
- Aplica heurísticas para classificar trivialidade
- Se non-trivial: avalia critérios EROS e injeta veredito
- Score <4/5: emite warning (não bloqueante por padrão para evitar quebrar fluxo)
  → para BLOQUEIO real, definir EROS_GATE_STRICT=1 no env

Instalação manual: adicionar em ~/.claude/settings.json hooks.PostToolUse:
  {
    "matcher": "Write|Edit|MultiEdit",
    "hooks": [{"type": "command", "command": "python3 $HOME/.claude/hooks/eros-gate.py"}]
  }

Para ativar quando estiver maduro. Por ora: opt-in.
"""
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime

LOG_PATH = Path.home() / ".claude" / "logs" / "eros-gate.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# Triviality detection — heurísticas baratas
TRIVIAL_TOOLS = {"Read", "Glob", "Grep", "Bash"}  # leituras + bash genérico
NON_TRIVIAL_TOOLS = {"Write", "Edit", "MultiEdit"}  # geração/modificação

# Patterns que marcam entrega trivial mesmo em tool non-trivial
TRIVIAL_PATTERNS = [
    r"^\s*#.*$",                    # apenas comentário
    r"^\s*$",                       # vazio
    r"^[\s\n]*//.*[\s\n]*$",         # comentário JS
]

# Patterns que marcam entrega SUBSTANTIVA (precisa de gate)
SUBSTANTIVE_INDICATORS = [
    r"function\s+\w+\s*\(",        # nova função
    r"def\s+\w+\s*\(",             # função Python
    r"class\s+\w+",                # nova classe
    r"---\s*\nname:",              # frontmatter de skill/agent
    r"# [A-Z]",                    # título de doc/spec
]


def log(message: str):
    """Append ao log para depuração."""
    with LOG_PATH.open("a") as f:
        f.write(f"{datetime.now().isoformat()} {message}\n")


def is_trivial(tool_name: str, content: str) -> bool:
    """Decide se a entrega é trivial e merece passar sem gate."""
    if tool_name in TRIVIAL_TOOLS:
        return True
    if tool_name not in NON_TRIVIAL_TOOLS:
        return True  # tool desconhecido = não interferir
    if not content:
        return True
    if len(content) < 100:
        return True  # mudança pequena
    # se NENHUM indicador substantivo aparece, é trivial
    has_substantive = any(re.search(p, content) for p in SUBSTANTIVE_INDICATORS)
    return not has_substantive


def assess_eros(content: str, file_path: str) -> dict:
    """
    Avaliação EROS heurística (5 critérios + score).
    NOT um LLM call — análise estática.

    Para gate VERDADEIRO via LLM, ativar via comando separado:
      bash ~/.claude/skills/eros-verdict.sh {file}
    """
    score = 5
    notes = []

    # Completude (heurística: arquivo termina abrupto?)
    if content.rstrip().endswith(("TODO", "FIXME", "...", "// continue")):
        score -= 1
        notes.append("Completude: possíveis TODOs não resolvidos")

    # Precisão (heurística: typos comuns ou placeholders)
    placeholders = re.findall(r"(?i)\b(lorem|xxx|placeholder|insert\s+here)\b", content)
    if placeholders:
        score -= 1
        notes.append(f"Precisão: {len(placeholders)} placeholders detectados")

    # Qualidade (heurística: tamanho de funções)
    long_blocks = len(re.findall(r"^(function|def)\s+\w+[^}]{2000,}\}", content, re.M))
    if long_blocks > 0:
        score -= 1
        notes.append(f"Qualidade: {long_blocks} função(ões) >40 linhas — refactor sugerido")

    # Coerência (heurística: arquivo markdown com frontmatter incompleto)
    if file_path.endswith(".md") and content.startswith("---"):
        if not re.search(r"^(name|description):", content, re.M):
            score -= 1
            notes.append("Coerência: frontmatter sem name/description")

    # Utilidade (heurística: docstring/comment para funções)
    funcs = len(re.findall(r"^(function|def)\s+\w+", content, re.M))
    if funcs > 0:
        doc_funcs = len(re.findall(r"(\/\*\*|\"\"\"|@param|@return).*\n.*(function|def)\s+\w+", content))
        coverage = doc_funcs / funcs if funcs else 1
        if coverage < 0.5 and funcs > 3:
            score -= 1
            notes.append(f"Utilidade: apenas {int(coverage*100)}% das funções documentadas")

    return {
        "score": max(0, score),
        "max": 5,
        "notes": notes,
        "verdict": (
            "AUTORIZADO" if score >= 4 else
            "CONDICIONAL" if score == 3 else
            "BLOQUEADO"
        )
    }


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        event = json.loads(raw)
    except Exception as e:
        log(f"Failed to parse stdin: {e}")
        return 0  # nunca quebra fluxo

    tool = event.get("tool_name", "")
    tool_input = event.get("tool_input", {}) or {}
    content = tool_input.get("content") or tool_input.get("new_string") or ""
    file_path = tool_input.get("file_path", "")

    if is_trivial(tool, content):
        return 0  # passa silencioso

    eros = assess_eros(content, file_path)
    log(f"{tool} on {file_path} → score {eros['score']}/{eros['max']} ({eros['verdict']})")

    if eros["score"] < 4:
        msg = (
            f"\n⚠️  EROS GATE — Score {eros['score']}/5 ({eros['verdict']})\n"
            + "\n".join(f"  - {n}" for n in eros["notes"])
            + "\n  Considere revisar antes de continuar.\n"
        )
        if os.getenv("EROS_GATE_STRICT") == "1":
            # Block: stderr message + non-zero exit
            print(msg, file=sys.stderr)
            return 2  # exit code 2 sinaliza ao Claude Code que o hook bloqueou
        else:
            # Warning mode (default): print to stderr but exit 0
            print(msg, file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
