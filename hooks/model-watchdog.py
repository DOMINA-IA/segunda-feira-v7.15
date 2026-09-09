#!/usr/bin/env python3
"""
model-watchdog.py — PreToolUse hook que avisa sobre modelo inadequado

Origem: Opção C da decisão CLI Model Default (cli-model-default.md).
Detecta padrão "trabalho mecânico em sessão Opus" e sugere /model sonnet.
Funciona como CONSCIÊNCIA de custo em runtime.

Lógica:
1. Lê estado da sessão atual (counter de tools em ~/.claude/.session-state/)
2. Se últimas 5 tool calls forem ≥3 de Bash/Edit/Write/MultiEdit
3. E modelo atual for Opus (heurística via env CLAUDE_MODEL ou nome do processo)
4. Injeta warning sugerindo /model sonnet

Anti-noise:
- Só avisa uma vez por sessão (state flag)
- Threshold ≥5 tool calls antes de avisar (não polui início)
- Silencioso se sessão tem mix Read/Grep (raciocínio)
"""
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

STATE_DIR = Path.home() / ".claude" / ".session-state"
STATE_DIR.mkdir(parents=True, exist_ok=True)
SESSION_ID = os.environ.get("CLAUDE_SESSION_ID") or os.environ.get("SESSION_ID") or "default"
STATE_FILE = STATE_DIR / f"{SESSION_ID}-tools.json"
WARNED_FILE = STATE_DIR / f"{SESSION_ID}-warned.flag"
MAX_AGE_HOURS = 6  # state mais velho que isso é nova sessão

DEV_TOOLS = {"Bash", "Edit", "Write", "MultiEdit"}
REASONING_TOOLS = {"Read", "Grep", "Glob", "AskUserQuestion"}
THRESHOLD_TOOLS_BEFORE_WARN = 5  # esperar acumular antes de avisar
DEV_RATIO_TRIGGER = 0.6  # 60%+ das últimas tools são dev


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"tools": [], "started_at": time.time()}
    try:
        data = json.loads(STATE_FILE.read_text())
        # Reset se sessão muito velha
        if time.time() - data.get("started_at", 0) > MAX_AGE_HOURS * 3600:
            return {"tools": [], "started_at": time.time()}
        return data
    except (OSError, json.JSONDecodeError):
        return {"tools": [], "started_at": time.time()}


def save_state(data: dict):
    try:
        STATE_FILE.write_text(json.dumps(data, ensure_ascii=False))
    except OSError:
        pass


def has_warned() -> bool:
    return WARNED_FILE.exists()


def mark_warned():
    try:
        WARNED_FILE.touch()
    except OSError:
        pass


def is_opus_session() -> bool:
    """Heurística para detectar se sessão atual é Opus.

    Não há env var canônica do Claude Code expondo o modelo ativo.
    Default: assume Opus se settings.json NÃO declara sonnet/haiku explicitamente.
    """
    settings_path = Path.home() / ".claude" / "settings.json"
    if not settings_path.exists():
        return True  # conservador: assume Opus se não souber
    try:
        s = json.loads(settings_path.read_text())
        model = s.get("model", "").lower()
        if model in ("sonnet", "haiku"):
            return False
        return True  # opus ou não declarado
    except (OSError, json.JSONDecodeError):
        return True


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        event = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return 0

    tool = event.get("tool_name", "")
    if not tool:
        return 0

    state = load_state()
    state["tools"].append(tool)
    # Manter só as últimas 20 para análise
    state["tools"] = state["tools"][-20:]
    save_state(state)

    # Não avisar se já avisou nesta sessão
    if has_warned():
        return 0

    # Não avisar se tem poucas tool calls ainda
    if len(state["tools"]) < THRESHOLD_TOOLS_BEFORE_WARN:
        return 0

    # Só avisar se modelo atual é Opus (caso contrário não há economia possível)
    if not is_opus_session():
        return 0

    # Calcular ratio das últimas 10 tool calls
    recent = state["tools"][-10:]
    counter = Counter(recent)
    dev_count = sum(counter[t] for t in DEV_TOOLS)
    dev_ratio = dev_count / len(recent) if recent else 0

    if dev_ratio < DEV_RATIO_TRIGGER:
        return 0

    # Disparo: padrão dev em sessão Opus
    top_tools = ", ".join(f"{t}:{n}" for t, n in counter.most_common(3))
    msg = f"""
⚠️  MODEL WATCHDOG — Padrão dev detectado em sessão Opus
   Últimas 10 tools: {top_tools}
   Dev ratio: {dev_ratio:.0%} (Bash/Edit/Write/MultiEdit)

   Recomendação: trocar para Sonnet via comando `/model sonnet`
   Economia esperada: ~90% no custo das próximas calls mecânicas.

   Detalhes: ~/cortex/vault/decisions/cli-model-default.md
   (Este aviso só aparece UMA vez por sessão.)
"""
    print(msg, file=sys.stderr)
    mark_warned()
    return 0


if __name__ == "__main__":
    sys.exit(main())
