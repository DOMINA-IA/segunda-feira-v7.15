#!/usr/bin/env python3
"""
freeze.py — PreToolUse hook (matcher: Write|Edit|MultiEdit) que restringe edições a um diretório.

Origem: absorvido do /freeze do gstack (Garry Tan) em 26-Jun-2026.
Previne scope-creep: durante debug/trabalho focado, bloqueia edições fora do
diretório permitido. Inerte quando não há freeze ativo (zero impacto default).

Estado: ~/.claude/.session-state/freeze.json
  {"path": "/abs/dir/", "session": "<id>", "set_at": <epoch>}

Ativar/desativar via skill /freeze (ou editar o arquivo de estado).
Quando ativo e a edição-alvo está FORA do path → permissionDecision "deny".
A barra final no path evita match por substring (lição do gstack).
"""
import json
import os
import sys
from pathlib import Path

STATE = Path.home() / ".claude" / ".session-state" / "freeze.json"


def main():
    if not STATE.exists():
        sys.exit(0)  # sem freeze ativo → não interferir

    try:
        state = json.loads(STATE.read_text())
        allowed = state.get("path", "")
    except Exception:
        sys.exit(0)

    if not allowed:
        sys.exit(0)

    # Normaliza com barra final (evita que /foo libere /foobar)
    allowed = os.path.abspath(os.path.expanduser(allowed))
    if not allowed.endswith(os.sep):
        allowed += os.sep

    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool = payload.get("tool_name", "")
    if tool not in ("Write", "Edit", "MultiEdit"):
        sys.exit(0)

    target = payload.get("tool_input", {}).get("file_path", "") or ""
    if not target:
        sys.exit(0)

    target_abs = os.path.abspath(os.path.expanduser(target))

    if not target_abs.startswith(allowed):
        reason = (
            f"🧊 FREEZE ativo — edição bloqueada.\n"
            f"   Permitido apenas em: {allowed}\n"
            f"   Tentou editar: {target_abs}\n"
            f"   Para liberar: /freeze off  (ou amplie o escopo com /freeze <dir>)."
        )
        out = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
        print(json.dumps(out))
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
