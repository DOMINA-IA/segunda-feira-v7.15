#!/usr/bin/env python3
"""
careful.py — PreToolUse hook (matcher: Bash) que pede confirmação em comandos destrutivos.

Origem: absorvido do /careful do gstack (Garry Tan) em 26-Jun-2026.
Operacionaliza em CÓDIGO a coluna "risco alto" da autonomous-execution.md.
Filosofia (visual-rendering-safety.md): "memória esquece, código não".

Comportamento:
- Lê o tool_input via stdin (JSON do Claude Code).
- Se o comando Bash casar um padrão destrutivo E não for exceção segura → permissionDecision "ask".
- Caso contrário → silencioso (não interfere; o harness segue o fluxo normal).

NÃO bloqueia ("deny"): apenas eleva para confirmação humana ("ask"). Reversível
removendo o bloco do settings.json (backup em settings.json.pre-careful-*).
"""
import json
import re
import sys

# Padrões destrutivos (regex, case-insensitive). Cada um = (padrão, descrição).
DESTRUCTIVE = [
    (r"\brm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)\b", "rm -rf (remoção recursiva forçada)"),
    (r"\brm\s+-[a-z]*r\b.*\*", "rm -r com wildcard"),
    (r"\bgit\s+push\b.*--force\b", "git push --force"),
    (r"\bgit\s+push\b.*\s-f\b", "git push -f"),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard"),
    (r"\bgit\s+clean\s+-[a-z]*f", "git clean -f (apaga untracked)"),
    (r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", "DROP TABLE/DATABASE"),
    (r"\bTRUNCATE\s+TABLE\b", "TRUNCATE TABLE"),
    (r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", "DELETE FROM sem WHERE"),
    (r"\bUPDATE\b(?!.*\bWHERE\b).*\bSET\b", "UPDATE sem WHERE"),
    (r"\bkubectl\s+delete\b", "kubectl delete"),
    (r"\bdocker\s+system\s+prune\b", "docker system prune"),
    (r"\bdd\s+if=", "dd (escrita de disco bruta)"),
    (r"\bmkfs\b", "mkfs (formatação)"),
    (r":\(\)\s*\{.*\};:", "fork bomb"),
    (r">\s*/dev/sd[a-z]", "escrita direta em disco"),
    (r"\bchmod\s+-R\s+777\b", "chmod -R 777 (permissão insegura)"),
]

# Exceções seguras: se o comando mexe SÓ nesses caminhos, não alertar.
SAFE_PATHS = ("node_modules", ".next/", "dist/", "build/", "__pycache__",
              ".cache", ".turbo", "/tmp/", "coverage/", ".pytest_cache",
              ".venv", "venv/", "target/debug", ".git/objects")


def is_safe_target(command: str, matched_pattern: str) -> bool:
    """rm/clean apontando apenas para diretórios descartáveis = seguro."""
    if "rm " not in command and "clean" not in command:
        return False
    return any(sp in command for sp in SAFE_PATHS)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # sem input parseável → não interferir

    tool = payload.get("tool_name", "")
    if tool != "Bash":
        sys.exit(0)

    command = payload.get("tool_input", {}).get("command", "") or ""
    if not command.strip():
        sys.exit(0)

    for pattern, desc in DESTRUCTIVE:
        if re.search(pattern, command, re.IGNORECASE):
            if is_safe_target(command, pattern):
                continue
            reason = (
                f"⚠️ Comando destrutivo detectado: {desc}\n"
                f"   $ {command.strip()[:200]}\n"
                f"   Confirme que é intencional e reversível antes de prosseguir "
                f"(autonomous-execution.md: risco alto exige confirmação)."
            )
            out = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": reason,
                }
            }
            print(json.dumps(out))
            sys.exit(0)

    sys.exit(0)  # nada destrutivo → silencioso


if __name__ == "__main__":
    main()
