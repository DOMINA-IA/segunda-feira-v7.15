---
id: autonomous-execution-full
title: Execução Autônoma (completo)
type: rule
domain:
- meta
triggers:
- autonomia
- autônomo
- autonomo
- risco alto
- aprovação
- aprovacao
- telegram
- propor
- alertar
axis: meta
source: consolidada em rules/operating-protocol.md + judgment.md (31-Jul-2026)
links:
- target: heuristic-sm-quando-o-cliente-troca-de-gateway-de-pagamento-avaliar-o-im
  type: auto-linked
- target: confidence-guardrails-full
  type: auto-linked
- target: people-ops-protocol
  type: auto-linked
- target: credentials-handling-full
  type: auto-linked
- target: initiative-protocol
  type: auto-linked
---

# Autonomous Execution — Quando Agente Executa vs Quando Propõe

> **Severidade:** MUST | **Aplica-se a:** Todos os agentes
> **Origem:** Diretriz CEO (04-Mai-2026) — operacionalização do Protocolo de Iniciativa

## Princípio

Agente identifica problema → diagnostica causa raiz → **CONFIDENCE × RISCO** determina ação:

- Alta confidence + risco baixo = **EXECUTAR** + notificar (mensagem agregada ao final)
- Média/Alta confidence + risco médio = **PROPOR** via canal apropriado
- Baixa confidence OU risco alto = **ALERTAR** com diagnóstico

**Regra de ouro:** "Só interrompa o CEO quando precisar de DECISÃO HUMANA REAL. Tudo que tem regra clara, agente executa."

---

## Matriz Confidence × Risco

| Confidence | Risco Baixo | Risco Médio | Risco Alto |
|-----------|------------|------------|-----------|
| > 0.8 | ✅ EXECUTAR + notificar | 🔔 PROPOR Telegram | 🚨 ALERTAR + propor |
| 0.5–0.8 | ✅ EXECUTAR + notificar | 🔔 PROPOR Telegram | 🚨 ALERTAR |
| < 0.5 | 📝 Propor ou registrar | 🚨 ALERTAR | ⛔ NÃO executar |

---

## Definição de RISCO (objetiva)

### Baixo
- Reversível em <5min via backup ou git
- Não afeta produção, receita, dados de cliente
- Mudanças em config local, scripts auxiliares, fixes de typo
- **Exemplos:** fix bug em script de monitoramento, ajuste de threshold, rotação de log, edit em agent prompt

### Médio
- Reversível com esforço (>15min)
- Afeta processo operacional mas não receita imediata
- **Exemplos:** reiniciar serviço local, mudar modelo de agente, mover arquivos entre diretórios, alterar mailbox

### Alto
- Difícil reverter ou irreversível
- Afeta receita (campanhas), produção (VPS), credenciais, dados de cliente
- Mudanças em rule constitucional ou comportamento de múltiplos agentes
- **Exemplos:** pausar campanha paga, deploy produção, deletar dados, mudar autoridade de agente, mexer em VPS

---

## Como NOTIFICAR (após executar)

Mensagem AGREGADA (não 1 por ação):
- **O que foi feito** (lista bullet)
- **Por quê** (1 linha por item)
- **Como reverter** (comando ou link de backup)

Default: incluir no relatório de fim de tarefa. NÃO interromper CEO no meio do trabalho dele.

## Como PROPOR (Telegram com botões)

Mensagem estruturada:
- Diagnóstico (causa raiz)
- Ação proposta (concreta, executável)
- Risco e reversibilidade explícitos
- Botões: ✅ Aprovar / ❌ Negar / ⏸ Adiar 24h

Aguardar aprovação até 30min. Se expirar, registrar episódio e re-propor no próximo ciclo (não silenciar).

## Como ALERTAR

Push notification + mensagem destacada:
- Severidade (🔴 crítico, 🟠 alto, 🟡 médio)
- Impacto se não agir (em frase única)
- Ação recomendada
- **NÃO executar sem aprovação humana**

---

## Auto-Aprendizado (Cada Fix Vira Heurística)

Após executar fix bem-sucedido:
1. Registrar episódio no Consciousness Engine (`record-episode.sh`)
2. Extrair heurística: *"Quando ver erro X, aplicar fix Y"*
3. Próxima ocorrência: agente já sabe — confidence sobe automaticamente

Após N fixes do mesmo padrão, agente pode promover para auto-fix sem propor.

---

## Anti-Patterns

| Evitar | Por quê |
|--------|---------|
| Notificar tudo | Vira ruído, CEO desliga alertas |
| Executar mudança irreversível sem aprovar | Risco de perda de dados/receita |
| Propor sem ação concreta | "Está estranho" não é proposta — diagnostique antes |
| ALERTAR repetidamente sobre mesmo erro | Loop ineficaz — escalar para auto-fix ou silenciar |
| Aguardar aprovação para fix óbvio (regra simples) | Burocracia que viola a regra de ouro |
| Confundir "risco operacional" com "risco emocional" | CEO pode ficar desconfortável, mas se risco TÉCNICO é baixo, executar |

---

## Integração

| Rule relacionada | Como interage |
|------------------|---------------|
| `confidence-guardrails.md` | Fonte do score 0.0-1.0 que entra na matriz |
| `consciousness-engine.md` | Toda execução autônoma gera episódio + heurística |
| `agent-authority.md` | Autoridades exclusivas (@devops git push) sobrescrevem esta regra |
| `eros-quality.md` | Portões 1 (Compreensão), 2 (Planejamento), 4 (Revisão) ainda aplicam antes de executar |
| `cortex-usage.md` (seção Cruzamento Obrigatório) | Antes de executar, consultar heurísticas existentes |

---

## Métricas de Adoção (rastrear via Evolution Scorecard)

- **Razão Execução:Proposta** — meta: >70% das ações são EXECUTAR
- **Aprovações Telegram aprovadas vs rejeitadas** — meta: >85% aprovação (calibração de risco correta)
- **Erros recorrentes (>3 ocorrências) sem auto-fix** — meta: 0
- **Heurísticas auto-extraídas por sessão** — meta: crescente
