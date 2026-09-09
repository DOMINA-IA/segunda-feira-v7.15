---
name: today-recap
description: "Resume as entregas do dia atual (100% local, custo zero) cruzando episódios do Consciousness Engine, git diff e sessions_db — top agentes do dia, arquivos alterados, crises resolvidas e pendências. Use para 'o que fiz hoje?' ou 'onde parei?' rápido, sem precisar buscar. NOT for: buscar em dias/sessões passadas ou por termo específico — isso é /session-search."
axis: meta
harnesses:
  claude-code: full
  codex: limited
  cursor: limited
  aider: limited
model-routing:
  primary: local-bash-tier0
---

# /today-recap — Resumo do Dia

## Quando usar
- Fim do dia: "o que fiz hoje?"
- Início do dia seguinte: "onde parei?"
- Antes de standup: "preciso lembrar das entregas"
- Quando perder o contexto numa sessão longa

## Como executa

100% Tier 0 (local Bash/Python, $0):

```bash
# 1. Episódios de hoje (filtrados, sem ruído)
TODAY=$(date +%Y-%m-%d)
for f in ~/consciousness/memory/episodic/*.jsonl; do
  agent=$(basename "$f" .jsonl)
  grep "\"timestamp\":\"$TODAY" "$f" 2>/dev/null | while read line; do
    echo "$line" | python3 -c "
import json, sys
ep = json.loads(sys.stdin.read())
ts = ep.get('timestamp','')[11:16]
summ = ep.get('summary','')[:150]
res = (ep.get('outcome') or {}).get('result','?')
print(f'  {ts} @$agent ({res}): {summ}')
"
  done
done | sort

# 2. Sessions DB do dia (via skill /session-search)
python3 ~/cortex/scripts/sessions_db.py browse --limit 20

# 3. Versão atual do framework
grep -E "Constituição v[0-9]" ~/.claude/CLAUDE.md | head -1
```

## Output esperado

```
🗓️  RECAP — 2026-05-24

🎯 Versão atual: v7.10 "Cost Crisis Mitigated"

📋 Episódios significativos (cronológico):
  08:31 @sf-master (success): Sprint completo de absorção ruflo→Segunda-feira v7.7...
  09:21 @sf-master (success): Sprint Hermes Absorption v7.8 (B+C) completo...
  09:35 @sf-master (success): Sprint D — User Model completo (v7.9)...
  09:52 @sf-master (success): Sprint D.1 — User Model OPS Integration (v7.9.1)...
  10:05 @cost-watchdog (success): COST CRISIS MITIGATED (v7.10)...

🔧 Top agents do dia: @sf-master(8), @cost-watchdog(3), @dev(2)

📁 Arquivos criados/modificados:
  ~/.claude/agents/{spec-engineer,tester,heuristic-curator}.md
  ~/.claude/skills/{cortex-pagerank,cortex-ultralearn,...}.md
  ~/cortex/scripts/{sessions_db,skill_auto_proposer,user_model_updater}.py
  ~/cortex/vault/user-model/*.md
  ~/HERMES-ABSORPTION-REPORT.md
  ~/SESSION-SUMMARY-2026-05-24.md

⚠️  Crises resolvidas:
  R$ X.XXX (11 dias) em sessões Opus padrão @dev → settings.json model=sonnet

🚧 Pendências:
  - 4 CTR alerts <1% (ver ~/cortex/reports/ops-creative-refresh-*.md)
  - Sprint E DSPy+GEPA (deferido)
```

## Variações úteis

```bash
# Recap de outro dia
python3 ~/cortex/scripts/sessions_db.py search "$(date -v -1d +%Y-%m-%d)"

# Só episódios success (sem failures)
grep "task_completed.*success" ~/consciousness/memory/episodic/*.jsonl

# Total custo/heurísticas do dia
wc -l ~/consciousness/memory/procedural/heuristics.jsonl
# (comparar com snapshot do dia anterior)
```

## Heurísticas

- **H1:** Recap deve ser <60s de leitura — se passar, está detalhado demais
- **H2:** Listar APENAS episódios significativos (filtrar tarefa_desconhecida + smoke)
- **H3:** Top agents revela onde mais tempo foi investido (sinal de prioridade)
- **H4:** Crises resolvidas + pendências = bookend do dia

## Multi-LLM

100% Tier 0 (Bash + Python local). Zero custo de tokens.

## Origem

Skill nova v7.10 — auto-contida, aproveita infra já existente (sessions_db.py, consciousness episódios). Inspirada pelo padrão de daily recap do hermes-agent.
