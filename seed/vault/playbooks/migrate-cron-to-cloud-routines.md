---
id: migrate-cron-to-cloud-routines
title: Migrar Cron Noturno DOMINA para Cloud Routines (Claude Code)
type: playbook
domain:
- meta
- automation
agents:
- vibe-coder
- automation-architect
- devops
- sf-master
tags:
- cloud-routines
- cron
- migration
- automation
- segunda-feira
status: ready_for_human
created: '2026-05-10'
last_verified: '2026-05-10'
decay_rate: 0.04
links:
- target: 2026-05-07-google-tracking-setup
  type: auto-linked
- target: heuristic-dev-quando-precisar-criar-repo-github-via-cli-1-gh-cli-pode-e
  type: auto-linked
- target: cloud-routines-claude-code
  type: implements
- target: framework-optimization-roadmap
  type: derived_from
- target: cloud-routines-claude-code
  type: related
- target: agent-teams-claude-code
  type: related
- target: framework-optimization-roadmap
  type: related
- target: plano-correcao-framework-05-set-2026
  type: related
- target: score-framework-segunda-feira-04-set-2026-6-4-10
  type: related
- target: score-framework-segunda-feira-05-set-2026-5-4-10
  type: related
- target: score-framework-segunda-feira-07-set-2026-5-2-10
  type: related
axis: meta
---

# Migrar Cron Noturno para Cloud Routines

> **Status:** PREPARADO. Aguardando CEO ativar via UI da claude.ai (Cloud Routines não tem CLI ainda — config é via interface web).
> **Origem:** passo D do framework-optimization-roadmap (10-Mai-2026).

## Por que migrar

- **Independência de máquina ligada** — laptop pode estar fechado, routine roda
- **Conectores nativos** — Slack, Gmail, GitHub events sem setup
- **Observabilidade** — UI da Anthropic mostra histórico de execuções
- **Menos manutenção local** — cron, crontab, logs em ~/logs/, tudo na nuvem

## Inventário de Cron Atual (10-Mai-2026)

Cron jobs ativos no macOS local:

| Cron | Cadência | Quando migra para Cloud? |
|------|----------|--------------------------|
| `utm-manager/otimizacao_12mar.py` | 1x ano (12-Mar 00:05) | **NÃO** — script específico de otimização anual |
| `utm-manager/token_refresh.py` | Segunda 08:00 | **SIM** — bom candidato (cadência semanal) |
| `segunda-feira-daemon/sync-context.sh` | 9h e 18h UTC | **NÃO** — manipula `~/segunda-feira-daemon/` local |
| `consciousness/feedback-to-consciousness.sh` | 23:25 BRT | **NÃO** — lê `~/feedback-loop/` local |
| `consciousness/consolidate.sh` | 23:30 BRT | **NÃO** — workspace `~/consciousness/` local |
| `scripts/daily-scan.sh` | 09:00 BRT | **SIM** — análise estratégica, output Markdown |
| `meeting-pipeline/run-watcher.sh` | 12:00 e 00:05 | **NÃO** — captura local de Google Meet |
| `brain/brainstem/heartbeat.py` (daemon) | @reboot | **NÃO** — daemon contínuo |
| `scripts/daily-digest.sh` (NOVO 10-Mai) | Diário 08:00 (a ativar) | **SIM** — primeiro candidato natural |
| `cortex/scripts/audit_ids.py` (NOVO 10-Mai) | Semanal (a ativar) | **SIM** — output Markdown puro |

## Candidatos a Cloud Routine (priorizados)

### 1. Daily Digest (PRIORIDADE 1)
- **Ainda não está em cron** — perfeito laboratório
- Cadência: diária 08:00 BRT
- Output: Markdown salvo em `~/cortex/reports/`
- Script local: `~/scripts/daily-digest.sh`
- Risco migração: **BAIXO** (não tem usuário esperando ainda)

### 2. Audit IDS (PRIORIDADE 2)
- Cadência: semanal (segunda 06:00 BRT)
- Output: Markdown
- Script local: `~/cortex/scripts/audit_ids.py`
- Risco: **BAIXO**

### 3. Token Refresh utm-manager (PRIORIDADE 3)
- Cadência: semanal (segunda 08:00)
- Crítico para Meta Ads
- Risco: **MÉDIO** — falhar = quebrar ingestão de campanhas

## Passos UI (CEO faz manual na claude.ai)

### Pré-requisitos
- [ ] Conta Anthropic Pro/Max/Team/Enterprise (Cloud Routines não está em Free)
- [ ] Repositório GitHub conectado na claude.ai (configurações → integrações)
- [ ] Conectores configurados: Slack #segunda-feira (ou outro), Gmail (opcional)

### Passo 1 — Criar repo dedicado
```bash
mkdir -p ~/segunda-feira-cloud-routines
cd ~/segunda-feira-cloud-routines
git init
echo "# Segunda-feira Cloud Routines" > README.md
git add . && git commit -m "init"
gh repo create ${HANDLE}mentor-creator/segunda-feira-cloud-routines --private --push
```

### Passo 2 — Adicionar prompt para Daily Digest
Arquivo `~/segunda-feira-cloud-routines/daily-digest.md`:

```markdown
# Daily Digest Routine

Você é o Daily Digest Agent. Sua tarefa:

1. Ler `~/broadcast/signals.json` e listar sinais ativos das últimas 24h
2. Ler `~/consciousness/memory/episodic/*.jsonl` e listar heurísticas registradas em 24h
3. Ler `~/cortex/scripts/cortex_engine.py health` para estado CORTEX
4. Ler `~/.claude/.last-preflight.json` se existir
5. Ler `~/cortex/vault/projects/framework-optimization-roadmap.md` para status

Compor digest em Markdown com seções:
- Sinais Ativos
- Heurísticas Registradas
- Pre-Flight Pendente
- CORTEX Estado
- Roadmap Framework

Salvar em `~/cortex/reports/daily-digest-YYYY-MM-DD.md`.

Enviar resumo de 5 linhas para Slack #segunda-feira.
```

### Passo 3 — Configurar Routine na UI
1. Acessar https://claude.ai/routines (ou similar — caminho exato varia)
2. New Routine
3. Nome: "Daily Digest DOMINA"
4. Repositório: `segunda-feira-cloud-routines`
5. Prompt: arquivo `daily-digest.md` do repo
6. Cadência: diária 11:00 UTC (08:00 BRT)
7. Modelo: Sonnet 4.6
8. Conectores: Slack
9. Permissões: read-only no repo
10. Save & Activate

### Passo 4 — Validar
- Aguardar primeira execução (próximo 08:00 BRT)
- Verificar mensagem no Slack
- Comparar com output de `bash ~/scripts/daily-digest.sh` local
- Se OK: desativar cron local equivalente

### Passo 5 — Replicar para Audit IDS e Token Refresh
Mesmo processo, apenas trocando prompt e cadência.

## O que mantém local (não migra)

Scripts que precisam de filesystem local, hardware ou daemons contínuos:
- `consciousness/consolidate.sh` (lê/escreve `~/consciousness/` workspace)
- `consciousness/feedback-to-consciousness.sh` (lê `~/feedback-loop/`)
- `segunda-feira-daemon/sync-context.sh` (sync com Obsidian local)
- `brain/brainstem/heartbeat.py` (daemon contínuo)
- `meeting-pipeline/run-watcher.sh` (Google Meet local)
- `signal-router.py` (manipula `~/broadcast/`)

Esses ficam em cron local — Cloud Routines não tem acesso ao filesystem do laptop.

## Heurística Derivada

> Quando avaliar migração de cron local para Cloud Routine, perguntar 3 coisas: (a) cadência >= 1h? (b) prompt+repo é input suficiente? (c) output cabe em Markdown ou Slack? Se sim a 3 = candidato. Senão = manter local. Por que: Cloud Routine não acessa filesystem local arbitrário, então jobs que mexem em `~/broadcast/`, `~/consciousness/`, `~/feedback-loop/` ficam local. Como aplicar: começar pelos jobs que JÁ produzem Markdown — eles são portáveis por design.

## Status de Execução

- [x] Inventário cron mapeado (10-Mai-2026)
- [x] 3 candidatos prioritizados
- [x] Prompt template para Daily Digest pronto
- [x] Script local Daily Digest funcional (~/scripts/daily-digest.sh)
- [x] Script local Audit IDS funcional (~/cortex/scripts/audit_ids.py)
- [ ] **CEO:** validar conta Anthropic suporta Routines
- [ ] **CEO:** criar repo GitHub `segunda-feira-cloud-routines`
- [ ] **CEO:** ativar 1ª routine (Daily Digest) via UI
- [ ] **Auto:** validar 1ª execução cloud equivalente ao local
- [ ] **Auto:** desativar cron local correspondente

## Quando o CEO destravar

Avise "ativei a Daily Digest cloud routine" — eu valido a primeira execução e desativo o cron local equivalente automaticamente.

## Fontes

- Sessão 10-Mai-2026 (passo D do roadmap)
- Playbook companheiro: `cloud-routines-claude-code.md`
- Inventário cron: `crontab -l` em 10-Mai-2026 14:30 BRT