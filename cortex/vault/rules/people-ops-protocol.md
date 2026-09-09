---
name: People Ops Protocol — Quando reportar a @people-ops
description: Protocolo de reporting dos agentes para @people-ops (Athena). Rule on-demand
  injetada via CORTEX hook em contextos relevantes.
type: rule
agents:
- all
tags:
- rule
- people-ops
- athena
- reporting
- agent-ops
- constitutional
created: 2026-05-10
freshness: 1.0
severity: SHOULD
links:
- target: heuristic-dev-quando-uma-fonte-de-dados-for-integrada-medir-os-campos-que
  type: auto-linked
- target: autonomous-execution-full
  type: auto-linked
- target: agent-communication-full
  type: auto-linked
- target: consciousness-engine-full
  type: auto-linked
- target: evolution-scorecard
  type: auto-linked
- target: confidence-guardrails-full
  type: auto-linked
- target: heuristic-dev-quando-ceo-pedir-todos-devem-ir-para-x-em-flows-CLIENTE_EXEMPLO
  type: auto-linked
- target: heuristic-sf-master-quando-rule-constitucional-define-princ-pio-ex-eros-port-o
  type: auto-linked
- target: initiative-protocol
  type: auto-linked
- target: cross-collaboration-mandate
  type: auto-linked
- target: people-ops-bibliografia-2026
  type: auto-linked
- target: people-ops
  type: auto-linked
axis: meta
status: active
triggers:
- people-ops
- athena
- agente dormente
- dormência
- dormencia
- standup
- monitorar agentes
- performance de agente
---
# People Ops Protocol

> **Severidade:** SHOULD | **Aplica-se a:** Todos os agentes
> **Origem:** Criação do @people-ops em 10-Mai-2026

## Princípio

@people-ops (Athena) é o **olho operacional do framework**. Para que ela enxergue a operação corretamente, agentes devem reportar eventos significativos. Reporting é leve, não burocrático — em maior parte automático via Consciousness Engine.

**Regra de ouro:** "Se aconteceu algo que outro agente precisaria saber para ajudar, registre."

## O que reportar (automático via Consciousness Engine)

Todo agente já registra episódios via `record-episode.sh`. Athena consome esses episódios automaticamente. Garantir que os campos abaixo estejam preenchidos quando aplicável:

| Campo | Quando preencher |
|---|---|
| `--type` | Sempre — usa task_completed/task_failed/insight_discovered/error_recovered |
| `--summary` | Sempre — descrição objetiva |
| `--result` | success/partial/failure |
| `--valence` | -1.0 a +1.0 — sentimento sobre execução |
| `--intensity` | 0.0 a 1.0 — quão memorável |
| `--worked` | O que funcionou (se positivo) |
| `--failed` | O que falhou (se negativo) |
| `--heuristic` | Aprendizado extraído ("Quando X, fazer Y porque Z") |

## O que reportar (explícito via mailbox para @people-ops)

Em contextos específicos, enviar mensagem direta para `~/broadcast/mailbox/people-ops.json`:

| Situação | Tipo de mensagem | Urgência |
|---|---|---|
| Agente bloqueado (não consegue executar mesmo tendo autoridade) | `alert` | high |
| Heurística com confidence >0.9 após 10+ aplicações | `request` (promoção a rule) | normal |
| Detecta degradação em outro agente (output ruim) | `info` | high |
| Sugestão de criar agente novo para domínio não coberto | `request` (analisar) | low |
| Sucesso excepcional (valência +0.9, intensidade >0.8) | `info` (celebrar/registrar) | low |
| Conflito de autoridade detectado | `alert` | high |

## Formato da mensagem (canonical-v3)

```json
{
  "id": "msg_{timestamp}",
  "from": "@agente-remetente",
  "to": "@people-ops",
  "type": "request|info|alert|response",
  "subject": "Resumo 1 linha",
  "body": "Detalhes",
  "priority": "high|normal|low",
  "data": {},
  "timestamp": "ISO-8601",
  "read": false,
  "thread_id": null
}
```

## O que @people-ops faz com o reporting

- **Daily standup (08h05)** consome últimas 24h
- **Dormant detector (segunda 09h)** consulta histórico
- **Quarterly review** agrega trimestre completo
- **CSAT (quinzenal sexta 17h)** correlaciona com percepção do CEO
- **Workspace global** Athena propõe ignição quando padrão cross-agent emerge

## Anti-padrões

| Evitar | Por quê |
|---|---|
| Reportar coisa trivial (lint passou) | Polui dados, dilui sinal |
| Não registrar valência | Athena perde a leitura emocional → análise pobre |
| Heurística genérica ("fazer melhor") | Sem especificidade não promove a rule |
| Esperar @people-ops perguntar | Reporting é PUSH, não pull |
| Reportar via Telegram direto | Quebra a cadência aggregate da Athena — gera ruído pro CEO |

## Integração com outras rules

| Rule | Como interage |
|---|---|
| `consciousness-engine.md` | Fonte primária dos dados que Athena consome |
| `agent-communication.md` | Define mailbox como canal canônico |
| `eros-quality.md` | Veredito EROS entra na análise de Athena |
| `confidence-guardrails.md` | Confidence dos episódios alimenta override rate |
| `autonomous-execution.md` | Define autoridade de Athena |
| `feedback-loop.md` | Resultados de negócio entram em métricas de qualidade |
