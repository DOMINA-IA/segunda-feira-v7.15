#!/usr/bin/env python3
"""
dispatch-write-edit.py — Dispatcher unificado para hooks PreToolUse (matcher Write|Edit).

Substitui, em UM único processo Python, a execução em cadeia de 3 hooks hoje
registrados separadamente em settings.json (cada um seu próprio `python3 ...`
subprocesso):

    1. check-acentos.py   (matcher "Write|Edit")
    2. model-watchdog.py  (matcher "Bash|Edit|Write|MultiEdit")
    3. freeze.py          (matcher "Write|Edit|MultiEdit")

Ordem preservada EXATAMENTE igual à ordem de declaração hoje em
~/.claude/settings.json (bloco "PreToolUse").

Como cada estágio é executado
------------------------------
Cada hook original é rodado via `runpy.run_path(script, run_name="__main__")`
— ou seja, o arquivo .py original roda exatamente como se tivesse sido
chamado via `python3 hook_original.py`, sem nenhuma reescrita/duplicação de
lógica. Isso preserva 100% do comportamento original, inclusive leitura e
escrita de estado em ~/.claude/.session-state/ (usado por model-watchdog.py
e freeze.py).

stdin é lido UMA VEZ pelo dispatcher e "repassado" a cada estágio via
io.StringIO — cada hook original chama json.load(sys.stdin)/sys.stdin.read()
internamente sem saber que está rodando dentro do dispatcher.

Semântica de bloqueio preservada
---------------------------------
- check-acentos.py bloqueia imprimindo `{"decision": "block", "reason": ...}`
  no stdout (exit sempre 0 — a decisão vive no JSON, não no exit code).
- freeze.py bloqueia (deny) imprimindo
  `{"hookSpecificOutput": {"permissionDecision": "deny", ...}}` no stdout
  (exit sempre 0).
- model-watchdog.py NUNCA bloqueia — só escreve aviso em stderr e retorna 0
  sem nada no stdout.

Regra "primeiro que bloquear, bloqueia" (short-circuit): os estágios rodam
em sequência; assim que um estágio produz QUALQUER saída não-vazia em
stdout (ou seja, tomou uma decisão), essa saída é repassada verbatim ao
stdout real do dispatcher e os estágios seguintes NÃO rodam. Isso é
necessário porque o dispatcher é UM hook aos olhos do harness — só pode
emitir UMA decisão de permissão por invocação — e replica a ordem
declarada em settings.json (check-acentos primeiro, depois model-watchdog,
depois freeze).

stderr de cada estágio executado é acumulado e repassado ao stderr real do
dispatcher (na ordem em que os estágios rodaram), para não perder avisos
como os do model-watchdog.

Exit code final: sempre 0 (nenhum dos 3 hooks originais usa exit code != 0
para bloquear — todos usam JSON no stdout).
"""
import io
import runpy
import sys
import traceback
from pathlib import Path

HOOKS_DIR = Path.home() / ".claude" / "hooks"

# Ordem EXATA de declaração hoje em settings.json para tool_name Write|Edit:
#   1) matcher "Write|Edit"              -> check-acentos.py
#   2) matcher "Bash|Edit|Write|MultiEdit" -> model-watchdog.py
#   3) matcher "Write|Edit|MultiEdit"    -> freeze.py
STAGES = [
    HOOKS_DIR / "check-acentos.py",
    HOOKS_DIR / "model-watchdog.py",
    HOOKS_DIR / "freeze.py",
]


def run_stage(script_path: Path, raw_stdin: str) -> tuple[str, str]:
    """Executa um hook original como se fosse `python3 script_path`,
    alimentando raw_stdin via sys.stdin e capturando stdout/stderr.

    Retorna (stdout_capturado, stderr_capturado). Nunca propaga SystemExit
    nem exceções — hook original que crasha é tratado como "sem decisão"
    (fail-open, igual ao comportamento de cada hook original em seus
    próprios try/except que terminam em sys.exit(0)).
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
            # Hook original sumiu — não interferir (fail-open).
            continue

        stdout, stderr = run_stage(script_path, raw_stdin)

        if stderr:
            sys.stderr.write(stderr)

        if stdout.strip():
            # Este estágio tomou uma decisão (block/deny/ask) — short-circuit:
            # repassa a saída verbatim e não roda os estágios seguintes.
            sys.stdout.write(stdout)
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
