---
id: confidence-guardrails-full
title: Confidence Guardrails (completo)
type: rule
domain:
- meta
triggers:
- confidence
- confiança
- confianca
- score
- calibração
- calibracao
- alucinação
- alucinacao
- fonte primária
- verificar
axis: meta
source: consolidada em rules/judgment.md (31-Jul-2026)
links:
- target: agent-communication-full
  type: auto-linked
- target: consciousness-engine-full
  type: auto-linked
- target: autonomous-execution-full
  type: auto-linked
---

# Confidence Guardrails (resumo)
> Severidade: MUST (pesquisa) / SHOULD (demais) | Agentes que fazem afirmações factuais | Versão completa on-demand (triggers: confidence, confiança, score, verificar, alucinação, fonte, calibração)

**Regra de ouro:** "Afirmação sem confiança declarada é afirmação sem responsabilidade." Formato: `[confidence: 0.8]` após a afirmação, escala 0.0–1.0, incrementos de 0.1.

Exemplo: "O CPL médio do nicho é R$8,50. [confidence: 0.3] — VERIFICAR: estimativa sem fonte primária."

## Faixas e ação obrigatória

| Faixa | Classificação | Ação |
|-------|--------------|------|
| 0.0–0.4 | Baixa | Marcar **VERIFICAR**, citar fonte, não basear decisão nisso |
| 0.5–0.7 | Moderada | Incluir ressalva explícita |
| 0.8–1.0 | Alta | Afirmar direto (fonte recomendada) |

## Quando aplicar
SIM: mercado/tendências/dados, concorrentes/benchmarks, recomendações estratégicas.
NÃO: comandos técnicos, código verificável por execução, leitura de arquivo local, docs oficiais, logs/deploy (observação direta).

## Por tipo de agente
- **MUST** (@market-intel, @analyst, @advogado-do-diabo, @mestre-do-conselho): score + fonte em toda afirmação factual.
- **SHOULD** (@pm, @po, @sm, @architect): score em estimativas/avaliações de impacto.
- **EXEMPT** (@dev, @devops, @data-engineer): dispensado em operações técnicas; @content/@copywriter só em afirmações de performance/conversão.

## Integração
EROS Portão 1 (identifica premissa fraca) e Portão 3 (score <0.5 exige verificação antes de decisão). Model routing: score <0.5 em tarefa crítica → escalar Opus; em tarefa simples → marcar VERIFICAR e seguir.

## Anti-patterns principais
Score em toda frase (poluição); score 1.0 inflado sem fonte; score <0.5 sem ação de verificação; omitir score em pesquisa (MUST sem exceção).

Detalhe completo (tabela de calibração 0.1–1.0, exemplos por faixa, anti-patterns) na versão on-demand.
