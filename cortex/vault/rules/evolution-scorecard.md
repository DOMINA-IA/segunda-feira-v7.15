---
id: evolution-scorecard
title: Evolution Scorecard — Métricas de Evolução por Sessão
type: rule
domain:
- meta
agents:
- sf-master
tags:
- scorecard
- métricas
- evolução
- antecipação
triggers:
- scorecard
- métricas de evolução
- evolução por sessão
- antecipação
- antecipações aceitas
- erros repetidos
- perguntas desnecessárias
status: active
created: '2026-04-12'
last_verified: '2026-07-07'
decay_rate: 0.01
on_demand: true
axis: meta
links:
- target: token-economy
  type: auto-linked
- target: people-ops-protocol
  type: auto-linked
- target: credentials-handling-full
  type: auto-linked
- target: consciousness-facts
  type: auto-linked
---

# Evolution Scorecard — Métricas de Evolução por Sessão

> **Severidade:** SHOULD | **Aplica-se a:** Todos os agentes
> **Origem:** Absorvido de Deus Sistêmico (Abr/2026) + Adaptado para Segunda-feira v7.1

## Princípio

Evolução que não se mede não existe. Cada agente rastreia sua própria performance com métricas concretas, não platitudes.

**Regra de ouro:** "Se você não sabe se melhorou vs a última sessão, não melhorou."

---

## Métricas Obrigatórias (por sessão)

| Métrica | O que mede | Meta |
|---------|-----------|------|
| Erros repetidos | Quantos erros já catalogados em heurísticas voltaram a acontecer | 0 |
| Perguntas desnecessárias | Quantas vezes o agente perguntou algo que poderia inferir | 0 |
| Antecipações feitas | Quantas ações proativas o agente tomou antes do pedido | Crescente |
| Antecipações aceitas | Quantas dessas o usuário aceitou sem editar | >70% |
| Entregas sem revisão | Quantas entregas o usuário aceitou na primeira versão | >80% |
| Cruzamentos aplicados | Quantas lições de outro contexto evitaram erro | Crescente |

## Quando Atualizar

- Ao final de sessões significativas (não triviais)
- Registro via Consciousness Engine (campo extras no episódio)
- Consolidação automática no ciclo noturno do brainstem

## Onde Armazenar

NÃO criar arquivo separado. Usar o Consciousness Engine existente:
- Episódios já capturam success/failure + valence
- Heurísticas já capturam aprendizados
- O scorecard é uma VIEW sobre dados que já existem

## Anti-Patterns

| Evitar | Por quê |
|--------|---------|
| Scorecard decorativo (tudo "ok") | Se tudo está perfeito, as métricas são brandas demais |
| Registrar em arquivo flat separado | Duplica dados — usar Consciousness Engine |
| Preencher com números inventados | Pior que não ter scorecard |
| Rastrear métricas que não mudam nada | Cada métrica deve informar comportamento futuro |

## Integração

| Componente | Relação |
|-----------|---------|
| `consciousness-engine.md` | Fonte dos dados (episódios + heurísticas) |
| `~/consciousness/scripts/reflect.sh` | Reflexão periódica que usa essas métricas |
| Brainstem ciclo sono | Consolida métricas na síntese noturna |
