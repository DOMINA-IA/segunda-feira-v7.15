---
name: skill-auto-detect
description: "Detector automático de workflows repetidos nos episódios do Consciousness Engine — quando um padrão se repete ≥3x (similaridade Jaccard ≥0.35), gera um draft de skill em ~/.claude/skills/_proposed/ e notifica @spec-engineer. Use mensalmente, após sprint intenso, ou quando suspeitar que está repetindo um workflow não codificado. NOT for: escrever a skill final a partir de um caso de uso já claro — isso é /skill-creator."
axis: meta
harnesses:
  claude-code: full
  codex: native
  cursor: limited
  aider: limited
model-routing:
  primary: local-python-jaccard
  optional-refine: anthropic/claude-sonnet-4-6
---

# /skill-auto-detect — Auto-Skill Proposer

## Quando usar
- Mensalmente (cron sugerido: 1º dia 03h BRT)
- Após sprint intenso de uma semana
- Quando suspeitar que está repetindo workflow não codificado
- Como input para @spec-engineer formalizar skills

## Como funciona

1. Lê episódios de `~/consciousness/memory/episodic/` dos últimos N dias
2. Filtra agentes excluídos (autonomous-smoke, brainstem — ruído)
3. Tokeniza summaries (stopwords + termos curtos removidos)
4. Agrupa por **similaridade Jaccard ≥0.35**
5. Para cada cluster com **≥3 ocorrências**:
   - Gera draft em `~/.claude/skills/_proposed/`
   - Notifica `@spec-engineer` via mailbox

## Execução

```bash
# Dry-run (mostra o que faria, sem criar arquivos)
python3 ~/cortex/scripts/skill_auto_proposer.py --days 7 --dry-run

# Rodada real (cria drafts + mailbox)
python3 ~/cortex/scripts/skill_auto_proposer.py --days 14

# Ajustar sensibilidade
python3 ~/cortex/scripts/skill_auto_proposer.py --days 30 --threshold 0.5 --min-occurrences 5

# JSON estruturado
python3 ~/cortex/scripts/skill_auto_proposer.py --days 14 --json
```

## Parâmetros

| Flag | Default | Quando ajustar |
|------|---------|----------------|
| `--days` | 7 | Aumentar para padrões mensais; reduzir para sprints |
| `--threshold` | 0.35 | Subir (0.5+) para padrões mais estritos; descer (0.25) para detectar mais |
| `--min-occurrences` | 3 | Subir (5+) para reduzir falsos positivos |

## Workflow de revisão

Após executar, drafts em `_proposed/` precisam ser triados:

1. **REVIEW** — Abrir draft, ler episódios fonte, validar padrão
2. Decisão:
   - ✅ **PROMOVER** → mover para `~/.claude/skills/{slug}.md`, preencher pipeline
   - 🔄 **REFATORAR** → reescrever description + pipeline antes de promover
   - 🔗 **CONSOLIDAR** → fundir com skill existente
   - 🗑️ **REJEITAR** → mover para `~/.claude/_archive/skills-rejected/`
3. Marcar como `read: true` no mailbox de @spec-engineer

## Filtros aplicados

Agentes EXCLUÍDOS da análise (ruído):
- `autonomous-smoke` (smoke tests automáticos)
- `brainstem` (consolidação noturna)
- `consciousness` (meta-eventos)

Summaries excluídos:
- "tarefa desconhecida" (auto-gen sem contexto)
- Vazios ou < 100 chars

## Custo

100% Tier 0 (local Python). Zero LLM. Custo: ~$0 por execução, ~5s em 200+ episódios.

## Integração

- **@spec-engineer** recebe mailbox quando proposals criadas
- **@heuristic-curator** pode usar `_proposed/` como input para validação
- **Cron sugerido** (futuro): `0 3 1 * *` (todo dia 1 às 3h BRT)

## Heurísticas

- **H1:** Padrão repetido ≥3x sem skill = código tácito caro. Codificar imediatamente.
- **H2:** Detector é determinístico — mesma input gera mesma proposta. Use para validar mudanças.
- **H3:** Filtrar agentes de smoke/test é CRÍTICO — eles poluem com falsos padrões.
- **H4:** Threshold 0.35 é equilíbrio entre recall (detectar muito) e precision (qualidade).

## Origem

Adaptado de [hermes-agent/agent/curator.py](https://github.com/NousResearch/hermes-agent/blob/main/agent/curator.py) — versão simplificada do curator inactivity-triggered. Hermes faz fork de agente para review; SF faz batch analítico sobre episódios.
