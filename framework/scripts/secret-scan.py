#!/usr/bin/env python3
"""secret-scan — procura credencial em texto plano onde a rule credentials-handling proíbe.
Reporta LOCAL e TIPO, nunca o valor. Exit 1 se achar algo. Usado pelo framework_health_check."""
import re, sys, json
from pathlib import Path
HOME = Path.home()
ROOTS = {
    "vault": HOME/"cortex/vault", "briefings": HOME/"cortex/briefings",
    "memory": HOME/".claude/projects/-HOME-/memory",
    "skills": HOME/".claude/skills", "agents": HOME/".claude/agents",
    "commands": HOME/".claude/commands", "rules": HOME/".claude/rules",
    "scripts": HOME/"framework/scripts", "broadcast": HOME/"broadcast",
    "episodic": HOME/"consciousness/memory", "CLAUDE.md": HOME/".claude/CLAUDE.md",
    "history": HOME/".claude/history.jsonl", "file-history": HOME/".claude/file-history", "archive": HOME/".claude/_archive",
    "projetos-runtime": HOME/"projetos/utm-manager", "projetos-desafio": HOME/"projetos/desafio", "projetos-${REDIGIDO}": HOME/"projetos/${REDIGIDO}",
}
PATS = {
    "openai/anthropic-key": re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}"),
    "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    "slack-token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    "aws-key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "meta-token": re.compile(r"\bEAA[A-Za-z0-9]{40,}"),
    "telegram-bot": re.compile(r"\b\d{8,10}:AA[A-Za-z0-9_-]{30,}"),
    "private-key": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    "url-creds": re.compile(r"[a-z]+://[A-Za-z0-9._%-]+:([^@\s/<\[]{4,})@[A-Za-z0-9.-]+"),
    "password-assign": re.compile(r"(?i)\b(?:password|senha|passwd|pass|pwd)\s*[:=]\s*['\"]?([^\s'\"`,;)<\[]{6,})"),
    "sshpass": re.compile(r"sshpass\s+-p\s+['\"]?([^\s'\"]{4,})"),
}
PLACEHOLDER = re.compile(r"(?i)^(senha|password|sua_senha|x{3,}|\*{3,}|<.*>|\{.*\}|\$\{?\w+\}?|redacted|removid[ao]|placeholder|\.\.\.|example|changeme|none|null|true|false|string|secret|token|key|value|required|optional|1password|ver\b.*|em\b.*)$")
# Só suprime quando o VALOR é ponteiro/placeholder ou o trecho é claramente código lendo env
# (07-Set: a palavra ".env" a 80 chars de distância escondia uma senha real).
CTX_OK = re.compile(r"(?i)(ver ~/_secrets|em ~/_secrets|1password|getenv\(|process\.env\.|os\.environ|\$\{?[A-Z_]{4,}\}?|REDACTED|<senha|<token|placeholder)")
SKIP = {".git", "__pycache__", "node_modules", "_pre-credclean"}
EXT = {".md", ".json", ".jsonl", ".sh", ".py", ".yaml", ".yml", ".txt", ".env", ".js", ".ts", ".php", ""}
def scan():
    hits = []
    for label, root in ROOTS.items():
        files = [root] if root.is_file() else ([p for p in root.rglob("*") if p.is_file() and not any(s in p.parts for s in SKIP) and p.suffix in EXT] if root.exists() else [])
        for f in files:
            if label.startswith("projetos-") and f.name.startswith(".env"):
                continue      # .env (600) é o lugar sancionado da credencial; o que se acusa é código
            try: txt = f.read_text(errors="ignore")
            except Exception: continue
            for name, p in PATS.items():
                for m in p.finditer(txt):
                    val = m.group(1) if m.groups() else m.group(0)
                    if PLACEHOLDER.match(val) or val.startswith("/") or re.fullmatch(r"[A-Z][a-z]+", val): continue
                    if "REDACTED" in txt[m.start():m.end() + 40] or val.startswith("[REDACTED"): continue   # já redigido
                    if name in ("password-assign", "url-creds") and CTX_OK.search(txt[max(0, m.start()-80):m.end()+40]): continue
                    hits.append({"area": label, "file": str(f.relative_to(HOME)), "type": name, "line": txt[:m.start()].count("\n")+1})
    return hits
if __name__ == "__main__":
    hits = scan()
    if "--json" in sys.argv: print(json.dumps(hits, ensure_ascii=False, indent=1))
    else:
        for h in hits: print(f"  [{h['area']}] {h['type']:18s} ~/{h['file']}:{h['line']}")
        print(f"{len(hits)} ocorrência(s) de credencial em texto plano")
    sys.exit(1 if hits else 0)
