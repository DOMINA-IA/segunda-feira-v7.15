#!/usr/bin/env python3
"""
dispatch-bash.py — Dispatcher unificado para hooks PreToolUse (matcher Bash).

Substitui, em UM único processo Python, a execução em cadeia de 2 hooks hoje
registrados separadamente em settings.json:

    1. model-watchdog.py  (matcher "Bash|Edit|Write|MultiEdit")
    2. careful.py         (matcher "Bash")

Ordem preservada EXATAMENTE igual à ordem de declaração hoje em
~/.claude/settings.json (bloco "PreToolUse").

Mesmo mecanismo de execução, repasse de stdin e short-circuit descritos em
dispatch-write-edit.py — ver aquele arquivo para o racional completo.

Semântica de bloqueio preservada
---------------------------------
- model-watchdog.py NUNCA bloqueia — só escreve aviso em stderr (uma vez por
  sessão) e retorna 0 sem nada no stdout.
- careful.py eleva para confirmação humana (não bloqueia definitivamente)
  imprimindo `{"hookSpecificOutput": {"permissionDecision": "ask", ...}}` no
  stdout quando o comando Bash casa um padrão destrutivo (exit sempre 0).

Regra "primeiro que bloquear, bloqueia" (short-circuit): como model-watchdog
nunca produz stdout, na prática ele sempre roda por completo (side effects:
atualiza contador de tools em ~/.claude/.session-state/) e depois careful.py
roda e decide. Se no futuro model-watchdog passar a emitir decisão, o
short-circuit entra em vigor automaticamente.

Exit code final: sempre 0.
"""
import io
import runpy
import sys
import traceback
from pathlib import Path

HOOKS_DIR = Path.home() / ".claude" / "hooks"

# Ordem EXATA de declaração hoje em settings.json para tool_name Bash:
#   1) matcher "Bash|Edit|Write|MultiEdit" -> model-watchdog.py
#   2) matcher "Bash"                      -> careful.py
STAGES = [
    HOOKS_DIR / "model-watchdog.py",
    HOOKS_DIR / "careful.py",
]


def run_stage(script_path: Path, raw_stdin: str) -> tuple[str, str]:
    """Executa um hook original como se fosse `python3 script_path`,
    alimentando raw_stdin via sys.stdin e capturando stdout/stderr.

    Retorna (stdout_capturado, stderr_capturado). Nunca propaga SystemExit
    nem exceções — hook original que crasha é tratado como "sem decisão"
    (fail-open, igual ao comportamento de cada hook original).
    """
    old_stdin, old_stdout, old_stderr = sys.stdin, sys.stdout, sys.stderr
    sys.stdin = io.StringIO(raw_stdin)
    out_buf, err_buf = io.StringIO(), io.StringIO()
    sys.stdout = out_buf
    sys.stderr = err_buf
    try:
        try:
            runpy.run_path(str(script_path), run_name="__main__")
        except SystemExit:
            pass
        except Exception:
            traceback.print_exc(file=err_buf)
    finally:
        sys.stdin, sys.stdout, sys.stderr = old_stdin, old_stdout, old_stderr
    return out_buf.getvalue(), err_buf.getvalue()


def main() -> int:
    raw_stdin = sys.stdin.read()

    for script_path in STAGES:
        if not script_path.exists():
            continue

        stdout, stderr = run_stage(script_path, raw_stdin)

        if stderr:
            sys.stderr.write(stderr)

        if stdout.strip():
            sys.stdout.write(stdout)
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
