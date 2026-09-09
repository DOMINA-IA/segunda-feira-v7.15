---
id: cortex-internal-formulas
title: CORTEX — Fórmulas Internas (Estado Atual)
type: meta
axis: meta
status: active
created: '2026-05-23'
last_verified: '2026-05-23'
decay_rate: 0.01
domain:
- meta
- framework
agents:
- knowledge-builder
- rag-architect
tags:
- cortex
- freshness
- orphan
- decay
- documentation
- activation-sprint
links:
- target: cortex-formula-canonica-freshness
  type: related
- target: inema-abr-2026-minera-o-upgrade-ecossistema
  type: related
---

# CORTEX — Fórmulas Internas (Estado Atual)

> Documento de auditoria produzido pelo @knowledge-builder em 2026-05-23.
> Objetivo: registrar EXATAMENTE como cada fórmula funciona hoje, antes de qualquer
> decisão canônica do @rag-architect.
> Cross-link: [[cortex-formula-canonica-freshness]] (nota do @rag-architect — pode não existir ainda)

Fonte primária: `~/cortex/scripts/cortex_engine.py`

---

## 1. Freshness Score

### Onde vive

Função `calculate_freshness(note)` — `cortex_engine.py`, linhas 122–156.
Chamada por: `build_freshness_index()`, `build_agents_scope()`, `build_search_index()`,
e indiretamente por `build_briefing()`.

### O que faz

Calcula um número entre 0.0 e 1.0 representando o quão "atual" é uma nota.
Usa decaimento exponencial: quanto mais tempo sem verificação, menor o score.

**Fórmula:**

```
freshness = e^(-decay_rate × semanas_decorridas)
```

onde `semanas_decorridas = (hoje - data_referência).days / 7.0`

**Data de referência (prioridade):**
1. Campo `last_verified` do frontmatter (se presente)
2. Campo `created` do frontmatter (fallback)
3. Ausência de ambos → retorna `0.5` (incerto, sem calcular)

**Seleção do `decay_rate` (três passos):**
1. Se `decay_rate` está no frontmatter da nota → usa esse valor (frontmatter vence)
2. Senão → lookup em `DEFAULT_DECAY_RATES` por `type` da nota
3. Exceção: `type=project` + `status=paused` → força `decay_rate = 0.10` (dobra o padrão de 0.05)

**Tabela de defaults por tipo:**

| Tipo | decay_rate/semana | Half-life |
|------|-------------------|-----------|
| infra | 0.15 | 32 dias |
| feedback | 0.08 | 61 dias |
| project (active) | 0.05 | 97 dias |
| project (paused) | 0.10 | 48 dias |
| pattern | 0.03 | 162 dias |
| playbook | 0.02 | 243 dias |
| rule | 0.01 | 485 dias |
| agent | 0.01 | 485 dias |
| meta | 0.01 | 485 dias |

Half-life = tempo para freshness cair de 1.0 para 0.5 = `ln(2) / decay_rate × 7` dias.

### Exemplo numérico real

Nota: `deploy-hostinger-process` (tipo `infra`, `decay_rate=0.15`, `last_verified=2026-04-29`)
Calculado em 2026-05-23:

```
semanas_decorridas = 24 dias / 7 = 3.429 semanas
freshness = e^(-0.15 × 3.429)
          = e^(-0.5143)
          = 0.598
```

Classificação resultante:
- fresh (>0.7)? Não
- aging (0.3–0.7)? Sim
- stale (<0.3)? Não
- needs_review (<0.5)? Não (score 0.598 > threshold 0.5)

Tempo para atingir cada limiar com decay_rate=0.15 (tipo infra):

| Limiar | Tempo |
|--------|-------|
| 0.7 (fresh→aging) | 17 dias |
| 0.5 (needs_review) | 32 dias |
| 0.3 (aging→stale) | 56 dias |
| 0.2 (stale hard) | 75 dias |

### Edge cases

**Data em formato ISO com timezone** (`2026-05-22T15:48:31.000Z`):
O parse usa `datetime.strptime(str, "%Y-%m-%d")` que falha em timestamps com hora.
Resultado: `ValueError` → capturado → retorna `0.5` (incerto).
Impacto real: notas cujo campo `created` tem timestamp ISO completo (geradas pelo
consciousness-engine) usam `last_verified` (que é `YYYY-MM-DD` curto) quando disponível.
Se apenas `created` existe em formato ISO → freshness fica travado em 0.5.

**Nota sem nenhuma data:** retorna `0.5` direto, sem calcular.

**Nota com `decay_rate` no frontmatter:** frontmatter vence completamente o DEFAULT.
Não há override por `status=paused` se o rate já está no frontmatter.

---

## 2. Classificação de Freshness (Categorias)

### Onde vive

Função `compute_health(notes, freshness_index, graph)` — linhas 444–491.
Função `print_health()` — linhas 494–532 (display).
Função `build_briefing()` — linha 569 (indicadores visuais).

### O que faz

Classifica cada nota em uma de quatro categorias com base no freshness score.
Existem **dois sistemas de threshold paralelos** no mesmo codebase:

**Sistema A — Health Report (compute_health, linha 451–453):**

| Categoria | Condição | Cor |
|-----------|----------|-----|
| fresh | score > 0.7 | verde |
| aging | 0.3 <= score <= 0.7 | amarelo |
| stale | score < 0.3 | vermelho |

**Sistema B — Freshness Index (build_freshness_index, linhas 245–247):**

| Campo | Condição | Descrição |
|-------|----------|-----------|
| `needs_review` | score < alert_threshold | alerta configurável por nota |
| `stale` | score < 0.2 | limiar duro de obsolescência |

**Diferença crítica entre os dois sistemas:**

- `stale` no health report = score < 0.3
- `stale` no freshness index = score < 0.2
- São thresholds diferentes para a mesma palavra "stale"

O `alert_threshold` é lido do frontmatter (`fm.get("alert_threshold", 0.5)`).
Nenhuma nota no vault atual usa `alert_threshold` customizado — todas ficam com 0.5.

### Exemplo numérico

Nota com freshness=0.25:
- Health report → categorizada como `stale` (0.25 < 0.3)
- Freshness index → `stale=True` (0.25 > 0.2)? Não. `stale=False` (0.25 > 0.2).
- Freshness index → `needs_review=True` (0.25 < 0.5 alert_threshold)

Nota com freshness=0.15:
- Health report → `stale` (0.15 < 0.3)
- Freshness index → `stale=True` (0.15 < 0.2)
- Freshness index → `needs_review=True` (0.15 < 0.5)

### Edge case

Nota com score exatamente 0.3 cai na categoria `aging` no health report
(`0.3 <= score <= 0.7` é inclusivo nos dois extremos).

---

## 3. Orphan Detection

### Onde vive

Dentro de `compute_health()` — linhas 457–462.
Também consultado em `print_health()` para exibir a lista.

### O que faz

Uma nota é considerada **órfã** se não aparece como `source` nem como `target`
em nenhuma edge do grafo de links.

**Algoritmo (4 linhas):**

```python
linked_ids = set()
for edge in graph["edges"]:
    linked_ids.add(edge["source"])   # quem aponta para alguém
    linked_ids.add(edge["target"])   # quem é apontado por alguém
node_ids = {n["id"] for n in graph["nodes"]}
orphans = node_ids - linked_ids
```

**O grafo é construído exclusivamente a partir do campo `links` do frontmatter** (ver `build_graph()`, linhas 161–183). Links no corpo markdown (estilo `[[nota]]`) não são
processados pelo `cortex_engine.py` — apenas os links em YAML estruturado contam.

**Consequência:** uma nota pode ter `[[wikilinks]]` no corpo e ainda ser considerada
orphan pelo CORTEX se não tiver `links:` no frontmatter.

### Exemplo numérico real

Vault atual (2026-05-23): 894 nodes, 12 orphans.

Nota orphan real: `heuristic-content-quando-criar-material-educacional-sobre-framework-pr-prio-e`

Frontmatter:
```yaml
links:
- target: mastra-suspend-resume-nativo-em-workflows-hitl-primeiro-classe
  type: auto-linked       # lista vazia = 0 out-links
created: '2026-05-22T15:48:31.000Z'
last_verified: '2026-05-22'
```

No grafo:
- Out-links (aparece como source): 0
- In-links (aparece como target): 0
- Resultado: não está em `linked_ids` → incluída em `orphans`

Nota com links para comparar: `playbook-trafego`
- Out-links: 4 (aponta para outras 4 notas)
- In-links: 21 (21 notas apontam para ela)
- Resultado: está em `linked_ids` → não é orphan

### Edge cases

**Nota apontando para si mesma:** seria simultaneamente source e target, portanto
entraria em `linked_ids` e não seria orphan. Não há validação que impeça isso.

**Nota A aponta para nota B inexistente:** B não é um node do grafo mas entra em
`linked_ids` como target. Isso pode "esconder" uma nota inexistente da lista de
orphans. O CORTEX não valida se targets de edges existem como nodes.

**Notas com apenas out-links (sem in-links):** não são orphans pelo critério atual.
No vault atual: 354 notas têm out-links mas ninguém aponta para elas (semi-orphans
de entrada). O CORTEX não os distingue dos nodes normalmente conectados.

---

## 4. Decay Rate — Aplicação ao Longo do Tempo

### Onde vive

Definição dos defaults: linhas 38–47 (dicionário `DEFAULT_DECAY_RATES`).
Aplicação na criação de nota: `create_note()`, linha 706–707.
Aplicação no cálculo de freshness: `calculate_freshness()`, linhas 147–153.

### O que faz

O `decay_rate` é a "taxa de deterioração semanal" da relevância de uma nota.
Funciona como constante de decaimento exponencial na fórmula de freshness.

Ao criar uma nota via `create_note()`, o `decay_rate` é:
1. Calculado do DEFAULT baseado em `note_type`
2. Escrito no frontmatter da nota permanentemente

Isso significa que o `decay_rate` fica **fixo no frontmatter no momento da criação**.
Mudanças no `DEFAULT_DECAY_RATES` do código não afetam notas existentes —
apenas novas notas.

Para mudar o decay de uma nota existente: editar manualmente o frontmatter.

### Exemplo numérico comparativo

Cenário: duas notas criadas hoje (2026-05-23), verificadas em 12 semanas (3 meses):

| Tipo | decay_rate | freshness em 12 semanas |
|------|------------|--------------------------|
| infra | 0.15 | e^(-0.15×12) = 0.165 → stale |
| feedback | 0.08 | e^(-0.08×12) = 0.382 → aging |
| project | 0.05 | e^(-0.05×12) = 0.549 → aging |
| pattern | 0.03 | e^(-0.03×12) = 0.698 → aging |
| rule | 0.01 | e^(-0.01×12) = 0.887 → fresh |

### Edge cases

**Projeto pausado (project + status=paused):**
O override `decay_rate = 0.10` é aplicado **no momento do cálculo** de freshness,
não escrito no frontmatter. Isso cria uma discrepância: o frontmatter diz `decay_rate: 0.05`
mas o cálculo usa 0.10. Se a nota for `refresh`-ada e recalculada, a diferença é invisível
para quem lê o frontmatter.

**Nota tipo desconhecido (não listado em DEFAULT_DECAY_RATES):**
`DEFAULT_DECAY_RATES.get(note_type, 0.05)` → cai no default de 0.05 (mesma taxa de project).

---

## 5. last_verified — Quando e Por Quem é Atualizado

### Onde vive

Escrito na criação: `create_note()`, linha 695 (sempre `datetime.now().strftime("%Y-%m-%d")`).
Atualizado por reset: `refresh_note()`, linha 784 (mesmo formato).
Lido por: `calculate_freshness()`, linha 127.

### O que faz

O campo `last_verified` no frontmatter é a âncora temporal do freshness score.
Representa a última vez que um humano (ou agente) confirmou que a nota está correta.

**Quatro formas de atualizar `last_verified`:**

1. **Criação** (`ingest.sh` → `create_note()`): define automaticamente como hoje.
2. **Refresh manual** (`refresh.sh note_id` → `refresh_note()`): reescreve o frontmatter com data de hoje. O corpo da nota NÃO muda — apenas `last_verified`.
3. **Edição direta do frontmatter**: agente ou humano edita o `.md` manualmente.
4. **Nunca**: se a nota for criada e nunca mais tocada, `last_verified` fica igual a `created` e o freshness decai continuamente.

**Quem pode chamar `refresh.sh`:**
- Qualquer agente que detectou informação desatualizada (per `cortex-usage.md`)
- O script `refresh_aging_notes.sh` (automático, via cron ou manual)
- O CEO diretamente

### Discrepância: `created` com timestamp vs `last_verified` com data curta

Notas geradas pelo consciousness-engine têm `created` em formato ISO completo
(`2026-05-22T15:48:31.000Z`). O CORTEX prioriza `last_verified` na fórmula —
se `last_verified` estiver presente em formato `YYYY-MM-DD`, o cálculo funciona normalmente.
Se `last_verified` estiver ausente e `created` for ISO completo, o parse falha e
o freshness trava em 0.5 (incerto).

---

## 6. Freshness Boost na Busca

### Onde vive

Função `query()`, linhas 403–405.

### O que faz

O freshness não apenas categoriza notas — também penaliza notas antigas nos resultados
de busca. Após calcular o score BM25, aplica um multiplicador:

```
final_score = bm25_score × (0.5 + 0.5 × freshness)
```

**Efeito prático:**

| Freshness | Multiplicador | Penalidade |
|-----------|---------------|------------|
| 1.0 (fresh) | 1.00 | 0% |
| 0.7 (limiar aging) | 0.85 | 15% |
| 0.5 (needs_review) | 0.75 | 25% |
| 0.3 (limiar stale) | 0.65 | 35% |
| 0.0 (decaído total) | 0.50 | 50% |

**Nota importante:** uma nota completamente decaída (freshness=0) ainda recebe
50% do seu score BM25. O freshness nunca zera um resultado de busca — apenas
o penaliza em até 2x versus uma nota fresquíssima com mesma relevância textual.

---

## 7. Discrepâncias e Inconsistências Encontradas

### 7.1 Dois limiares para "stale"

| Contexto | Limiar "stale" |
|----------|----------------|
| `compute_health()` — health report | score < 0.3 |
| `build_freshness_index()` — campo `stale` | score < 0.2 |

Uma nota com score=0.25 é "stale" no health report mas NÃO tem `stale=True`
no freshness-index. Os dois sistemas usam a mesma palavra com limiares diferentes.

### 7.2 Override silencioso de project pausado

O `decay_rate = 0.10` para `project+paused` é aplicado **em memória** no cálculo,
mas **não escrito** no frontmatter. O frontmatter continua dizendo `decay_rate: 0.05`.
Quem lê o frontmatter diretamente (sem passar pelo `calculate_freshness`) vê um valor
diferente do que o engine efetivamente usa.

### 7.3 Freshness calculado em dois índices separados

O `freshness` score aparece tanto em `freshness.json` quanto em `search-index.json`.
Ambos chamam `calculate_freshness()` na mesma execução de `build_all_indexes()`,
portanto são idênticos quando construídos juntos. Mas se alguém chamar
`build_freshness_index()` isoladamente (sem reconstruir o search-index), os dois
índices podem divergir.

### 7.4 Wikilinks no corpo não criam edges

Links no formato `[[nota-alvo]]` no corpo markdown são ignorados pelo engine.
Apenas `links:` no frontmatter YAML cria edges no grafo.
Isso significa que a detecção de orphans é cega para links textuais.

---

## Resumo executivo para @rag-architect

| Fórmula | Implementada em | Status |
|---------|-----------------|--------|
| Freshness (decaimento exponencial) | `calculate_freshness()` L122 | Funcional, 1 edge case de parse |
| Categorias fresh/aging/stale | `compute_health()` L444 + `build_freshness_index()` L230 | 2 limiares diferentes para "stale" |
| Orphan detection | `compute_health()` L457 | Ignora wikilinks no corpo |
| Decay rate selection | `calculate_freshness()` L147 + `DEFAULT_DECAY_RATES` L38 | Override pausado não grava no frontmatter |
| last_verified reset | `refresh_note()` L769 | Funcional, manual ou via script |
| Freshness boost na busca | `query()` L403 | Score mínimo 50% — nunca zera |

Decisões que dependem do @rag-architect:
- Unificar os dois limiares de "stale" (0.2 vs 0.3)?
- Gravar o decay_rate efetivo (com override de paused) no frontmatter?
- Processar wikilinks do corpo como edges no grafo?
- Separar `needs_review` de `stale` em campos com nomes mais distintos?