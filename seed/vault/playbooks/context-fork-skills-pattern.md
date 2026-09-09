---
id: context-fork-skills-pattern
title: Context Fork em Skills — Pattern de Economia de Contexto
type: playbook
domain:
- meta
- vibe-coding
agents:
- vibe-coder
- dev
- sf-master
tags:
- claude-code
- skills
- token-economy
- context-management
- inema-derived
status: active
created: '2026-05-10'
last_verified: '2026-05-10'
decay_rate: 0.02
source: inema-mining-2026-04-12
links:
- target: heuristic-tool-curator-antes-de-recomendar-patch-cve-verificar-vers-o-real-do-alvo
  type: auto-linked
- target: heuristic-vibe-coder-quando-criar-auditar-skill-que-faz-3-tool-calls-antes-de-re
  type: auto-linked
- target: inema-knowledge
  type: derived_from
- target: token-economy
  type: applies_to
- target: migrate-cron-to-cloud-routines
  type: related
- target: cloud-routines-claude-code
  type: related
- target: agent-teams-claude-code
  type: related
- target: claude-opus-4-7-launch-2026-04
  type: related
- target: inema-delta-22-mai-a-11-ago-2026-skills-como-unidade-de-trabalho
  type: related
- target: framework-optimization-roadmap
  type: related
- target: skins-agentes
  type: related
- target: plano-correcao-framework-05-set-2026
  type: related
- target: skills-apresentacao
  type: related
axis: meta
---

# Context Fork em Skills

> Origem: Mineração INEMA CCODE Mar/2026. Recurso novo do Claude Code: skills com `context_fork: true` rodam em janela de contexto **separada**. Trabalho pesado (buscas, tool calls) acontece fora do contexto principal — apenas o resumo limpo retorna.

## Quando Aplicar

Skill é candidata a `context_fork: true` se:
- Faz 3+ tool calls antes de responder (busca, fetch, leitura múltipla)
- Lê arquivos/repos grandes para sintetizar
- Roda análises com múltiplos passos intermediários
- Output esperado é resumo curto comparado ao trabalho interno

## Quando NÃO Aplicar

- Skills que precisam compor com contexto principal (ex: `init`, `simplify`)
- Skills curtas que retornam direto (ex: configs simples)
- Skills que dependem de histórico da conversa principal

## Como Aplicar

```markdown
---
name: skill-name
description: ...
context_fork: true   # ← adiciona esta linha
---
```

Skill roda em janela isolada. Apenas o resumo final retorna ao fluxo principal.

## Skills do Framework Candidatas (auditoria 10-Mai-2026)

| Skill | Razão | Prioridade |
|-------|-------|-----------|
| `analyze-competitors` | Multi-fetch + síntese | ALTA |
| `research` | Multi-fonte (web, RSS, Reddit) | ALTA |
| `conteúdo-semanal` | Pesquisa → estratégia → criativos | ALTA |
| `campaign-report` | Múltiplas chamadas Meta API | ALTA |
| `fix-instagram` | Diagnóstico multi-etapa | MÉDIA |
| `whatsapp-bot` | Deploy multi-step | MÉDIA |
| `claude-api` | Análise multi-arquivo | MÉDIA |
| `init` | NÃO — precisa contexto principal | - |
| `simplify` | NÃO — review do contexto atual | - |

## ROI Estimado

Aplicar `context_fork: true` em 7 skills candidatas TIER ALTA:
- Redução estimada: ~30% tokens de contexto principal em sessões com pesquisa pesada
- Sem custo de implementação (1 linha por skill)
- Sem regressão (default de skills antigas é `false`)

## Companion: 3 Hábitos de Contexto Limpo

1. `context_fork: true` em skills pesadas
2. `/by-the-way` (ou `/btw`) para perguntas secundárias sem poluir contexto
3. `/fork` para explorar caminhos alternativos sem ramificar contexto principal

## Heurística Derivada

> Quando criar/auditar skill que faz 3+ tool calls antes de responder, adicionar `context_fork: true`. Por quê: economia de contexto principal sem perda de funcionalidade. Como aplicar: revisar 89 skills do framework com este filtro; 7 já identificadas como TIER ALTA.

## Fontes

- INEMA_CCODE Mar-Abr/2026 (4.355 msgs)
- `~/projetos/telegram-scraper/mining/ccode-vibe-bmad.md` Seção 1