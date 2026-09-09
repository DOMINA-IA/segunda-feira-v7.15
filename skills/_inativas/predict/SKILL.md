---
name: predict
description: "Sugestões preditivas sobre o que o CEO provavelmente vai pedir em seguida — cruza estado do negócio, padrões temporais (dia da semana, fase do lançamento) e histórico de comportamento para antecipar ações e pré-carregar recursos antes de ser pedido. Use no fim de sessões longas ou sob demanda para antecipar o próximo passo. NOT for: detectar padrões factuais nos dados operacionais (CPL, infra, conteúdo, leads) — isso é /pattern-detector."
tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
---

# /predict — Sugestões Preditivas

> **Tipo:** Skill de antecipação | **Agente padrão:** @sf-master
> **Trigger:** Final de cada sessão longa, ou sob demanda
> **Output:** Lista de ações prováveis + preparação prévia

## Objetivo

Antecipar o que o CEO vai precisar em seguida, baseado em padrões de comportamento, estado do negócio e calendário. Preparar contexto e recursos ANTES de ser pedido.

---

## Processo

### 1. Analisar Estado Atual
Ler e cruzar:
- `~/feedback-loop/results.json` — campanhas ativas, métricas
- `~/broadcast/signals.json` — sinais pendentes
- `~/broadcast/mailbox/*.json` — mensagens não processadas
- `~/framework/observations/opportunities.md` — oportunidades em aberto
- Memórias recentes (últimos 7 dias)

### 2. Analisar Padrões Temporais
- **Dia da semana:** segunda = planejamento, sexta = review, domingo = conteúdo
- **Fase do lançamento:** captação → evento → cart open → pós-venda
- **Ciclo mensal:** início = estratégia, meio = execução, fim = análise

### 3. Analisar Contexto do Lançamento Ativo
Se há lançamento em andamento (ex: AI FIRST):
- Quantos dias faltam para o evento?
- Campanhas estão performando? Precisam de ajuste?
- Conteúdo orgânico está alinhado com a captação?
- WhatsApp Bot está configurado e funcional?

### 4. Gerar Predições

Para cada predição, estruturar:

```markdown
### Predição #N — [Ação provável]
- **Probabilidade:** X% (baseado em: [evidência])
- **Timing:** [quando o CEO provavelmente vai pedir]
- **Preparação:** [o que posso adiantar agora]
- **Recursos necessários:** [dados, arquivos, acessos]
```

### 5. Pré-carregar Recursos
Para predições com >70% de probabilidade:
- Ler arquivos relevantes
- Preparar dados necessários
- Gerar rascunhos se aplicável
- Deixar contexto pronto para execução imediata

## Exemplos de Predições

| Contexto | Predição | Preparação |
|----------|----------|------------|
| Campanha rodando há 2 dias | "Vai pedir relatório de performance" | Puxar dados da API, gerar tabela |
| Evento em 5 dias | "Vai revisar conteúdo das lives" | Ler roteiros, verificar agenda |
| Domingo à noite | "Vai planejar conteúdo da semana" | Rodar /micro-trend, preparar brief |
| Post performou muito bem | "Vai querer replicar o formato" | Analisar elementos, sugerir variações |
| CPL subiu | "Vai querer pausar ou ajustar" | Preparar comparativo, sugerir ação |

## Output

```markdown
# Predições — [DATA]

## 🎯 Alta Probabilidade (>70%)
1. [predição + preparação pronta]

## 📊 Média Probabilidade (40-70%)
1. [predição + recursos identificados]

## 💭 Baixa Probabilidade (<40%)
1. [predição registrada como observação]
```

---

## Regras
- Predições DEVEM ser baseadas em dados, não em suposição genérica
- Não executar ações — apenas preparar e sugerir
- Atualizar predições quando contexto muda
- Se predição se confirma → registrar como padrão no feedback loop
- Se predição falha → ajustar modelo mental

---

## Extensão v2 (24-Mai-2026, absorvido do ruflo worker `predict`)

### Algoritmo de Scoring (PageRank no grafo de transições)

```python
# Sublinear PageRank no grafo de transições entre agentes
# Personalized: peso do contexto atual

score(agent_X, context) =
  base_score(agent_X) +
  0.4 × day_pattern(agent_X, today) +
  0.3 × cooccurrence(agent_X, last_3_agents) +
  0.2 × project_affinity(agent_X, active_project) +
  0.1 × event_trigger(agent_X, active_signals)
```

Fontes para os sinais:
- `day_pattern`: histórico em `~/consciousness/memory/episodic/*.jsonl` agrupado por dia da semana
- `cooccurrence`: matriz de transições consecutivas entre agentes
- `project_affinity`: tags de projeto nos episódios
- `event_trigger`: `~/broadcast/signals.json` ativos

### Detecção de Anomalias

Sinalizar quando padrão atual desvia >2σ da média histórica:
- "Você usou @advogado-do-diabo 3x esta semana — média histórica: 0.5x"
- "Saturday sem @content (90% típico) — anormal"

### Multi-LLM (extensão de economia)

| Operação | Modelo |
|----------|--------|
| Leitura histórico + cálculo scores | Python+NumPy local — $0 |
| Detecção anomalia (z-score) | scipy local — $0 |
| Geração explicação humana | Haiku (200-300 tokens) |
| Predição estratégica complexa | Sonnet apenas se solicitado |

100% local em condição padrão. Zero custo de tokens para predições básicas.

### Integração com `/preload`

Top 3 predições alimentam `/preload --agents @x,@y,@z`. Cache warming proativo reduz latência de primeira chamada do dia.

Origem da extensão: ruflo worker `predict` + ScheduleWakeup 270s cache pattern.

