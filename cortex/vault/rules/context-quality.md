---
id: context-quality
title: Qualidade de Contexto — o agente questiona antes de entregar pouco
type: rule
axis: meta
status: active
created: '2026-09-05'
last_verified: '2026-09-05'
severity: MUST
triggers:
  - contexto
  - pedido
  - briefing
  - "o que você precisa"
  - suposição
  - critério de pronto
  - vago
domain:
  - meta
agents:
  - all
tags:
  - rule
  - contexto
  - eros
links:
- target: cortex-usage-full
  type: auto-linked
- target: eros-quality-full
  type: auto-linked
- target: cross-collaboration-mandate
  type: auto-linked
---

# Qualidade de Contexto — O agente questiona antes de entregar pouco

> **Severidade:** MUST | **Aplica-se a:** Todos os agentes, em qualquer harness (Claude Code, Codex, Cursor, Aider)
> **Origem:** Decisão CEO 05-Set-2026 — a diferença entre entrega mediana e entrega de nível é o contexto que o usuário passa; o agente é responsável por cobrá-lo.

## Princípio

Contexto pobre produz entrega pobre, e a culpa recai no agente. Antes de executar qualquer
tarefa não-trivial, o agente mede o que recebeu. Se faltar o essencial, **não adivinha e não
entrega pela metade**: pergunta o que falta, em uma mensagem só, e diz ao usuário, com clareza
e sem rodeio, que a forma como ele passou a informação limita o nível da entrega.

**Regra de ouro:** "Entregar com contexto insuficiente é escolher o resultado medíocre em nome do usuário."

## Os 5 elementos (o que uma tarefa precisa ter)

| # | Elemento | Pergunta que responde | Exemplo bom | Exemplo pobre |
|---|---|---|---|---|
| 1 | **Objetivo** | Para quê? Qual resultado de negócio? | "reduzir CPL abaixo de R$5 na campanha X" | "melhora os anúncios" |
| 2 | **Entrega** | O que exatamente sai? Formato, tamanho, destino | "3 variações de headline em markdown" | "faz algo aí" |
| 3 | **Onde** | Arquivo, projeto, sistema, URL, campanha | "`~/projetos/x/server.js`, rota /api/leads" | "no sistema" |
| 4 | **Critério de pronto** | Como saber que ficou bom? | "lint passa e a página abre em < 2s" | (ausente) |
| 5 | **Restrições** | O que não pode mudar, prazo, orçamento, tom | "sem mexer no schema; até sexta" | (ausente) |

Pontuação: 1 ponto por elemento presente. **≤ 2/5 em tarefa não-trivial = parar e perguntar.**
3/5 = executar declarando as suposições. 4-5/5 = executar.

## Como agir quando o contexto é pouco (≤ 2/5)

Uma única mensagem, neste formato:

```
Antes de executar: o pedido veio com [N]/5 elementos e isso limita o nível da entrega.
Faltou:
  - Objetivo: [pergunta concreta]
  - Onde: [pergunta concreta]
  - Critério de pronto: [pergunta concreta]
Se preferir que eu siga assim mesmo, vou assumir: [suposição 1], [suposição 2].

Para elevar o nível das próximas entregas, passe já no pedido: objetivo, o que sai,
onde, como saber que ficou bom e o que não pode mudar. Um pedido de 4 linhas com isso
rende mais do que 10 mensagens de ajuste depois.
```

Regras do formato: perguntas concretas (nunca "me dê mais contexto"); no máximo 3 faltas por
vez; sempre oferecer a saída "seguir com suposições"; o aviso sobre a forma de passar informação
é obrigatório e vem **uma vez por sessão**, não a cada pedido.

## Quando NÃO aplicar

| Situação | Por quê |
|---|---|
| Continuação de tarefa em andamento ("segue", "faz o push", "agora o outro") | O contexto já está na conversa |
| Pergunta ou conversa (não é tarefa) | Nada a entregar |
| Fix trivial de 1 arquivo com erro explícito | A mensagem de erro é o contexto |
| Usuário já disse "assuma e faça" nesta sessão | Decisão dele; registre as suposições na entrega |
| Contexto existe em memória/CORTEX/story e o agente consegue buscá-lo | Buscar é obrigação do agente antes de perguntar |

## Anti-patterns

- Entregar "uma versão inicial" sem avisar que faltou contexto. Depois o usuário acha que o agente é fraco.
- Fazer 8 perguntas. Três, concretas, com saída de escape.
- Repetir o sermão sobre "passe melhor a informação" toda mensagem. Uma vez por sessão.
- Perguntar o que está no CLAUDE.md, na story ou na memória do projeto. Busque primeiro.

## Integração

- **EROS Portão 1 (Compreensão):** esta rule é o portão 1 operacionalizado.
- **Hook `context-coach.py`** (Claude Code, UserPromptSubmit): mede o prompt e injeta o lembrete
  quando a pontuação é baixa. Em outros harnesses, o agente aplica a rule lendo este arquivo.
- **Skill `/plan-first`:** com 3/5, o plano é onde as suposições ficam explícitas.
