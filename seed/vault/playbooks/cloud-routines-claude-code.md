---
id: cloud-routines-claude-code
title: Cloud Routines (Claude Code) — Automações na Nuvem sem Máquina Ligada
type: playbook
domain:
- meta
- automation
agents:
- vibe-coder
- automation-architect
- dev
- devops
tags:
- claude-code
- routines
- cloud-tasks
- cron
- inema-derived
status: active
created: '2026-05-10'
last_verified: '2026-05-10'
decay_rate: 0.03
source: inema-delta-2026-05-10
links:
- target: heuristic-dev-quando-um-provedor-tira-o-modelo-multimodal-do-ar-decompor
  type: auto-linked
- target: heuristic-devops-quando-rodar-comando-longo-via-run-in-background-da-ferramen
  type: auto-linked
- target: heuristic-tool-curator-antes-de-recomendar-patch-cve-verificar-vers-o-real-do-alvo
  type: auto-linked
- target: heuristic-prompt-engineer-quando-usar-opus-4-7-ser-mais-espec-fico-no-prompt-que-com
  type: auto-linked
- target: people-ops
  type: auto-linked
- target: inema-knowledge
  type: derived_from
- target: agent-teams-claude-code
  type: relates_to
- target: agent-teams-claude-code
  type: related
- target: production-refactor-protocol-instrumenta-o-leve-antes-de-modulariza-o-full
  type: related
- target: context-fork-skills-pattern
  type: related
- target: migrate-cron-to-cloud-routines
  type: related
- target: framework-optimization-roadmap
  type: related
- target: plano-correcao-framework-05-set-2026
  type: related
- target: verificacao-honesta
  type: related
axis: meta
---

# Cloud Routines no Claude Code

> Origem: INEMA_CCODE 15-Abr-2026 (oficial Anthropic). Recurso que permite criar automações que rodam na **nuvem**, sem máquina local ligada. Substitui necessidade de cron próprio para tarefas Claude Code agendadas.

## Como Funciona

Routine = prompt automatizado que pode ser disparado por:
1. **Agendamento** (cron-like, mínimo 1 hora de cadência)
2. **API call** externa
3. **Eventos GitHub** (push, PR, issue, release)

Execução acontece em servidores Anthropic, não na máquina local.

## Configuração

Pré-requisitos:
- Repositório GitHub conectado (sistema lê arquivos de lá)
- Permissões definidas (autonomia da rotina)
- Conectores: Slack, Gmail, ou APIs com chaves diretas

Parâmetros por tarefa:
- Nome
- Prompt (instrução)
- Modelo (Opus 4.7, Sonnet 4.6, Haiku 4.5)
- Repositório alvo
- Ambiente de nuvem
- Cadência (>= 1h)
- Conectores
- Permissões/autonomia

## Diferença vs Soluções Existentes

| Aspecto | GitHub Actions cron | Cloud Routines | Cron local |
|---------|--------------------|--------------------|-----------|
| Máquina ligada | Não | Não | Sim |
| Execução nativa Claude | Workflow yaml | Prompt direto | Comando shell |
| Custo de setup | Médio | Baixo | Baixo |
| Cadência mín | 5min | 1h | 1min |
| Conectores | Manual | Built-in (Slack/Gmail) | Manual |

## Casos de Uso DOMINA.IA

### Substituir cron noturno atual (23:20-23:35 BRT)
```yaml
- mailbox-ttl: cadência 6h em vez de 24h
- feedback-to-consciousness: trigger por commit em ~/feedback-loop
- consolidate.sh: trigger diário 23:30 via Routine cloud
- build-briefings: idempotente, pode rodar a cada 12h
```

### Novos casos viabilizados
- **Daily-scan automatizado**: rota diária verifica anomalias e propõe ao Workspace Global
- **Inema-scout semanal**: rota dispara `*scout` toda segunda 07h sem laptop ligado
- **CVE watch**: rota verifica releases de n8n, Claude Code, etc; alerta no Telegram se mudança crítica
- **Weekly reports**: rota gera relatório dos 5 projetos toda sexta 18h

### Caso emblema do INEMA — Bot Trader 24/7
5 rotinas cobrem dia de negociação:
1. Pré-mercado (pesquisa)
2. Abertura (execução)
3. Meio-dia (análise)
4. Fechamento (resumo)
5. Sexta (revisão semanal)

Memória reside em arquivos `.md` no repositório. Nenhum processo Python roda em lugar nenhum. Claude É o robô.

## Trade-offs

**Quando usar Cloud Routines:**
- Cadência >=1h (limitação)
- Trabalho cabe em prompt + arquivos de repo
- Resultado vai para Slack/Gmail/issue/PR
- Não precisa de hardware local específico (ex: GPU)

**Quando NÃO usar:**
- Cadência <1h (use cron local)
- Precisa de hardware local (GPU para vídeo, mic para voz)
- Acesso a arquivos fora do repositório
- Workflow exige interação humana frequente

## Heurística Derivada

> Quando criar tarefa agendada Claude Code com cadência >=1h e resultado caber em prompt+repo, usar Cloud Routine em vez de cron local. Por quê: independência de máquina ligada + conectores nativos. Como aplicar: começar com 1 routine de baixo risco (ex: weekly report); validar; migrar gradualmente. Manter cron local apenas para tarefas <1h ou hardware-dependentes.

## Próximos Passos para DOMINA.IA

1. Criar 1 Routine piloto: weekly-report-domina (sextas 18h)
2. Validar autonomia + conectores
3. Migrar daily-scan se piloto OK
4. Avaliar bot trader 24/7 como case (ROI alto se ${CEO_NAME} tem capital alocado)

## Fontes

- INEMA_CCODE 15-Abr-2026 (descrição oficial Anthropic)
- INEMA_CCODE 17-Abr-2026 (case Bot Trader 24/7 com 5 routines)
- `~/projetos/telegram-scraper/output/INEMA_CCODE/messages.md`