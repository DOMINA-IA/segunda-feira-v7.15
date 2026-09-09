#!/usr/bin/env python3
"""
trajectory-logger.py — PostToolUse hook que registra tool calls por sessão.

Propósito: capturar a sequência real de ferramentas usadas durante uma story,
permitindo que /trajectory-eval compare contra o trajectory esperado no AC.

Output: ~/.claude/.session-state/{session_id}-trajectory.jsonl
Cada linha: {"ts": ISO, "tool": "Edit", "agent": "@dev", "seq": N}

Só loga tools relevantes para trajectory (não loga Read/Grep/Glob — são
consultas, não ações). O filtro reduz ruído e torna a comparação mais limpa.

Ativado via PostToolUse em settings.json com matcher:
  "Bash|Edit|Write|MultiEdit|Agent|TaskCreate|TaskUpdate"
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

TRACKED_TOOLS = {
    "Bash", "Edit", "Write", "MultiEdit",
    "Agent", "TaskCreate", "TaskUpdate", "TaskStop",
}

STATE_DIR = Path.home() / ".claude" / ".session-state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

SESSION_ID = (
    os.environ.get("CLAUDE_SESSION_ID")
    or os.environ.get("SESSION_ID")
    or "default"
)

TRAJ_FILE = STATE_DIR / f"{SESSION_ID}-trajectory.jsonl"
SEQ_FILE  = STATE_DIR / f"{SESSION_ID}-traj-seq.txt"


def get_next_seq() -> int:
    try:
        return int(SEQ_FILE.read_text().strip()) + 1
    except Exception:
        return 1


def save_seq(n: int) -> None:
    SEQ_FILE.write_text(str(n))


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        event = json.loads(raw)
    except Exception:
        return 0

    tool = event.get("tool_name", "")
    if tool not in TRACKED_TOOLS:
        return 0

    seq = get_next_seq()

    entry = {
        "ts":    datetime.now(timezone.utc).isoformat(),
        "tool":  tool,
        "agent": os.environ.get("SF_ACTIVE_AGENT", "unknown"),
        "seq":   seq,
    }

    # Captura contexto extra por tipo
    tool_input = event.get("tool_input", {})
    if tool == "Bash":
        cmd = tool_input.get("command", "")
        # Resume só os primeiros 80 chars para não poluir
        entry["cmd"] = cmd[:80] if cmd else ""
    elif tool in ("Edit", "Write", "MultiEdit"):
        entry["file"] = tool_input.get("file_path", "")
    elif tool == "Agent":
        entry["subagent"] = tool_input.get("subagent_type", "")

    try:
        with open(TRAJ_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
        save_seq(seq)
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
