#!/usr/bin/env python3
"""
slop-scan.py — Detector de "AI slop" (design + código + copy) como Tier 0 ($0).

Absorvido do /slop-scan do gstack (Garry Tan) em 26-Jun-2026.
A política vive em DADO editável (~/.claude/slop-blacklist.json), não no código.
Cruza com visual-rendering-safety.md ("memória esquece, código não").

Uso:
  slop-scan.py <arquivo>              # escaneia um arquivo
  slop-scan.py <diretório>           # escaneia recursivamente
  slop-scan.py --diff                 # só arquivos do git diff, só findings NOVOS
  slop-scan.py --diff --staged        # idem, staged
  slop-scan.py <alvo> --severity alto # filtra por severidade mínima

Saída: arquivo:linha [severidade] id — descrição
Exit code: 0 sempre (é relatório); use --strict para exit 1 se houver findings 'alto'.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BLACKLIST = Path.home() / ".claude" / "slop-blacklist.json"
SCAN_EXT = {".html", ".htm", ".css", ".js", ".jsx", ".ts", ".tsx",
            ".py", ".md", ".txt", ".vue", ".svelte"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "__pycache__",
             ".venv", "venv", ".cache", "vendor", "coverage"}
SEV_ORDER = {"info": 0, "baixo": 1, "medio": 2, "alto": 3}


def to_python_regex(pattern: str) -> str:
    """Converte \\x{HHHH} (PCRE) para \\U........ (Python re)."""
    return re.sub(r"\\x\{([0-9A-Fa-f]+)\}",
                  lambda m: "\\U" + m.group(1).zfill(8), pattern)


def load_rules():
    data = json.loads(BLACKLIST.read_text())
    rules = []
    for category in ("design_slop", "code_slop", "copy_slop"):
        for r in data.get(category, []):
            flags = 0
            if "i" in r.get("flags", ""):
                flags |= re.IGNORECASE
            if "u" in r.get("flags", ""):
                flags |= re.UNICODE
            try:
                compiled = re.compile(to_python_regex(r["regex"]), flags)
            except re.error as e:
                print(f"  [aviso] regex inválida '{r['id']}': {e}", file=sys.stderr)
                continue
            rules.append({"id": r["id"], "re": compiled,
                          "desc": r["desc"], "sev": r.get("severity", "baixo"),
                          "cat": category})
    return rules


def scan_file(path, rules, min_sev=0):
    findings = []
    try:
        lines = Path(path).read_text(errors="ignore").splitlines()
    except Exception:
        return findings
    for n, line in enumerate(lines, 1):
        for rule in rules:
            if SEV_ORDER.get(rule["sev"], 1) < min_sev:
                continue
            if rule["re"].search(line):
                findings.append((str(path), n, rule["sev"], rule["id"],
                                 rule["desc"], line.strip()[:80]))
    return findings


def collect_files(target):
    p = Path(target)
    if p.is_file():
        return [p]
    files = []
    for root, dirs, names in os.walk(p):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            if Path(name).suffix.lower() in SCAN_EXT:
                files.append(Path(root) / name)
    return files


def git_diff_files(staged=False):
    cmd = ["git", "diff", "--name-only"] + (["--cached"] if staged else [])
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    except Exception:
        return []
    return [Path(f) for f in out.splitlines()
            if Path(f).suffix.lower() in SCAN_EXT and Path(f).exists()]


def baseline_findings(rules, min_sev):
    """Findings na base branch (HEAD) — para modo --diff só reportar NOVOS.
    Strip de número de linha: compara por (arquivo, id, conteúdo)."""
    seen = set()
    try:
        base = subprocess.run(["git", "stash", "list"], capture_output=True, text=True)
    except Exception:
        return seen
    return seen  # simplificação: comparação por conteúdo no caller


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__.strip().split("\n\n")[2])  # bloco "Uso"
        sys.exit(0)

    diff_mode = "--diff" in args
    staged = "--staged" in args
    strict = "--strict" in args
    min_sev = 0
    if "--severity" in args:
        i = args.index("--severity")
        min_sev = SEV_ORDER.get(args[i + 1], 0) if i + 1 < len(args) else 0

    rules = load_rules()
    positional = [a for a in args if not a.startswith("--")
                  and a not in ("alto", "medio", "baixo", "info")]

    if diff_mode:
        files = git_diff_files(staged)
        if not files:
            print("Nenhum arquivo escaneável no diff.")
            sys.exit(0)
    else:
        target = positional[0] if positional else "."
        files = collect_files(target)

    all_findings = []
    for f in files:
        all_findings.extend(scan_file(f, rules, min_sev))

    # modo --diff: só NEW findings — remove os que já existem na base (por conteúdo)
    if diff_mode:
        base_set = set()
        try:
            changed = {str(f) for f in files}
            show = subprocess.run(["git", "show", "HEAD:" + "", ], capture_output=True, text=True)
        except Exception:
            pass
        new_findings = []
        for f in files:
            try:
                old = subprocess.run(["git", "show", f"HEAD:{f}"],
                                     capture_output=True, text=True)
                old_lines = set(l.strip() for l in old.stdout.splitlines()) if old.returncode == 0 else set()
            except Exception:
                old_lines = set()
            for fd in [x for x in all_findings if x[0] == str(f)]:
                if fd[5] not in old_lines:  # conteúdo da linha não existia na base
                    new_findings.append(fd)
        all_findings = new_findings

    if not all_findings:
        print("✅ Nenhum slop detectado." + (" (apenas NEW no diff)" if diff_mode else ""))
        sys.exit(0)

    # ordena por severidade desc
    all_findings.sort(key=lambda x: -SEV_ORDER.get(x[2], 0))
    icon = {"alto": "🔴", "medio": "🟡", "baixo": "⚪", "info": "ℹ️"}
    counts = {}
    for path, n, sev, rid, desc, snippet in all_findings:
        counts[sev] = counts.get(sev, 0) + 1
        print(f"{icon.get(sev,'•')} {path}:{n} [{sev}] {rid} — {desc}")
    print(f"\n{len(all_findings)} achado(s): " +
          ", ".join(f"{v} {k}" for k, v in sorted(counts.items(), key=lambda x: -SEV_ORDER.get(x[0],0))))

    if strict and counts.get("alto", 0) > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
