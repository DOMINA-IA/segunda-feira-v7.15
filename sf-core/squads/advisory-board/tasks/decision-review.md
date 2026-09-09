---
task: decisionReview()
responsavel: "@board-chair"
responsavel_type: Agent
atomic_layer: Task
elicit: true

Entrada:
  - campo: decision_id
    tipo: string
    origem: User Input
    obrigatorio: false
  - campo: review_mode
    tipo: enum
    valores: [single, all-open, monthly]
    origem: User Input
    obrigatorio: false
    default: all-open

Saida:
  - campo: review_output
    tipo: string
    destino: Console
    persistido: false
  - campo: updated_log
    tipo: object
    destino: data/decision-log.yaml
    persistido: true

Checklist:
  - "[ ] Decision log loaded from data/decision-log.yaml"
  - "[ ] Open decisions identified"
  - "[ ] CEO provided outcome for each decision"
  - "[ ] Learning captured and logged"
  - "[ ] Decision status updated (reviewed/closed)"
---

# Task: Decision Review — Follow-up de Decisões Passadas

**Task ID:** REVIEW-001
**Version:** 1.0.0
**Command:** `*review-decision [DEC-id]` | `*review-all` | `*monthly-review`
**Agent:** Board Chair (board-chair)
**Purpose:** Revisar decisões passadas, avaliar resultados e capturar aprendizados. Os conselheiros cobram o CEO.

---

## Context

A parte mais valiosa do advisory board — como o Alan Nicolas disse, os conselheiros
"anotam as decisões e depois perguntam: deu certo? não deu? por que não deu?"

Esta task implementa o ciclo de follow-up:
1. Carregar decisões em aberto do decision-log.yaml
2. Perguntar ao CEO o que aconteceu
3. Os conselheiros originais avaliam o resultado
4. Capturar aprendizado
5. Atualizar o log

---

## Inputs

| Input | Source | Required | Default |
|-------|--------|----------|---------|
| `decision_id` | ID da decisão (DEC-001) | NO | Todas em aberto |
| `review_mode` | `single`, `all-open`, `monthly` | NO | `all-open` |

---

## Execution Phases

### Phase 1: Load Decision Log

1. Ler `data/decision-log.yaml`
2. Filtrar decisões com `status: open`
3. Identificar decisões com `follow_up_date` vencido ou próximo
4. Ordenar por data (mais antigas primeiro)

### Phase 2: Present Open Decisions

```markdown
📋 DECISÕES EM ABERTO — Review

| # | ID | Data | Decisão | Follow-up | Conselheiros |
|---|-----|------|---------|-----------|-------------|
| 1 | DEC-001 | 2026-03-17 | "Investir R$10K em ads..." | 2026-04-17 | Munger, Naval, Sinek |
| 2 | DEC-002 | 2026-03-20 | "Lançar mini-produto..." | 2026-04-20 | Hormozi, Dalio |

Qual decisão quer revisar? (número, ID, ou "todas")
```

### Phase 3: CEO Reports Outcome

Para cada decisão em review:

```
ELICIT: Resultado da Decisão DEC-{id}

📋 Decisão: "{resumo da decisão}"
📅 Tomada em: {data}
🎯 Resultado esperado: "{expected_outcome}"

O que aconteceu desde então?
- Qual foi o resultado real?
- Funcionou como esperado?
- O que surpreendeu (positivo ou negativo)?

→ Validation: Precisa de informação concreta
```

### Phase 4: Advisors Evaluate

**Chamar os mesmos conselheiros que foram consultados na decisão original:**

```markdown
📊 AVALIAÇÃO DOS CONSELHEIROS:

{icon} **{Nome}** (consultado na decisão original):
"Minha avaliação: {avaliação na voz do conselheiro}"

**O que eu teria feito diferente:** {se aplicável}
**Padrão identificado:** {padrão que pode ser aplicado no futuro}
```

**Regras da avaliação:**
- Ser honesto — se deu errado, dizer por quê
- Identificar se a decisão estava certa mas a execução falhou
- Identificar se os dados mudaram (decisão era certa na época)
- Capturar padrão reutilizável para futuras decisões
- Não ser condescendente — ser direto como o perfil DC exige

### Phase 5: Capture Learning

```markdown
📝 APRENDIZADO CAPTURADO:

**Decisão:** DEC-{id}
**Resultado:** {sucesso | parcial | falhou}
**Score (1-10):** {nota da qualidade da decisão em retrospecto}

**O que aprendemos:**
1. {learning 1}
2. {learning 2}

**Padrão reutilizável:**
"{regra ou princípio que pode ser aplicado em decisões futuras}"

**Atualização de perfil:**
{Se o resultado revela algo novo sobre como o CEO decide, anotar}
```

### Phase 6: Update Log

Atualizar `data/decision-log.yaml`:

```yaml
  review:
    date: "{hoje}"
    outcome: "{resultado real}"
    learning: "{aprendizado capturado}"
    score: {1-10}
    pattern: "{padrão identificado}"
  status: reviewed  # ou closed
```

---

## Monthly Review (*monthly-review)

Uma vez por mês, o Board Chair faz review completo:

```markdown
🏛️ MONTHLY REVIEW — {mês/ano}

📊 RESUMO DO MÊS:
- Decisões tomadas: {n}
- Decisões revisadas: {n}
- Score médio: {média}
- Ainda em aberto: {n}

🎯 TOP DECISÕES (melhor score):
1. DEC-{id} — {resumo} — Score: {n}/10

⚠️ DECISÕES QUE FALHARAM:
1. DEC-{id} — {resumo} — {por que falhou}

📝 PADRÕES IDENTIFICADOS:
1. {padrão 1}
2. {padrão 2}

🔮 RECOMENDAÇÃO PARA O PRÓXIMO MÊS:
{recomendação baseada nos padrões identificados}
```

---

## Post-Conditions

```yaml
post-conditions:
  - [ ] Decisões revisadas com input do CEO
    tipo: quality-check
    validação: "CEO forneceu resultado real"
  - [ ] Conselheiros originais avaliaram
    tipo: quality-check
    validação: "Cada conselheiro deu sua avaliação na voz autêntica"
  - [ ] Aprendizado capturado
    tipo: quality-check
    validação: "Pelo menos 1 learning e 1 padrão por decisão"
  - [ ] Decision log atualizado
    tipo: output-validation
    validação: "Status e review preenchidos no YAML"
```

---
*AIOS Task - decision-review.md — Created 2026-03-17*
