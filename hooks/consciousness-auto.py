#!/usr/bin/env python3
"""
consciousness-auto.py — Hook PostToolUse para registro automático de episódios.

Detecta conclusão de tarefas significativas a partir do output de ferramentas
e registra episódios no Consciousness Engine sem depender do agente.

Triggers:
- TaskUpdate com status=completed → episódio de tarefa concluída
- Bash com git commit → episódio de commit
- Bash com npm run test/lint/typecheck que falha → episódio de falha

Roda como PostToolUse hook no Claude Code.
"""

import json
import os
import subprocess
import sys
import re
from datetime import datetime, timezone
from pathlib import Path

CONSCIOUSNESS_DIR = Path.home() / "consciousness"
RECORD_SCRIPT = CONSCIOUSNESS_DIR / "scripts" / "record-episode.sh"
EPISODIC_DIR = CONSCIOUSNESS_DIR / "memory" / "episodic"
ACTIVE_AGENT_FILE = CONSCIOUSNESS_DIR / "memory" / ".active-agent"

# Mapeamento de patterns → agente provável
AGENT_SIGNALS = {
    "@traffic": ["campanha", "cpl", "meta ads", "ads", "criativo", "tráfego", "leads", "orçamento"],
    "@content": ["post", "carrossel", "reels", "legenda", "instagram", "conteúdo", "agendamento"],
    "@dev": ["npm", "git", "typescript", "component", "api", "endpoint", "refactor", "bug", "fix"],
    "@devops": ["deploy", "git push", "ci/cd", "pipeline", "docker", "pm2"],
    "@qa": ["test", "lint", "typecheck", "quality", "review", "coverage"],
    "@analyst": ["relatório", "métricas", "dados", "análise", "dashboard", "kpi"],
    "@architect": ["arquitetura", "schema", "design", "padrão", "integração"],
    "@copywriter": ["copy", "headline", "cta", "persuasão", "aida", "pas"],
    "@offer-engineer": ["oferta", "preço", "garantia", "bônus", "stack de valor"],
    "@data-engineer": ["sql", "migration", "rls", "index", "query", "supabase"],
}


def detect_active_agent(context: str) -> str:
    """Detecta o agente mais provável baseado no contexto combinado."""
    # 1. Checar arquivo de sessão (escrito pelo skill de ativação de agente)
    if ACTIVE_AGENT_FILE.exists():
        try:
            agent = ACTIVE_AGENT_FILE.read_text().strip()
            if agent.startswith("@"):
                return agent
        except Exception:
            pass

    # 2. Inferir do contexto por keyword matching
    context_lower = context.lower()
    scores = {}
    for agent, keywords in AGENT_SIGNALS.items():
        score = sum(1 for kw in keywords if kw in context_lower)
        if score > 0:
            scores[agent] = score

    if scores:
        return max(scores, key=scores.get)

    # 3. Default
    return "@sf-master"


def record_episode(agent: str, ep_type: str, summary: str, result: str,
                   valence: float, intensity: float,
                   worked: str = "", failed: str = "", heuristic: str = ""):
    """Registra episódio via record-episode.sh."""
    if not RECORD_SCRIPT.exists():
        return

    args = [
        "bash", str(RECORD_SCRIPT),
        "--agent", agent,
        "--type", ep_type,
        "--summary", summary[:200],
        "--result", result,
        "--valence", str(valence),
        "--intensity", str(intensity),
    ]
    if worked:
        args.extend(["--worked", worked[:150]])
    if failed:
        args.extend(["--failed", failed[:150]])
    if heuristic:
        args.extend(["--heuristic", heuristic[:200]])

    try:
        subprocess.run(args, capture_output=True, timeout=5)
    except Exception:
        pass


def detect_from_tool_input(tool_name: str, tool_input: str):
    """Detecta padrões significativos no input da ferramenta."""

    # TaskUpdate com completed
    if tool_name == "TaskUpdate":
        try:
            data = json.loads(tool_input) if isinstance(tool_input, str) else tool_input
            if data.get("status") == "completed":
                subject = data.get("subject", "tarefa desconhecida")
                agent = detect_active_agent(subject)
                record_episode(
                    agent=agent,
                    ep_type="task_completed",
                    summary=f"Tarefa completada: {subject}",
                    result="success",
                    valence=0.6,
                    intensity=0.4,
                )
                return True
        except (json.JSONDecodeError, TypeError):
            pass

    return False


def detect_from_task_tool(tool_name: str, tool_input, tool_output: str):
    """Registra episódio quando Claude invoca subagent via Task/Agent tool.
    Resolve a quebra detectada em 09-Mai-2026: agentes invocados via Task
    não estavam chamando record-episode.sh, deixando o Consciousness Engine
    sub-povoado e quebrando o aprendizado entre invocações."""

    if tool_name not in ("Task", "Agent"):
        return False

    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except (json.JSONDecodeError, TypeError):
            return False
    if not isinstance(tool_input, dict):
        return False

    subagent = tool_input.get("subagent_type", "")
    description = tool_input.get("description", "") or "subtask"
    if not subagent or subagent in ("general-purpose", "Explore", "Plan",
                                    "claude-code-guide", "statusline-setup"):
        return False

    output_str = (tool_output or "")
    out_lower = output_str.lower()[:1000]
    if any(s in out_lower for s in ["traceback", "inputvalidationerror",
                                    "error:", "failed", "exception"]):
        result, valence, ep_type = "failure", -0.4, "task_failed"
    else:
        result, valence, ep_type = "success", 0.5, "task_completed"

    record_episode(
        agent=f"@{subagent}",
        ep_type=ep_type,
        summary=f"[via Task] {description}"[:200],
        result=result,
        valence=valence,
        intensity=0.4,
    )
    return True


def detect_from_tool_output(tool_name: str, tool_input: str, tool_output: str):
    """Detecta padrões significativos no output da ferramenta."""

    if tool_name != "Bash":
        return False

    input_lower = tool_input.lower() if tool_input else ""
    output_lower = tool_output.lower() if tool_output else ""

    # git commit bem sucedido
    if "git commit" in input_lower and "create mode" in output_lower or "file changed" in output_lower:
        # Extrair mensagem do commit
        commit_match = re.search(r'-m\s+["\'](.+?)["\']', tool_input)
        msg = commit_match.group(1)[:100] if commit_match else "commit realizado"
        record_episode(
            agent="@dev",
            ep_type="task_completed",
            summary=f"Commit: {msg}",
            result="success",
            valence=0.5,
            intensity=0.3,
        )
        return True

    # Test/lint/typecheck que falhou
    if any(cmd in input_lower for cmd in ["npm run test", "npm run lint", "npm run typecheck", "pytest"]):
        if any(fail in output_lower for fail in ["error", "failed", "failure", "exit code 1"]):
            record_episode(
                agent="@dev",
                ep_type="task_failed",
                summary=f"Falha em verificação: {tool_input[:80]}",
                result="failure",
                valence=-0.5,
                intensity=0.6,
                failed=tool_output[:150] if tool_output else "",
            )
            return True
        elif any(ok in output_lower for ok in ["passed", "success", "0 error", "0 warning"]):
            record_episode(
                agent="@qa",
                ep_type="task_completed",
                summary=f"Verificação passou: {tool_input[:80]}",
                result="success",
                valence=0.5,
                intensity=0.3,
            )
            return True

    # Deploy / push (se detectado)
    if "git push" in input_lower and "error" not in output_lower:
        record_episode(
            agent="@devops",
            ep_type="task_completed",
            summary=f"Push realizado: {tool_input[:80]}",
            result="success",
            valence=0.7,
            intensity=0.6,
        )
        return True

    return False


def main():
    """Entry point — lê contexto do hook via stdin/env."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return

        data = json.loads(raw)
        tool_name = data.get("tool_name", "")
        tool_input = json.dumps(data.get("tool_input", {})) if isinstance(data.get("tool_input"), dict) else str(data.get("tool_input", ""))
        tool_output = str(data.get("tool_output", ""))

        # Salvar contexto combinado para detecção de agente (usado por detect_active_agent)
        combined_context = f"{tool_input} {tool_output}"
        os.environ["_CONSCIOUSNESS_CONTEXT"] = combined_context[:500]

        # Tentar detectar do input primeiro (TaskUpdate)
        if detect_from_tool_input(tool_name, data.get("tool_input", {})):
            return

        # Task/Agent tool — invocação de subagent
        if detect_from_task_tool(tool_name, data.get("tool_input", {}), tool_output):
            return

        # Tentar detectar do output (Bash)
        detect_from_tool_output(tool_name, tool_input, tool_output)

    except Exception:
        # Hook nunca deve bloquear — falha silenciosa
        pass


if __name__ == "__main__":
    main()
