#!/bin/bash
# =============================================================================
# week1-evaluation.sh — Avaliação após 7 dias do Auto Orchestrator (Nível 1).
#
# Roda 1 vez (one-shot) em sábado 02/Mai/2026 às 08:33 BRT.
# Avalia se o ritual gruda e gera relatório com recomendação Nível 2 ou ajuste.
# =============================================================================

# PATH: usa o python3 do sistema (portavel Linux/macOS)
LOG="$HOME/logs/week1-evaluation.log"
mkdir -p "$HOME/logs"

REPORT="$HOME/.cache/sf-week1-evaluation-$(date +%Y%m%d).md"

python3 <<'PY' > "$REPORT" 2>&1
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

HOME = Path.home()
NOW = datetime.now()
WEEK_AGO = NOW - timedelta(days=7)

# 1. Briefings matinais consumidos (existem N arquivos sf-morning-DATA.md?)
cache_dir = HOME / ".cache"
mornings = sorted(cache_dir.glob("sf-morning-*.md"))
mornings_count = len(mornings)

# 2. Episódios novos por agente (últimos 7 dias)
ep_dir = HOME / "consciousness" / "memory" / "episodic"
new_episodes = Counter()
for jf in ep_dir.glob("*.jsonl"):
    name = jf.stem
    try:
        for line in jf.open():
            try:
                ep = json.loads(line)
                ts = ep.get("timestamp") or ep.get("ts") or ""
                if ts:
                    try:
                        epd = datetime.fromisoformat(ts.replace("Z","+00:00").split("+")[0])
                        if epd >= WEEK_AGO:
                            new_episodes[name] += 1
                    except: pass
            except: pass
    except: pass

# 3. Agentes que ANTES nunca tinham episódio mas tiveram esta semana
agents_dir = HOME / ".claude" / "agents"
all_agents = {f.stem for f in agents_dir.glob("*.md") if not f.stem.startswith("_")}
existing_agents = {jf.stem for jf in ep_dir.glob("*.jsonl")}
unused_before = all_agents - existing_agents
newly_used = [a for a in new_episodes if a in unused_before or new_episodes[a] >= 3]

# 4. Decisões registradas
dec_file = HOME / "cortex" / "decisions" / "active.json"
decisions_count = 0
if dec_file.exists():
    try:
        decisions_count = len(json.loads(dec_file.read_text()).get("decisions", []))
    except: pass

# 5. Recomendação
score = 0
if mornings_count >= 5: score += 3
elif mornings_count >= 3: score += 2
elif mornings_count >= 1: score += 1

if len(newly_used) >= 3: score += 3
elif len(newly_used) >= 1: score += 1

if decisions_count >= 5: score += 2
elif decisions_count >= 1: score += 1

if score >= 6:
    rec = "✅ **SOBE PRA NÍVEL 2.** O ritual gruda, vale escalar pra alertas em tempo real."
elif score >= 3:
    rec = "⚠️ **Mantém Nível 1 mais 7 dias.** Está pegando, mas ainda não maduro."
else:
    rec = "🔴 **Não vale Nível 2.** Ritual não está sendo consumido — ajustar formato/horário antes."

print(f"# 📊 Avaliação Auto Orchestrator — Semana 1 ({NOW.strftime('%d/%m/%Y')})\n")
print(f"## Métricas\n")
print(f"- **Briefings matinais gerados:** {mornings_count} / 7")
print(f"- **Agentes novos com episódios esta semana:** {len(newly_used)}")
if newly_used:
    print(f"  - Lista: {', '.join(newly_used)}")
print(f"- **Decisões rastreadas no Decision Engine:** {decisions_count}")
print(f"- **Total de episódios novos esta semana:** {sum(new_episodes.values())}")
print(f"\n## Score de adoção: {score}/8\n")
print(f"## Recomendação\n\n{rec}\n")
print(f"\n## Como agir\n")
print(f"- Para SUBIR pra Nível 2 (alertas em tempo real): rode `~/scripts/level2-upgrade.sh` (ainda não criado)")
print(f"- Para AJUSTAR Nível 1: edite `~/scripts/auto_orchestrator.py` (mude horário, agentes, formato)")
print(f"- Para DESLIGAR tudo: `crontab -e` e comente as linhas com 'auto-orchestrator'")
print(f"\n_Salvo automaticamente — leia com `cat ~/.cache/sf-week1-evaluation-*.md`_")
PY

# Notificação macOS pra você ver
osascript -e 'display notification "Avaliação semana 1 da Segunda-feira pronta. cat ~/.cache/sf-week1-evaluation-*.md" with title "Segunda-feira v7.4" sound name "Submarine"' 2>/dev/null

# Emitir sinal no broadcast
python3 <<PYS 2>/dev/null
import json
from datetime import datetime
from pathlib import Path
p = Path.home() / "broadcast" / "signals.json"
try:
    data = json.loads(p.read_text())
except:
    data = []
if not isinstance(data, list):
    data = []
data.append({
    "id": f"sig_week1_eval_{datetime.now().strftime('%Y%m%d')}",
    "type": "EVALUATION_READY",
    "agent": "@auto-orchestrator",
    "action": "Avaliação semana 1 do Nível 1 pronta — leia ~/.cache/sf-week1-evaluation-*.md",
    "ts": datetime.now().isoformat(),
    "consumed": False,
})
p.write_text(json.dumps(data, indent=2, ensure_ascii=False))
PYS

echo "$(date) — Week 1 evaluation rodou, relatório em $REPORT" >> "$LOG"
