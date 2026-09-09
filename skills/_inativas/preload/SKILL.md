---
name: preload
description: "Aquece o cache de briefings dos top 5 agentes do dia (via CORTEX Predict) para reduzir latência da primeira mensagem, respeitando a janela de cache de 270s do Anthropic Prompt Cache. Use no início do dia, antes de uma sessão longa prevista, ou após rebuild de briefings (invalida o cache)."
axis: meta
harnesses:
  claude-code: full
  codex: limited
  cursor: none
  aider: none
---

# /preload — Cache Warming

## Quando usar
- Início do dia (cron 7h BRT)
- Antes de sessão longa prevista
- Após `cortex_engine.py build-briefings` (rebuild invalida cache)

## Como funciona

A janela de cache do Anthropic Prompt Cache é **300s TTL**. Manter cache quente significa:
- Briefing carregado em <100ms vs cold ~2s
- Custo cache hit é ~10% do custo normal
- Latência inicial dos agentes despenca

Estratégia:
1. Identificar **top 5 agentes do dia** baseado em CORTEX Predict
2. Para cada agente, fazer uma chamada vazia (NoOp) que toca o briefing
3. Re-cycle a cada 270s (cache window safe)
4. Parar ao fim do dia ou quando CEO offline >2h

## Quem entra no preload

Default (Saturday):
- @content (90% confidence)
- @dev (90%)
- @traffic (90%)
- @architect (recente uso)
- @dev (heavy user)

Configurável via:
```bash
~/.claude/skills/scripts/preload.sh --agents @dev,@content,@traffic
```

## Execução

```bash
# Iniciar daemon de preload
bash ~/.claude/skills/scripts/preload.sh --daemon --top 5

# Status
bash ~/.claude/skills/scripts/preload.sh --status

# Parar
bash ~/.claude/skills/scripts/preload.sh --stop
```

## Quality Gate

- [ ] Top 5 agentes identificados via CORTEX Predict
- [ ] Cache TTL respeitado (<270s entre recycles)
- [ ] Daemon não consome >$1/dia em tokens de aquecimento
- [ ] Hit rate medido (esperado: >70% nas primeiras mensagens do dia)

## Custo vs Benefício

Custo estimado: ~$0.50/dia (5 agentes × 3 ciclos/hora × 8h = 120 chamadas de aquecimento)
Benefício: economia em respostas reais com cache hit (~$3-5/dia)
**ROI:** ~6-10x

## Anti-Patterns

| Evitar | Por quê |
|--------|---------|
| Preload >10 agentes | Custo > benefício |
| Não monitorar hit rate | Pode estar gastando à toa |
| Rodar de madrugada (CEO dorme) | Desperdício |
| Não respeitar TTL 270s | Cache miss = preload inútil |

## Multi-LLM

| Operação | Modelo |
|----------|--------|
| Aquecimento (NoOp call) | Haiku (mais barato, ainda esquenta cache do prefixo) |
| Predição de quem vai usar | CORTEX Predict (local) — $0 |

Origem: ruflo worker `preload` + ScheduleWakeup 270s cache pattern.
