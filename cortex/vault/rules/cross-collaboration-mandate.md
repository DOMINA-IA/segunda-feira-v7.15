---
name: Cross-Collaboration Mandate — Agentes devem se comunicar
description: 'Regra constitucional: agentes devem usar mailbox para handoff cross-domain.
  Resolve descoberta Athena 11-Mai-2026: signal-router saudável mas mailboxes em zero
  por ausência de cultura.'
type: rule
agents:
- all
tags:
- rule
- cross-collaboration
- mailbox
- constitutional
- people-ops
- athena-mandated
severity: MUST
created: 2026-05-10
freshness: 1.0
links:
- target: context-quality
  type: auto-linked
- target: heuristic-analyst-quando-o-diagnostico-financeiro-travar-por-falta-de-informac
  type: auto-linked
- target: agent-communication-full
  type: auto-linked
- target: consciousness-engine-full
  type: auto-linked
- target: heuristic-architect-quando-cliente-entrega-prompt-de-agente-como-pedido-trata
  type: auto-linked
- target: visual-rendering-safety
  type: auto-linked
- target: n8n-patterns
  type: auto-linked
- target: axis-separation-full
  type: auto-linked
- target: feedback-loop
  type: auto-linked
- target: heuristic-mestre-do-conselho-quando-ceo-t-cnico-est-em-modo-reconhecimento-sem-deadline
  type: auto-linked
- target: .archived-initiative-protocol
  type: auto-linked
- target: initiative-protocol
  type: auto-linked
- target: people-ops-protocol
  type: auto-linked
- target: people-ops-bibliografia-2026
  type: auto-linked
axis: meta
status: active
triggers:
- colaboração
- colaboracao
- cruzamento
- handoff
- mailbox
- sinal
- inter-agente
- delegar
- broadcast
---
# Cross-Collaboration Mandate

> **Severidade:** MUST | **Aplica-se a:** Todos os agentes
> **Origem:** Descoberta Athena 11-Mai-2026 — signal-router OK (52 sinais roteados), mas só `@consciousness` emite signals. Agentes não conversam entre si. Cada um reinventa contexto. Resultado: 37% do trabalho recai em `@dev` que vira hub de informação que deveria fluir lateralmente.

## Princípio

A robustez do framework não vem de cada agente ser bom — vem de eles se comunicarem. Um agente isolado vê 1/64 do contexto. Dois agentes que trocam mensagem veem 2/64. Quando 32 agentes se comunicam, todos veem 32/64 sem nenhum precisar fazer trabalho extra de pesquisa.

**Regra de ouro:** "Se sua entrega muda a decisão de outro agente, MANDE A MENSAGEM. Não espere que ele descubra."

---

## Quando comunicar (MUST)

| Situação | Para quem | Tipo de mensagem |
|---|---|---|
| Criou novo ângulo de conteúdo | @creative-director, @traffic | info |
| Pausou/criou/escalou campanha | @content, @copywriter, @analyst | broadcast (signal) |
| Detectou bug em código compartilhado | @dev, @qa, @architect | alert |
| Identificou padrão em dados (CPL, CTR, conv) | @traffic, @offer-engineer, @copywriter | info |
| Criou/alterou oferta | @traffic, @copywriter, @content, @analyst | info |
| Cliente reportou problema | @cs (futuro), @dev, @cs-retention | request |
| Lead qualificado entrou | @closer (futuro), @cs | request |
| Encontrou tendência de mercado | @content, @traffic, @offer-engineer | info |
| Bug em produção | @dev, @devops, @security-auditor | alert (urgência alta) |
| Heurística promovida a rule | @sf-master, @people-ops | info |
| Output rejeitado pelo CEO | @people-ops, agente substituto | response |

## Como comunicar (formato canonical-v3)

```bash
bash ~/broadcast/send-mail.sh @destinatario "Assunto 1 linha" "Body com detalhes acionáveis"
```

Ou Python equivalente:
```python
import json, time
with open('$HOME/broadcast/mailbox/{destino}.json', 'r+') as f:
    mb = json.load(f)
    mb['messages'].append({
        "id": f"msg_{int(time.time())}",
        "from": "@meu-nome",
        "to": "@destino",
        "type": "request|info|alert|response",
        "subject": "Resumo 1 linha",
        "body": "Detalhes",
        "priority": "high|normal|low",
        "data": {},
        "timestamp": "...",
        "read": False,
        "thread_id": None
    })
    f.seek(0); json.dump(mb, f, indent=2); f.truncate()
```

## Métrica obrigatória

Cada agente DEVE enviar **≥1 mensagem cross-agent por semana de atividade**. Métrica monitorada por @people-ops no Daily Standup. Agentes que ficam 2+ semanas sem enviar mensagem cross-agent são flaggeados como "isolados" e entram em review.

## O que NÃO comunicar

| Evitar | Por quê |
|---|---|
| Confirmação trivial ("li sua msg") | Polui mailbox, dilui sinal |
| Status update repetitivo | Use Consciousness Engine, não mailbox |
| Mensagem sem subject claro | Destinatário ignora |
| Flood de low-priority | Vira ruído |
| Mensagem para si mesmo | Inútil — use memória local |

## Boot Protocol atualizado

Todo agente ao ser ativado DEVE:
1. `bash ~/broadcast/agent-boot-context.sh meu-nome` (já obrigatório por `consciousness-engine.md`)
2. **NOVO:** Verificar `~/broadcast/mailbox/{eu}.json` — processar mensagens unread ANTES de executar tarefa principal
3. Responder mensagens que requerem resposta no formato `response`

## Anti-Patterns

| Evitar | Por quê |
|---|---|
| "Vou comunicar quando tiver tempo" | Não vai — registre na hora |
| "Outro agente vai descobrir sozinho" | Não vai — você cria silos |
| Mandar pra todos (broadcast spam) | Use signals.json para multicast, mailbox para 1:1 |
| Não reagir a mensagem unread | Quebra trust no canal |
| Esperar Athena lembrar | Ela LEMBRA — vai puxar você no review |

## Integração com outras rules

| Rule | Como interage |
|---|---|
| `agent-communication.md` | Define mecânica básica — esta rule expande para MANDADO |
| `consciousness-engine.md` | Episódios complementam, não substituem mailbox |
| `feedback-loop.md` | Resultados disparam mensagens automáticas |
| `eros-quality.md` | Falha em comunicar = código P3 (violação de autonomia/processo) |
| `people-ops-protocol.md` | Athena consome dados de mailbox para review |

## Por que esta rule existe hoje (11-Mai-2026)

@people-ops fez engagement analysis e descobriu:
- 32 agentes, 320 episódios em ~30 dias
- 87% das tarefas geram heurística (cultura de aprendizado VIVA)
- **0 mensagens cross-agent** em qualquer mailbox
- Signal-router rodando a cada 15min, roteia tudo, mas o que ele roteia é só `@consciousness` → ninguém

Conclusão: o framework aprende mas não conversa. Esta rule muda isso.
