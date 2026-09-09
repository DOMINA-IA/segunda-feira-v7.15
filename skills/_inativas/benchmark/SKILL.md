---
name: benchmark
description: "Mede performance do framework — latência de query CORTEX, hooks, briefings e build-index — e detecta degradação (adaptado do worker benchmark do ruflo). Use semanalmente, quando o CORTEX parecer lento, após mudanças em hooks/cortex_engine.py, ou antes de decidir se precisa de HNSW vector search."
context_fork: true
axis: meta
harnesses:
  claude-code: full
  codex: native
  cursor: full
  aider: full
model-routing:
  primary: anthropic/claude-haiku-4-5
  analysis: anthropic/claude-sonnet-4-6
---

# /benchmark — Performance Framework

## Quando usar
- Semanalmente (cron sexta 23h)
- Quando query CORTEX começar a sentir lenta
- Após mudanças em hooks ou cortex_engine.py
- Antes de decisão "preciso de HNSW vector search?"

## Métricas Medidas

### CORTEX
```bash
# Query latency (média de 10 runs)
time python3 ~/cortex/scripts/cortex_engine.py query "test query"
```
- p50, p95, p99 latency
- Throughput (queries/sec)
- Index size (notas + bytes)

### Hooks
```bash
# Hook latency em cada PreToolUse/PostToolUse
time python3 ~/.claude/hooks/cortex-auto.py < /tmp/sample-input
time python3 ~/.claude/hooks/consciousness-auto.py < /tmp/sample-input
```
- Latência por hook
- Hooks lentos (>500ms) sinalizados

### Briefings
```bash
# Build briefings completo
time python3 ~/cortex/scripts/cortex_engine.py build-briefings
```
- Tempo total
- Por briefing
- Tamanho médio

### Mailbox + Signals
- Tempo de leitura mailbox
- Latência do signal-router

### Background Crons
- Tempo de execução cada cron noturno (23:20-23:35)
- Variação semana a semana

## Output (relatório semanal)

```markdown
# Framework Benchmark — Semana {YYYY-W##}

## Latências (p95)
| Operação | Esta semana | Semana passada | Δ |
|----------|-------------|----------------|---|
| CORTEX query | 80ms | 75ms | +6.7% ⚠️ |
| cortex-auto hook | 120ms | 110ms | +9% ⚠️ |
| build-briefings | 4.2s | 3.8s | +10.5% ⚠️ |
| signal-router | 45ms | 50ms | -10% ✅ |

## Tamanhos
- CORTEX vault: 912 notas → 925 notas (+1.4%)
- Index: 4.2 MB
- Heurísticas: 378 → 391 (+3.4%)

## Alertas
🟡 CORTEX query p95 cresceu 6.7% — atenção se passar 200ms
🟡 build-briefings cresceu 10% — pode estar relacionado a +13 notas

## Recomendações
1. Se CORTEX query p95 ultrapassar 500ms 2 semanas seguidas → ativar HNSW
2. build-briefings >10s → paralelizar build por briefing
```

## Execução

```bash
# Bench rápido
bash ~/.claude/skills/scripts/benchmark.sh

# Bench completo (inclui crons)
bash ~/.claude/skills/scripts/benchmark.sh --full

# Comparar com semana passada
bash ~/.claude/skills/scripts/benchmark.sh --compare last-week
```

## Quality Gate

- [ ] Todas métricas coletadas (sem erro)
- [ ] Comparação vs semana passada presente
- [ ] Alertas para regressões >20% sinalizados
- [ ] Recomendação concreta para cada alerta

## Multi-LLM

| Sub-tarefa | Modelo |
|------------|--------|
| Medir tempos (time, perf) | Bash/Python — $0 |
| Detectar regressões | Python local — $0 |
| Sugerir otimizações | Sonnet |
| Análise profunda se múltiplas regressões | Opus apenas se justificado |

## Heurísticas

- H1: Regressão >20% por 2 semanas seguidas = action item, não warning
- H2: CORTEX query p95 >500ms = trigger para implementar HNSW
- H3: build-briefings >15s = paralelizar
- H4: Crescimento de vault linear é saudável. Exponencial sugere falta de archive

Origem: ruflo worker `benchmark` + métricas observabilidade.
