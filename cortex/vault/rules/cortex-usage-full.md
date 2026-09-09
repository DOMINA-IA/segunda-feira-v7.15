---
id: cortex-usage-full
title: CORTEX — Uso (completo)
type: rule
domain:
- meta
triggers:
- cortex
- briefing
- vault
- ingest
- knowledge base
- cruzamento
axis: meta
source: consolidada em rules/operating-protocol.md + judgment.md (31-Jul-2026)
links:
- target: context-quality
  type: auto-linked
- target: feedback-loop
  type: auto-linked
- target: agent-communication-full
  type: auto-linked
- target: consciousness-engine-full
  type: auto-linked
---

# CORTEX — Regras de Uso do Knowledge System

> **Severidade:** MUST | **Aplica-se a:** Todos os agentes
> **Origem:** CORTEX v1.0 — Segunda-feira v7.1

## Princípio

CORTEX é a base de conhecimento do Segunda-feira. O hook `UserPromptSubmit` injeta contexto automaticamente — o agente recebe briefings e notas relevantes sem precisar buscar. Use esse contexto injetado como ponto de partida.

**Regra de ouro:** "O CORTEX já te deu contexto. Use-o. Só busque mais se precisar aprofundar."

---

## Comportamento Automático (hook UserPromptSubmit)

O hook `router.py` (`~/brain/thalamus/router.py`, disparado via `UserPromptSubmit`) roda em TODA mensagem do usuário e injeta:
- **@agent detectado** → briefing completo do agente (patterns, projetos, playbooks, feedback)
- **Keywords detectadas** → top 3 notas mais relevantes com path
- **Rules on-demand com trigger casado** → corpo truncado em 3000 chars com marcador (teto 3/prompt)

O agente DEVE usar esse contexto injetado. Ele aparece como `[CORTEX Briefing @agent]` ou `[CORTEX Context]`.

## Ao BUSCAR informação adicional

Se o contexto injetado não for suficiente:
```bash
# 1. Query CORTEX (1 call)
python3 ~/cortex/scripts/cortex_engine.py query "termo específico"

# 2. Ler nota específica indicada pelo CORTEX
cat ~/cortex/vault/projects/nota-indicada.md

# 3. ÚLTIMO RECURSO: memória flat
cat ~/.claude/projects/.../memory/arquivo.md
```

## Ao COMPLETAR tarefa com aprendizado

Se a tarefa gerou conhecimento novo ou validou/invalidou conhecimento existente:

```bash
# Criar nova nota
~/cortex/scripts/ingest.sh --title "Nome" --type feedback --domain traffic --agents traffic --tags campanha resultado

# Ou atualizar nota existente + marcar verificada
~/cortex/scripts/refresh.sh note_id
```

## Ao DETECTAR informação desatualizada

Se durante a execução o agente descobrir que uma nota CORTEX tem informação errada:

```bash
# 1. Atualizar a nota diretamente (editar o .md no vault)
# 2. Marcar como verificada
~/cortex/scripts/refresh.sh note_id
# 3. Reconstruir índices
python3 ~/cortex/scripts/cortex_engine.py build-index
```

## Hierarquia de Consulta

```
1. CORTEX query (1 call, ranqueado)
2. CORTEX briefing do agente (pré-computado)
3. Arquivo específico do vault (se query insuficiente)
4. Memória flat (~/.claude/projects/-/memory/) — último recurso
```

## Quando NÃO usar CORTEX

| Situação | Consultar diretamente |
|----------|----------------------|
| Feedback loop (resultados numéricos) | `~/feedback-loop/results.json` |
| Padrões de comunicação | `~/patterns/*.md` |
| Sinais ativos | `~/broadcast/signals.json` |
| Mailbox do agente | `~/broadcast/mailbox/{agent}.json` |
| Código-fonte de projetos | Arquivos do projeto diretamente |

Esses sistemas têm dados operacionais em tempo real que o CORTEX indexa mas não substitui.

---

## Cruzamento Obrigatório de Padrões (cross-project)

Antes de executar qualquer tarefa não-trivial, o agente verifica se existe lição de outro contexto (projeto, campanha, story) que se aplica aqui. Isso previne erros já cometidos e transfere soluções validadas.

**Regra de ouro:** "A lição do projeto A se aplica aqui?"

**Protocolo (antes de tarefa significativa):**
1. Consultar CORTEX/heurísticas pela hierarquia acima (já cobre `cortex_engine.py query` + `heuristics.jsonl`)
2. Se encontrar match: aplicar a lição e registrar micro-sinal inline: `[Cruzamento: lição de {contexto anterior} aplicada — {o que fez diferente}]`

**Quando é obrigatório:**

| Situação | Cruzamento obrigatório? |
|----------|------------------------|
| Story development | SIM — consultar heurísticas antes |
| Campanha/criativo novo | SIM — consultar feedback loop + patterns |
| Bug fix em área já problemática | SIM — verificar erros anteriores |
| Tarefa técnica trivial (lint, format) | NÃO |
| Resposta conversacional | NÃO |

**Anti-patterns:** consultar sem aplicar (cruzamento decorativo); consultar tudo para tudo (overhead em tarefas triviais); ignorar heurística com confidence alta; cruzamento genérico sem especificar qual lição e como foi aplicada.
