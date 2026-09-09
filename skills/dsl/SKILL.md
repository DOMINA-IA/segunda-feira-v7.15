---
name: dsl
description: "Expande comandos de raciocínio (/truth, /gaps, /pushback, /rank, /decide, /redteam) em protocolos completos e encadeáveis na ordem digitada. Use quando a mensagem começar com comando de barra. NOT for: execução técnica (deploy, código, query)."
axis: meta
harnesses:
  claude-code: full
  codex: full
  cursor: full
  aider: full
provider-fallback:
  - anthropic/claude-opus-5
  - openai/gpt-5
  - google/gemini-3.5-flash
---

# /dsl — Command Registry de Raciocínio

## Problema que resolve

Prompts bons são longos e repetitivos. Você reescreve "separe fato de inferência, verifique o que
está instável, diga o que não sabe" toda vez — ou não reescreve, e recebe resposta rasa.

Um comando é o **atalho**; o Command Registry abaixo é quem dá o **significado**. O agente lê o
comando, expande para o protocolo completo e só então executa.

**Regra de ouro:** "O comando não é código secreto do modelo. É contrato de protocolo que VOCÊ mantém."

> Origem: INEMA.Prompts, 19-Ago-2026 — tese da *INEMA Command Language*. Funciona porque Opus 5 e
> GPT-5.6 são fortes em instruction-following, não porque as palavras sejam mágicas.

## Como acionar

Comandos no **início** da mensagem, encadeáveis, executados **na ordem digitada**:

```
/truth /gaps /pushback   Quero abrir uma comunidade paga de médicos interessados em IA.
```

→ verifica realidade → encontra lacunas → ataca a própria tese → só então recomenda.

Sem comando, a skill não age. Ela não sequestra conversa normal.

---

## Command Registry

### Verificação

| Comando | Protocolo |
|---|---|
| `/truth` | Separe **fato / inferência / hipótese / desconhecido** em blocos rotulados. Marque tudo que pode ter mudado desde o cutoff e verifique antes de concluir. Declare `[confidence: 0.0-1.0]` por afirmação factual. Nunca apresente inferência com voz de fato. |
| `/evidence` | Para cada afirmação central, cite a fonte concreta (arquivo, URL, log, medição). Sem fonte → marque `SEM LASTRO` explicitamente em vez de suavizar. |
| `/gaps` | Liste o que está **faltando** na proposta, não o que está errado. Cubra: dados ausentes, decisão não tomada, dependência não mapeada, pessoa não consultada, custo não estimado. Ordene por quanto bloqueia a execução. |

### Adversarial

| Comando | Protocolo |
|---|---|
| `/pushback` | Tente **refutar** a proposta antes de recomendá-la. Argumento mais forte contra, não o mais fácil. Só recomende se a tese sobreviver. Se sobreviver alterada, entregue a versão alterada. |
| `/redteam` | Assuma que a ideia vai falhar e explique **como**. Vetores: técnico, financeiro, jurídico, reputacional, operacional, humano. Para cada um: gatilho, sinal precoce, mitigação. |
| `/premortem` | Salte 6 meses à frente: "isso fracassou". Escreva o post-mortem retroativo — a causa mais provável primeiro. Depois volte e diga o que fazer hoje para matar essa causa. |

### Decisão

| Comando | Protocolo |
|---|---|
| `/rank` | Defina critérios **explícitos com peso** antes de comparar. Tabela opção × critério com nota. Declare o critério que mais pesou e o que aconteceria se ele fosse removido. |
| `/decide` | Recomende **uma** opção, sem empate. Formato: escolha / porquê em 3 linhas / o que te faria mudar de ideia / custo de reverter / prazo em que a decisão expira. |
| `/secondorder` | "E depois?" três vezes. Efeito de 1ª ordem → 2ª → 3ª. Inclua o efeito sobre incentivos das pessoas envolvidas, que é o mais esquecido. |

### Construção

| Comando | Protocolo |
|---|---|
| `/blueprint` | Plano executável: objetivo mensurável, sequência numerada, dono por etapa, dependências, critério de pronto, ponto de reversão. Sem prosa motivacional. |
| `/simplify` | Corte pela metade. Diga explicitamente **o que foi removido e o que se perde**. Nunca entregue versão curta fingindo que nada se perdeu. |
| `/monetize` | Caminhos de receita ordenados por **tempo até o primeiro real**. Para cada: preço, quem paga, esforço de entrega, por que ainda não existe. |

---

## Combinações que funcionam

| Sequência | Uso |
|---|---|
| `/truth /gaps` | Antes de agir sobre informação de terceiro |
| `/pushback /decide` | Decisão que você já quer tomar (força o contraditório antes) |
| `/rank /decide /premortem` | Escolha entre alternativas com aposta real |
| `/redteam /blueprint` | Antes de deploy ou lançamento |
| `/truth /evidence` | Auditoria de relatório ou proposta externa |

## Regras de execução

1. **Ordem importa** — execute na sequência digitada; ela é o raciocínio.
2. **Um cabeçalho por comando** — a saída mostra onde cada protocolo agiu.
3. **Sem diluir** — `/pushback` que só elogia falhou. Se não há objeção real, diga "a tese resiste" e mostre o que você tentou.
4. **Comando desconhecido** → não invente. Liste os disponíveis e pergunte.
5. **Interage com EROS** — `/truth` e `/evidence` cobrem o Portão 4 (Revisão). Não duplique veredito.

## Estender

Um comando novo = uma linha no registry acima com protocolo **operacional** (o que fazer),
não adjetivo (ser rigoroso). Se não dá para descrever a ação, não é comando — é vontade.
