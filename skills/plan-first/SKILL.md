---
name: plan-first
description: "Rascunha plano estruturado (objetivo, sub-tarefas, riscos, critério de sucesso, reversibilidade) antes de executar — Portão 2 do EROS. Use em tarefa multi-arquivo, irreversível, em produção, com 3+ agentes ou confidence < 0.7. NOT for: 1…"
harnesses:
  - claude-code: full
  - codex: native
  - cursor: limited
  - aider: limited
---

# /plan-first — Pense Antes de Fazer

## Princípio

Tarefas com múltiplas etapas, alto impacto ou baixa reversibilidade devem ter PLANO escrito antes da execução. Plan Mode reduz retrabalho identificando gaps lógicos antes que virem custo real.

**Regra de ouro:** "Se você não consegue descrever o plano em <10 bullets, ainda não entendeu a tarefa."

## Quando USAR (obrigatório)

- Mudanças em múltiplos arquivos/sistemas
- Operações irreversíveis (delete, drop, force-push, migração)
- Tarefas que tocam produção (VPS, campanhas pagas, dados de cliente)
- Integração entre 3+ agentes
- Confidence < 0.7 em qualquer parte do escopo
- Tarefas com prazo > 1h

## Quando NÃO usar (overkill)

- Resposta conversacional
- 1 comando, 1 arquivo, < 5 min
- Operação determinística com regra clara (lint, format, build conhecido)
- Bug fix óbvio com causa identificada

## Formato do Plano (obrigatório)

```
═══════════════════════════════════════════
PLANO — {nome curto da tarefa}
═══════════════════════════════════════════

OBJETIVO (1 linha):
  {resultado mensurável que define sucesso}

CONTEXTO:
  - Situação atual: {estado pré-execução}
  - Restrições: {limites de tempo/recurso/risco}
  - Premissas: {o que estou assumindo verdadeiro}

SUB-TAREFAS (ordem de execução):
  1. {ação concreta} → {output esperado}
  2. {ação concreta} → {output esperado}
  3. ...

RISCOS IDENTIFICADOS:
  - 🔴 {risco crítico}: {mitigação}
  - 🟡 {risco médio}: {mitigação}

CRITÉRIO DE SUCESSO:
  - {métrica/observação verificável}
  - {teste que confirma}

REVERSIBILIDADE:
  - Backup: {snapshot/git ref}
  - Rollback: {comando para reverter}
  - Tempo de rollback: {< X min}

ESTIMATIVA: {N min/h}
CONFIDENCE GERAL: {0.0-1.0}
═══════════════════════════════════════════
```

## Fluxo

1. Agente recebe tarefa complexa
2. Identifica que se aplica (matriz acima)
3. Apresenta PLANO ao CEO no formato estruturado
4. **Aguarda aprovação explícita** antes de executar
5. Se CEO ajustar, refazer plano (não executar parcial)
6. Após aprovado, executar passo a passo
7. Ao final, reportar com diff plano vs realidade

## Integração com sistema existente

| Sistema | Como interage |
|---------|---------------|
| `eros-quality.md` Portão 2 | Plan-first é a operacionalização concreta — substitui "planejou?" por estrutura |
| `autonomous-execution.md` | Tarefas com risco médio/alto exigem Plan Mode antes de propor execução |
| `confidence-guardrails.md` | Confidence < 0.7 em qualquer sub-tarefa dispara Plan Mode automaticamente |
| `cortex-usage.md` (seção Cruzamento Obrigatório) | Plan deve incluir "lições de outro contexto aplicáveis" |

## Anti-Patterns

| Evitar | Por quê |
|--------|---------|
| Plano genérico ("vou fazer X") | Sem sub-tarefas concretas, não previne nada |
| Plano sem riscos identificados | Falsa segurança — todo plano tem riscos |
| Executar antes de aprovação | Quebra o ciclo — vira "Plano-decorativo" |
| Plan Mode em tarefa trivial | Burocracia que mata produtividade |
| Plano sem critério de sucesso mensurável | Não dá pra saber se acertou |

## Exemplo concreto

**Pedido CEO:** "migrar 20 agentes de Sonnet pra Haiku"

**Aplicar Plan-First?** SIM (múltiplos arquivos + impacto comportamental + reversibilidade depende)

**Plano gerado:**
```
═══════════════════════════════════════════
PLANO — Migrar 20 agentes Sonnet → Haiku
═══════════════════════════════════════════
OBJETIVO: Reduzir custo de tokens em ~75% nos agentes mecânicos sem perda mensurável de qualidade.

CONTEXTO:
  - 32 agentes hoje (11 Sonnet, 7 Opus, 13 sem model declarado)
  - Restrição: não posso degradar V4 (qualidade)
  - Premissa: tarefas mecânicas (filter, classify) toleram Haiku

SUB-TAREFAS:
  1. Auditar os 20 candidatos contra rule model-routing.md → lista validada
  2. Para cada agente: Edit no frontmatter (model: haiku) + git commit individual
  3. Rodar 3 invocações de cada para detectar regressão
  4. Se regressão > 20%: reverter aquele agente para Sonnet

RISCOS:
  - 🔴 Degradação de qualidade em raciocínio: rodar smoke test pós-migração
  - 🟡 Agentes interconectados podem cascatear erros: testar 1 a 1

CRITÉRIO DE SUCESSO:
  - 20 frontmatters atualizados sem warning
  - Smoke tests passam em 100% dos agentes migrados
  - Custo médio de invocação cai >= 60%

REVERSIBILIDADE:
  - Backup: git stash antes de cada Edit
  - Rollback: git revert dos commits
  - Tempo: < 5 min por agente

ESTIMATIVA: 2-3h
CONFIDENCE: 0.75
═══════════════════════════════════════════
```

CEO aprova → executa. CEO ajusta ("comece pelos 5 menos críticos") → refaz plano.

## Variantes

- **`/plan-first --quick`**: plano enxuto (3-4 linhas) para tarefas médias
- **`/plan-first --strict`**: exige aprovação por escrita do CEO antes de cada sub-tarefa
- **`/plan-first --review`**: revisar plano gerado em sessão anterior

## Quando o agente pode pular Plan-First

Apenas se TODAS estas condições forem verdadeiras:
1. Confidence > 0.85 em todas as sub-tarefas
2. Risco classificado como BAIXO (matriz autonomous-execution)
3. Reversível em <5 min
4. CEO autorizou explicitamente "execução direta"

Caso contrário: Plan-First é o caminho.
