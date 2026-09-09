#!/usr/bin/env python3
"""
usage-telemetry.py — PostToolUse hook que registra invocações de skills e agentes.

Propósito: alimentar telemetria de uso real (quem/o-que é invocado e quando),
pré-requisito para a poda informada de skills/agentes órfãos (Sprint 3, Grupo D).

Output: ~/cortex/skills-usage.jsonl
Cada linha: {"ts": ISO, "tool": "Skill"|"Agent", "name": "...", "session": "..."}

Só loga tool_name == "Skill" (nome em tool_input.skill) ou
tool_name in ("Agent", "Task") (nome em tool_input.subagent_type). Qualquer
outra tool é ignorada silenciosamente.

Fail-open total: qualquer exceção resulta em exit 0 sem output — o hook nunca
pode bloquear ou atrasar o fluxo do agente. Imports mínimos (json + os) para
latência mínima.

Ativado via PostToolUse em settings.json com matcher:
  "Skill|Task|Agent"
(ver TELEMETRY-WIRING.md para o snippet exato)
"""
import json
import os
import sys

# USAGE_TELEMETRY_FILE permite apontar para um jsonl de teste sem tocar no
# arquivo real — usado pelos testes sintéticos (D2) e por quem quiser simular
# em isolamento. Sem a env var, cai no path de produção.
USAGE_FILE = os.environ.get(
    "USAGE_TELEMETRY_FILE", os.path.expanduser("~/cortex/skills-usage.jsonl")
)

# Tools cujo nome de invocação queremos capturar e o campo do tool_input
# onde esse nome vive.
NAME_FIELD_BY_TOOL = {
    "Skill": "skill",
    "Agent": "subagent_type",
    "Task": "subagent_type",
}


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        event = json.loads(raw)

        tool = event.get("tool_name", "")
        field = NAME_FIELD_BY_TOOL.get(tool)
        if not field:
            return 0

        tool_input = event.get("tool_input", {})
        if not isinstance(tool_input, dict):
            return 0

        name = tool_input.get(field, "")
        if not name:
            return 0

        entry = {
            "ts": _now_iso(),
            "tool": tool,
            "name": name,
            "session": os.environ.get("CLAUDE_SESSION_ID", ""),
        }

        os.makedirs(os.path.dirname(USAGE_FILE), exist_ok=True)
        with open(USAGE_FILE, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    except Exception:
        # Hook nunca deve bloquear — falha silenciosa (fail-open)
        pass

    return 0


def _now_iso() -> str:
    # Import local ao invés de global — mantém o caminho quente (skill/agent
    # não encontrado) livre de custo de import.
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    sys.exit(main())
