#!/usr/bin/env python3
"""autonomy-gate.py — Autonomia que se conquista (Segunda-feira).

Operacionaliza a matriz confidence × risco da rule autonomous-execution e a tabela
"Evolução da Autonomia" do Protocolo de Iniciativa, que existiam só como texto.

Dois modos (registrar os dois em settings.json):
  PreToolUse  (matcher Bash):  python3 ~/.claude/hooks/autonomy-gate.py gate
  PostToolUse (matcher Bash):  python3 ~/.claude/hooks/autonomy-gate.py learn

gate  → classifica o comando numa CLASSE de risco e devolve allow / ask / deny.
        - destrutivo  → deny sempre (freio de mão; espelha o `deny` do settings)
        - produção    → ask sempre (dinheiro, deploy, banco remoto, mensagem em massa:
                        "Limites absolutos" da rule — nunca sozinho)
        - demais      → allow se a classe já CONQUISTOU confiança; senão ask
learn → depois que o comando rodou, grava sucesso/falha da classe no livro-razão.
        Confiança = >= N execuções OK sem falha recente. Uma falha derruba a classe
        para "ask" de novo (autonomia sobe devagar e cai rápido).

Livro-razão: ~/.claude/.autonomy-ledger.json  (por classe: ok, fail, últimos 20)
Ajustes:     AUTONOMY_MIN_OK (default 5), AUTONOMY_MODE=off desliga o gate.
Falha do hook nunca bloqueia: qualquer exceção → sem decisão (o harness segue o padrão).
"""
import json
import os
import re
import sys
import time
from pathlib import Path

LEDGER = Path.home() / ".claude" / ".autonomy-ledger.json"
MIN_OK = int(os.environ.get("AUTONOMY_MIN_OK", "5"))
JANELA = 20

# Ordem importa: a primeira classe que casar vence.
CLASSES = [
    ("destrutivo", r"\brm\s+-[a-z]*r[a-z]*f|\brm\s+-[a-z]*f[a-z]*r|git\s+push\s+(--force|-f)\b|git\s+reset\s+--hard|git\s+clean\s+-f|git\s+branch\s+-D|DROP\s+(TABLE|DATABASE|SCHEMA)|mkfs|>\s*/dev/sd|chmod\s+-R\s+777\s+/|:\(\)\s*\{"),
    ("producao",   r"\bssh\b|\bscp\b|\brsync\b.*:|pm2\s+(restart|stop|delete|reload)|systemctl\s+(start|stop|restart|enable|disable)|docker\s+(rm|stop|kill|compose\s+down)|kubectl|terraform\s+apply|vercel\s+--prod|git\s+push\b|npm\s+publish|psql\b.*-h\s+(?!localhost|127)|curl\s+.*-X\s*(POST|PUT|PATCH|DELETE)|sendMessage|api\.telegram|graph\.facebook|crontab\s+-|sudo\b"),
    ("pacotes",    r"\b(npm|pnpm|yarn|pip3?|brew|apt(-get)?|cargo|gem)\s+(install|add|i|uninstall|remove|upgrade)\b"),
    ("git-local",  r"\bgit\s+(add|commit|checkout|switch|stash|merge|rebase|tag|branch|restore\s+--staged)\b"),
    ("build-test", r"\b(npm|pnpm|yarn)\s+(run|test|start|build)\b|\bnpx\b|\bpytest\b|\bpython3?\s+-m\s+(pytest|unittest)|\bmake\b|\bcargo\s+(build|test)|\bgo\s+(build|test)"),
    ("scripts",    r"\b(python3?|node|bash|sh|ruby|php)\s+\S+\.(py|js|sh|rb|php)\b"),
    ("escrita",    r"\b(mkdir|touch|cp|mv|tee|sed\s+-i|chmod|ln\s+-s)\b|>>?\s*[^&|]"),
    ("leitura",    r"^\s*(ls|cat|head|tail|wc|grep|rg|find|pwd|echo|which|env|date|df|du|stat|file|tree|git\s+(status|diff|log|show|branch\b(?!\s+-D))|python3?\s+-c|node\s+-e|curl\s+-s(?!.*-X)|jq|awk|sort|uniq|cut|tr|diff)\b"),
]


def classify(cmd: str) -> str:
    c = cmd.strip()
    for name, pat in CLASSES:
        if re.search(pat, c, re.I):
            return name
    return "outros"


def load():
    try:
        return json.loads(LEDGER.read_text())
    except Exception:
        return {"classes": {}, "created": time.strftime("%Y-%m-%d")}


def save(d):
    try:
        LEDGER.write_text(json.dumps(d, ensure_ascii=False, indent=1))
    except Exception:
        pass


def trusted(d, cls):
    c = d["classes"].get(cls, {})
    recent = c.get("recent", [])[-JANELA:]
    return sum(1 for r in recent if r == 1) >= MIN_OK and 0 not in recent


def gate(payload):
    cmd = (payload.get("tool_input") or {}).get("command", "") or ""
    if not cmd:
        return None
    cls = classify(cmd)
    d = load()
    if cls == "destrutivo":
        return "deny", f"[autonomy] classe destrutiva — nunca sozinho. Se for intencional, rode você mesmo no terminal."
    if cls == "producao":
        return "ask", "[autonomy] toca produção/dinheiro/rede externa — limite absoluto da rule: sempre pede."
    if cls == "leitura":
        return "allow", "[autonomy] leitura"
    if trusted(d, cls):
        n = sum(d["classes"][cls].get("recent", []))
        return "allow", f"[autonomy] classe '{cls}' conquistou confiança ({n} execuções OK)"
    c = d["classes"].get(cls, {})
    ok = sum(1 for r in c.get("recent", [])[-JANELA:] if r == 1)
    return "ask", f"[autonomy] classe '{cls}': {ok}/{MIN_OK} execuções OK para liberar sozinho"


def learn(payload):
    cmd = (payload.get("tool_input") or {}).get("command", "") or ""
    if not cmd:
        return
    cls = classify(cmd)
    if cls in ("destrutivo", "producao", "leitura"):
        return                      # essas classes têm política fixa; não aprendem
    resp = payload.get("tool_response") or {}
    out = json.dumps(resp, ensure_ascii=False).lower() if not isinstance(resp, str) else resp.lower()
    failed = bool(re.search(r"exit code [1-9]|\berror\b|traceback|command not found|permission denied|fatal:", out[:4000]))
    d = load()
    c = d["classes"].setdefault(cls, {"ok": 0, "fail": 0, "recent": []})
    c["ok" if not failed else "fail"] += 1
    c["recent"] = (c.get("recent", []) + [0 if failed else 1])[-JANELA:]
    c["last"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    save(d)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "gate"
    if os.environ.get("AUTONOMY_MODE", "on") == "off":
        return 0
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    if payload.get("tool_name") not in (None, "Bash"):
        return 0
    try:
        if mode == "learn":
            learn(payload)
            return 0
        r = gate(payload)
        if not r:
            return 0
        decision, reason = r
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                 "permissionDecision": decision,
                                                 "permissionDecisionReason": reason}}, ensure_ascii=False))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
