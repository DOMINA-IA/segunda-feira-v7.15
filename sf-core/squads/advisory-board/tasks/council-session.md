---
task: councilSession()
responsavel: "@board-chair"
responsavel_type: Agent
atomic_layer: Task
elicit: true

Entrada:
  - campo: decision
    tipo: string
    origem: User Input
    obrigatorio: true
  - campo: context
    tipo: string
    origem: User Input
    obrigatorio: false
  - campo: group_mode
    tipo: enum
    valores: [full, similar, contrarian]
    origem: User Input
    obrigatorio: false
    default: full

Saida:
  - campo: council_output
    tipo: string
    destino: Console
    persistido: true
  - campo: decision_log_entry
    tipo: object
    destino: data/decision-log.yaml
    persistido: true

Checklist:
  - "[ ] CEO profile loaded from config/ceo-profile.yaml"
  - "[ ] Similar group advisors consulted (if applicable)"
  - "[ ] Contrarian group advisors consulted (if applicable)"
  - "[ ] Tensions between groups identified"
  - "[ ] Decision registered in decision-log.yaml with follow-up date"
---

# Task: Council Session — Sessão de Conselho com Grupos

**Task ID:** COUNCIL-001
**Version:** 1.0.0
**Command:** `*council {decisão}` | `*similar {decisão}` | `*contrarian {decisão}`
**Agent:** Board Chair (board-chair)
**Purpose:** Sessão de conselho com split Similar vs. Contrário baseado no perfil comportamental do CEO.

---

## Context

Esta task implementa o conceito de "Conclave" do Alan Nicolas: conselheiros calibrados pelo
DNA mental do CEO (DISC, Eneagrama, Big Five, MBTI), divididos em dois grupos:

- **Similar** (pensam como o CEO): Munger, Naval, Dalio, Thiel, Hormozi
- **Contrário** (desafiam o CEO): Sinek, Brené, Lencioni, Sivers, Hoffman, Chouinard

O split permite:
- `*council` — Todos opinam (full board)
- `*similar` — Só grupo similar (reforço/refinamento)
- `*contrarian` — Só grupo contrário (desafio/contraste)

---

## Inputs

| Input | Source | Required | Default |
|-------|--------|----------|---------|
| `decision` | Decisão ou pergunta estratégica | YES | — |
| `context` | Contexto do negócio, dados, restrições | NO | Usar contexto disponível |
| `group_mode` | `full`, `similar`, ou `contrarian` | NO | `full` |
| `urgency` | Timeline da decisão | NO | — |

---

## Preconditions

1. Carregar `config/ceo-profile.yaml` para calibrar as respostas
2. Decisão claramente formulada
3. Pelo menos 3 conselheiros relevantes disponíveis

---

## Execution Phases

### Phase 1: Load CEO Profile & Frame

1. **Ler** `config/ceo-profile.yaml`
2. **Identificar** o perfil comportamental do CEO (DC, 5w6, INTJ)
3. **Reformular** a decisão do CEO de forma precisa
4. **Determinar** quais conselheiros de cada grupo são mais relevantes
5. **Selecionar** 3-5 do grupo similar + 3-5 do grupo contrário (se full mode)

### Phase 2: Similar Group Responds

**Para cada conselheiro do grupo similar selecionado:**

```markdown
📊 GRUPO SIMILAR (pensam como você):

{icon} **{Nome}:**
"{Resposta na voz autêntica do conselheiro}"

**Framework aplicado:** {qual framework usou}
**Veredicto:** {apoiar | refinar | cautela}
**Ação sugerida:** {ação específica}
```

**Regras do grupo similar:**
- Responder usando seus frameworks específicos
- Reforçar ou refinar o raciocínio do CEO
- Apontar riscos que o CEO pode ter perdido
- Usar linguagem direta (calibrada pelo perfil DC do CEO)
- Cada resposta: máximo 3-4 parágrafos curtos

### Phase 3: Contrarian Group Responds

**Para cada conselheiro do grupo contrário selecionado:**

```markdown
🔄 GRUPO CONTRÁRIO (desafiam sua visão):

{icon} **{Nome}:**
"{Resposta na voz autêntica do conselheiro}"

**Perspectiva que desafia:** {qual aspecto desafia}
**Pergunta incômoda:** {pergunta que força reflexão}
**Alternativa proposta:** {caminho diferente}
```

**Regras do grupo contrário:**
- DEVE discordar de pelo menos um aspecto da decisão
- Usar perspectiva que o CEO naturalmente não considera
- Fazer uma pergunta incômoda que force reflexão
- Propor alternativa concreta, não só crítica
- Ser respeitoso mas firme (calibrado pelo perfil do CEO)

### Phase 4: Tension Analysis

```markdown
⚡ ANÁLISE DE TENSÕES:

**Onde concordam (Similar + Contrário):**
- {ponto de concordância}

**Onde divergem:**
- {tensão 1}: Similar diz X, Contrário diz Y
- {tensão 2}: Similar diz X, Contrário diz Y

**Tensão mais importante:**
{qual tensão merece mais atenção e por quê}
```

### Phase 5: Synthesis & Recommendation

```markdown
🏛️ SÍNTESE DO BOARD CHAIR:

**Recomendação:**
{recomendação clara baseada na síntese das perspectivas}

**Dissenting view (voto vencido):**
{perspectiva minoritária que merece atenção}

**Próximos passos:**
1. {ação concreta 1}
2. {ação concreta 2}
3. {ação concreta 3}

**Pergunta de follow-up (30 dias):**
"{pergunta que será feita em 30 dias para avaliar a decisão}"
```

### Phase 6: Decision Log

**Registrar no `data/decision-log.yaml`:**

```yaml
- id: DEC-{NNN}
  date: "{hoje}"
  question: "{decisão original}"
  context: "{contexto}"
  advisors_consulted:
    similar: [{lista}]
    contrarian: [{lista}]
  perspectives:
    agreement: "{concordância}"
    disagreement: "{divergência}"
    key_insight: "{insight mais valioso}"
  recommendation: "{recomendação do board}"
  decision: "PENDING — aguardando decisão do CEO"
  follow_up_date: "{hoje + 30 dias}"
  status: open
```

---

## Output Format

### Full Council (*council)

```
🏛️ COUNCIL SESSION — {data}
Decisão: "{decisão}"
Modo: Full Board (Similar + Contrário)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 GRUPO SIMILAR (pensam como você):

🧠 Charlie Munger: "..."
⚡ Naval Ravikant: "..."
📈 Ray Dalio: "..."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔄 GRUPO CONTRÁRIO (desafiam sua visão):

🎯 Simon Sinek: "..."
💛 Brené Brown: "..."
👥 Patrick Lencioni: "..."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ TENSÕES:
...

🏛️ SÍNTESE:
...

📋 Decisão registrada: DEC-{NNN} | Follow-up: {data+30}
```

### Similar Only (*similar)

Mesmo formato, mas apenas grupo similar responde.

### Contrarian Only (*contrarian)

Mesmo formato, mas apenas grupo contrário responde.

---

## Post-Conditions

```yaml
post-conditions:
  - [ ] Todos os conselheiros selecionados responderam na sua voz autêntica
    tipo: quality-check
    validação: "Cada resposta usa frameworks e vocabulário do conselheiro"
  - [ ] Tensões entre grupos foram identificadas
    tipo: quality-check
    validação: "Pelo menos 1 tensão explícita identificada"
  - [ ] Síntese com recomendação clara e dissenting view
    tipo: quality-check
    validação: "Recomendação acionável + voto vencido"
  - [ ] Decisão registrada no decision-log.yaml
    tipo: output-validation
    validação: "Entry criada com follow-up date"
  - [ ] Próximos passos concretos definidos
    tipo: quality-check
    validação: "Pelo menos 2 ações concretas"
```

---
*AIOS Task - council-session.md — Created 2026-03-17*
