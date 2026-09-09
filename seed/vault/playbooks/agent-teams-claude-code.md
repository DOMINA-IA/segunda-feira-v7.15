---
id: agent-teams-claude-code
title: Agent Teams — Multi-Agent Colaborativo no Claude Code
type: playbook
domain:
- meta
agents:
- vibe-coder
- dev
- architect
- sf-master
tags:
- claude-code
- multi-agent
- teammate-mode
- inema-derived
status: active
created: '2026-05-10'
last_verified: '2026-05-10'
decay_rate: 0.03
source: inema-mining-2026-04-12
links:
- target: heuristic-dev-quando-um-sistema-tem-so-o-caminho-da-excecao-implementado
  type: auto-linked
- target: heuristic-dev-antes-de-declarar-um-lote-de-tarefas-conclu-do-reler-a-list
  type: auto-linked
- target: heuristic-po-quando-validar-story-que-descreve-maquina-de-estados-enumer
  type: auto-linked
- target: heuristic-devops-monitor-que-aceita-o-estado-de-falha-como-sucesso-pior-que
  type: auto-linked
- target: heuristic-content-quando-narrativa-de-caso-real-tem-dados-de-agentes-incorreto
  type: auto-linked
- target: heuristic-content-quando-criar-conte-do-pra-evento-de-ia-com-p-blico-empres-ri
  type: auto-linked
- target: heuristic-traffic-quando-criar-campanha-meta-sem-cbo-via-api-sempre-incluir-i
  type: auto-linked
- target: heuristic-inema-scout-quando-absorver-descoberta-urgente-cve-vulnerabilidade-br
  type: auto-linked
- target: heuristic-prompt-engineer-quando-usar-opus-4-7-ser-mais-espec-fico-no-prompt-que-com
  type: auto-linked
- target: heuristic-vibe-coder-quando-criar-auditar-skill-que-faz-3-tool-calls-antes-de-re
  type: auto-linked
- target: inema-knowledge
  type: derived_from
- target: agent-communication
  type: extends
- target: claude-opus-4-7-launch-2026-04
  type: related
- target: loopy-era-karpathy-2026-03
  type: related
- target: production-refactor-protocol-instrumenta-o-leve-antes-de-modulariza-o-full
  type: related
- target: dashboard-data-freshness-toda-tabela-operacional-precisa-de-updated-at
  type: related
- target: inema-delta-22-mai-a-11-ago-2026-skills-como-unidade-de-trabalho
  type: related
- target: context-fork-skills-pattern
  type: related
- target: migrate-cron-to-cloud-routines
  type: related
- target: framework-optimization-roadmap
  type: related
- target: skins-agentes
  type: related
- target: clienteexemplo-pacote-c-consolida-o-completa-abr-2026
  type: related
- target: plano-correcao-framework-05-set-2026
  type: related
- target: skills-apresentacao
  type: related
axis: meta
---

# Agent Teams — Multi-Agent Colaborativo

> Origem: INEMA CCODE 25-Mar/2026. Recurso experimental para times de agentes especializados que colaboram entre si DIRETAMENTE (vs subagentes que retornam ao principal). Requer Claude Code v2.1.32+.

## Diferença vs Subagentes

| Aspecto | Subagentes (atual) | Agent Teams (novo) |
|---------|-------------------|-------------------|
| Comunicação | Retornam ao agente principal | Colaboram entre si diretamente |
| Contexto | Fork do principal | Independente, com seu próprio CLAUDE.md |
| Caso de uso | Tarefas isoladas, paralelas | Equipe trabalhando em sistema |
| Execução | Terminal único | tmux + multiplas janelas |

## Como Habilitar

```bash
# Variável de ambiente
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# OU persistente em .claude/settings.local.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

## Boas Práticas (do INEMA)

- 3 a 5 agentes por time (mais que isso vira ruído)
- Cada agente com responsabilidade sobre arquivos/entregas específicas
- Dar contexto completo (não tem histórico)
- Usar `tmux` para acompanhar visualmente
- `--teammate-mode in-process` para terminal simples
- Sempre incluir QA agent que valida fluxo e devolve correções

## Template de Prompt

```
Crie um agent team com 3 teammates usando Sonnet.
Objetivo: [OBJETIVO]

Teammate 1: [PAPEL]
- [responsabilidades]
- [entregáveis]

Teammate 2: [PAPEL]
- [responsabilidades]
- [entregáveis]

Teammate 3: QA agent
- validar fluxo, achar bugs e devolver correções
- só marcar como concluído quando os críticos forem resolvidos

Entregáveis finais:
- app rodando localmente
- relatório de testes
- resumo do que foi feito
```

## Aplicação ao Framework Segunda-feira

Times naturais já mapeados:

| Squad | Teammates | Caso de uso |
|-------|----------|------------|
| **Story Squad** | @dev + @qa + @architect | Desenvolvimento de story complexa |
| **Launch Squad** | @launch-strategist + @copywriter + @creative-director + @traffic | Lançamento de oferta |
| **Content Squad** | @content + @creative-director + @copywriter | Pipeline conteúdo semanal |
| **Voice Squad** | @video-producer + @voice-ai-specialist + @creative-director | Vídeo do ${CEO_NAME} sem gravar |
| **Outreach Squad** | @cold-outreach + @copywriter + @sdr | Campanha B2B |

## Considerações de Segurança

- Cada teammate tem permissões próprias — auditar antes de produção
- Times com `git push` exigem @devops como QA gate
- Compartilhamento de credenciais entre teammates DEVE passar por broadcast/mailbox

## Heurística Derivada

> Quando tarefa cruza 3+ domínios e exige colaboração contínua (não round-trip), considerar Agent Team em vez de subagentes sequenciais. Por quê: comunicação direta reduz ping-pong de contexto. Como aplicar: identificar squad pré-existente, definir QA agent como gatekeeper, usar tmux para visibilidade.

## Status no Framework

Pendência: criar squad-creator skill que orquestra Agent Team via CORTEX squads (`~/.aios-core/squads/`).

## Fontes

- INEMA_CCODE 25-Mar/2026
- `~/projetos/telegram-scraper/mining/ccode-vibe-bmad.md` Seção 4