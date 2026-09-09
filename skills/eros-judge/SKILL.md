---
name: eros-judge
description: "Avalia de forma independente clareza, completude e acionabilidade de uma entrega (1-5) com gate de aprovação/bloqueio — Portão 4 do EROS. Use antes de liberar entrega não-trivial, para reduzir viés de autoavaliação. NOT for: bug trivial ou…"
axis: meta
harnesses:
  claude-code: full
  codex: full
  cursor: limited
  aider: limited
model-routing:
  primary: anthropic/claude-haiku-4-5   # juiz barato (claude -p)
  independent: openai/gpt-5.5            # juiz cross-provider (codex), menos viés
provider-fallback:
  - anthropic/claude-haiku-4-5
  - openai/gpt-5.5
---

# /eros-judge — Juiz Independente de Qualidade

## Problema que resolve

O EROS Veredito (eros-quality.md) é hoje **auto-avaliação do próprio agente** —
quem fez julga o que fez. Viés inevitável. Este juiz é **independente**: um modelo
que não escreveu a entrega a pontua de fora.

## O que faz

Avalia uma entrega em 3 eixos (escala 1-5):
- **clareza** — o destinatário entende sem adivinhar?
- **completude** — cobre o objetivo sem lacunas?
- **acionabilidade** — dá para usar sem retrabalho?

Aplica **gate** (regra do gstack): completude ou média < 3 → BLOQUEADO; média < 4 →
CONDICIONAL; média ≥ 4 → APROVADO (padrão mínimo Alto do EROS).

## Uso

```bash
# Juiz barato (Haiku, ~$0.001, rápido) — default
python3 ~/.claude/skills/scripts/eros-judge.py <arquivo>
python3 ~/.claude/skills/scripts/eros-judge.py --text "..." --context "p/ quem / objetivo"
cat entrega.md | python3 ~/.claude/skills/scripts/eros-judge.py

# Juiz INDEPENDENTE cross-provider (GPT-5.5 via codex, grátis ChatGPT, menos viés)
python3 ~/.claude/skills/scripts/eros-judge.py <arquivo> --independent
```

## Quando usar

| Situação | Juiz recomendado |
|----------|------------------|
| Story / análise / relatório antes de entregar | Haiku (rápido) |
| Conteúdo OPS de alto valor (oferta, lançamento) | `--independent` (GPT-5.5) |
| Decisão de R$5k+ ou irreversível | `--independent` + revisão humana |
| Bug fix trivial | não usar (proporcionalidade EROS) |

## Integração com o EROS Veredito

Fluxo recomendado no Portão 4 (Revisão) da `eros-quality.md`:
1. Agente faz a auto-checagem EROS (como hoje)
2. Para entregas relevantes, roda `/eros-judge` como **segunda opinião**
3. Se o juiz BLOQUEAR, refaz antes do veredito final
4. Diferença juiz×auto-avaliação grande = sinal de viés → investigar

## Nota sobre custo

Haiku via `claude -p`: ~$0.001/julgamento. GPT-5.5 via `codex`: coberto pela
assinatura ChatGPT ($0 de API). Ambos baratos o suficiente para gate rotineiro.

## Origem

Absorvido do LLM-as-judge do gstack v1.58.5.0 (que usa Sonnet/Haiku). Adaptado
ao SF com a vantagem do **juiz cross-provider grátis** (codex/GPT-5.5), que o
gstack não tem. 26-Jun-2026.
