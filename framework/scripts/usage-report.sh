#!/bin/bash
# usage-report.sh — Relatório de telemetria de invocação de skills/agentes.
# Lê ~/cortex/skills-usage.jsonl (alimentado pelo hook usage-telemetry.py) e imprime:
#   1. Ranking de uso por nome nos últimos 30 dias
#   2. Skills que nunca foram invocadas (diff contra ~/.claude/skills/*.md)
#   3. Aviso de dados insuficientes se o histórico tiver menos de 28 dias
# Pré-requisito da poda informada (Sprint 3, Grupo D — telemetria antes de podar).
#
# Uso: bash ~/framework/scripts/usage-report.sh [path-alternativo-do-jsonl]
#   Sem argumento usa o path real de produção. Passe um path alternativo
#   (ex.: jsonl sintético) para testar sem tocar nos dados reais.

USAGE_FILE="${1:-$HOME/cortex/skills-usage.jsonl}"
SKILLS_DIR="$HOME/.claude/skills"

if [ ! -f "$USAGE_FILE" ]; then
    echo "usage-report: arquivo não encontrado — $USAGE_FILE"
    echo "(ainda não há telemetria coletada; nada para reportar)"
    exit 0
fi

python3 << PYTHON_SCRIPT
import json
import os
from datetime import datetime, timedelta, timezone

USAGE_FILE = "$USAGE_FILE"
SKILLS_DIR = "$SKILLS_DIR"

# ─── Colors ──────────────────────────────────────────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

def parse_ts(ts_str):
    """Parse timestamp ISO, retorna datetime aware em UTC (ou None se inválido)."""
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None

# ─── Carrega entradas (fail-open por linha — uma linha corrompida não derruba o relatório) ──
entries = []
skipped = 0
with open(USAGE_FILE) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        entry["_dt"] = parse_ts(entry.get("ts", ""))
        entries.append(entry)

print(f"{BOLD}{CYAN}═══ Usage Report — Telemetria de Skills/Agentes ═══{RESET}")
print(f"{DIM}Fonte: {USAGE_FILE}{RESET}")
print(f"{DIM}Total de linhas lidas: {len(entries)}{f' ({skipped} corrompidas ignoradas)' if skipped else ''}{RESET}")
print()

if not entries:
    print(f"{YELLOW}Nenhuma entrada válida no arquivo — nada para reportar.{RESET}")
    raise SystemExit(0)

now = datetime.now(timezone.utc)
cutoff_30d = now - timedelta(days=30)

# ─── 1. Ranking de uso por nome (últimos 30 dias) ────────────────────────────
recent = [e for e in entries if e["_dt"] and e["_dt"] >= cutoff_30d]
counts = {}
for e in recent:
    key = (e.get("tool", "?"), e.get("name", "?"))
    counts[key] = counts.get(key, 0) + 1

print(f"{BOLD}── Ranking de uso (últimos 30 dias) ──{RESET}")
if not counts:
    print(f"{DIM}(sem invocações nos últimos 30 dias){RESET}")
else:
    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    for (tool, name), n in ranked:
        print(f"  {GREEN}{n:>4}x{RESET}  [{tool:>5}] {name}")
print()

# ─── 2. Skills nunca invocadas (all-time, diff contra ~/.claude/skills/*.md) ─
invoked_skill_names = {
    e.get("name", "")
    for e in entries
    if e.get("tool") == "Skill" and e.get("name")
}

all_skills = set()
if os.path.isdir(SKILLS_DIR):
    for fname in os.listdir(SKILLS_DIR):
        if fname.endswith(".md"):
            all_skills.add(fname[: -len(".md")])

never_invoked = sorted(all_skills - invoked_skill_names)

print(f"{BOLD}── Skills nunca invocadas (histórico completo) ──{RESET}")
print(f"{DIM}Skills existentes: {len(all_skills)} | Já invocadas ao menos 1x: {len(all_skills & invoked_skill_names)}{RESET}")
if not all_skills:
    print(f"{YELLOW}Diretório de skills não encontrado ou vazio: {SKILLS_DIR}{RESET}")
elif not never_invoked:
    print(f"{GREEN}Todas as skills já foram invocadas ao menos uma vez.{RESET}")
else:
    for name in never_invoked:
        print(f"  {RED}·{RESET} {name}")
print()

# ─── 3. Aviso de dados insuficientes para poda ───────────────────────────────
timestamps = [e["_dt"] for e in entries if e["_dt"]]
print(f"{BOLD}── Cobertura temporal ──{RESET}")
if not timestamps:
    print(f"{YELLOW}Nenhum timestamp válido no arquivo — cobertura desconhecida.{RESET}")
    print(f"{RED}{BOLD}⚠ dados insuficientes para poda{RESET}")
else:
    first_ts = min(timestamps)
    span_days = (now - first_ts).total_seconds() / 86400
    print(f"{DIM}Primeira entrada: {first_ts.isoformat()} ({span_days:.1f} dias atrás){RESET}")
    if span_days < 28:
        print(f"{RED}{BOLD}⚠ dados insuficientes para poda{RESET} — histórico cobre {span_days:.1f} dias (mínimo recomendado: 28 dias).")
    else:
        print(f"{GREEN}Histórico cobre {span_days:.1f} dias — suficiente para decisão de poda informada.{RESET}")
PYTHON_SCRIPT
