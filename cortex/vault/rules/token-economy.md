---
id: token-economy
title: Token Economy — 3 Tiers, Context Fork
type: rule
domain:
- meta
agents:
- sf-master
tags:
- tokens
- economia
- context-fork
- budget
triggers:
- token economy
- economia token
- context fork
- custo
- tier
- token budget
status: active
created: '2026-04-12'
last_verified: '2026-04-12'
decay_rate: 0.01
on_demand: true
links:
- target: inema-delta-22-mai-a-11-ago-2026-skills-como-unidade-de-trabalho
  type: auto-linked
- target: evolution-scorecard
  type: auto-linked
- target: project-setup-conventions
  type: auto-linked
- target: model-routing-multi-llm-full
  type: auto-linked
- target: .archived-model-routing
  type: auto-linked
- target: model-routing
  type: auto-linked
- target: .archived-token-economy
  type: auto-linked
axis: meta
---

# Token Economy — Economia Inteligente de Tokens

> **Severidade:** SHOULD | **Aplica-se a:** Todos os agentes
> **Origem:** INEMA Tier System (Abr/2026) + Experiência operacional Segunda-feira

## Princípio

Tokens são recurso finito. Usar mais tokens não significa resultado melhor — significa custo maior. A economia inteligente maximiza qualidade por token gasto.

**Regra de ouro:** "Gaste tokens onde o raciocínio importa, economize onde é mecânico."

---

## Tier 1 — Básico (todo agente, toda sessão)

| # | Prática | Impacto |
|---|---------|---------|
| 1 | Conversas novas para tarefas não relacionadas (`/clear`) | Evita contexto irrelevante acumulado |
| 2 | Desconectar MCPs não usados na sessão | MCP conectado = tokens de schema carregados |
| 3 | Agrupar pedidos em uma única mensagem | Cada round-trip gasta tokens de sistema |
| 4 | Plan mode antes de tarefas complexas | Planeja barato, executa caro |
| 5 | Usar `/context` e `/cost` para ver fontes de gasto | Visibilidade = controle |
| 6 | `/statusline` para acompanhar em tempo real | Monitoramento passivo |
| 7 | Colar só o trecho necessário (não arquivo inteiro) | Menos input = menos custo |
| 8 | Observar trabalho em andamento para interromper loops | Loop detectado cedo = economia grande |

## Tier 2 — Intermediário (agentes pesados)

| # | Prática | Impacto |
|---|---------|---------|
| 9 | CLAUDE.md enxuto e bem organizado | Carregado a cada mensagem — cada byte conta |
| 10 | Referenciar arquivos com precisão (função + arquivo exato) | Evita o agente ler arquivos inteiros para encontrar 3 linhas |
| 11 | Compactar por volta de 60% (não esperar automático) | Automático compacta tarde demais — qualidade já caiu |
| 12 | Evitar pausas longas sem compactar (cache expira em 5min) | Cache miss = relê tudo do zero |
| 13 | Cuidado com output grande de comandos (vira contexto) | `npm install` com 500 linhas polui contexto inteiro |

## Tier 3 — Avançado (gestão estratégica)

| # | Prática | Impacto |
|---|---------|---------|
| 14 | Modelo certo por tarefa (ver model-routing.md) | Haiku para subtarefas = 10x mais barato |
| 15 | Entender custo de subagentes (gastam MUITO mais tokens) | Subagente herda contexto + gasta tokens próprios |
| 16 | `context_fork: true` em skills pesadas | Skill roda em janela separada, só resumo volta |
| 17 | CLAUDE.md como "constituição" — conciso mas completo | Referência, não manual. Links > texto inline |

## Hack Especial

**Perto do reset com saldo?** Use pesado — os tokens não acumulam.
**Perto do limite com tempo?** Pare e volte depois — melhor sessão fresca que sessão degradada.

---

## Custo por Modelo (referência)

| Modelo | Input (1M tokens) | Output (1M tokens) | Relativo |
|--------|-------------------|---------------------|----------|
| Opus | $15 | $75 | 1x (referência) |
| Sonnet | $3 | $15 | ~5x mais barato |
| Haiku | $0.80 | $4 | ~10-20x mais barato |

## Context Fork — Skills com Fork Ativo

Skills pesadas que rodam em janela separada para não poluir contexto principal:

- `/daily-scan` — scan completo do negócio
- `/agent-council` — conselho deliberativo multi-perspectiva
- `/swarm-simulation` — simulação MiroFish
- `/content-pipeline` — pipeline 21 posts
- `/weekly-sync` — sync semanal entre agentes
- `/self-optimize` — auto-análise do framework

### Adicionados em 10-Mai-2026 (commands TIER ALTA)
- `/research` — pesquisa multi-fonte (web + RSS + Reddit + HN)
- `/analyze-competitors` — análise competitiva multi-fetch
- `/conteúdo-semanal` — pipeline pesquisa → estratégia → criativos → upload
- `/campaign-report` — relatório Meta Ads multi-API
- `/fix-instagram` — diagnóstico multi-etapa de posts falhos
- `/whatsapp-bot` — gestão multi-comando do bot

**Como adicionar fork a uma skill:** incluir `context_fork: true` no frontmatter YAML.

---

## Anti-Patterns

| Anti-Pattern | Correção |
|-------------|----------|
| Ler arquivo de 2000 linhas para editar 3 | Usar offset+limit no Read, ou Grep primeiro |
| Subagente para tarefa de 1 linha | Fazer inline — subagente tem overhead fixo |
| Output de `ls -la` em diretório com 500 arquivos | Usar Glob com pattern específico |
| `/compact` nunca — esperar automático | Compactar proativamente a 60% |
| MCP conectado mas não usado | Desconectar — schema consome tokens |

---

## Integração

| Componente | Relação |
|-----------|---------|
| `model-routing.md` | Tier 3 #14 — modelo certo por tarefa |
| `consciousness-engine.md` | Episódios consomem tokens — registrar apenas tarefas significativas |
| Skills com `context_fork` | Tier 3 #16 — isolamento de contexto |
