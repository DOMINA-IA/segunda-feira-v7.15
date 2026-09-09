---
id: production-refactor-protocol-instrumenta-o-leve-antes-de-modulariza-o-full
title: Production Refactor Protocol — Instrumentação leve antes de modularização full
type: rule
status: active
created: '2026-04-30'
last_verified: '2026-04-30'
domain:
- dev
- meta
- architect
agents:
- dev
- architect
- qa
- devops
tags:
- rule
- refactor
- production-safe
- observability
- technical-debt
decay_rate: 0.01
links:
- target: patch-por-ncora-por-que-replace-com-string-erra-o-alvo-e-como-provar-que-n-o-errou
  type: auto-linked
- target: escape-em-template-literal-os-3-modos-de-quebrar-e-como-n-o-escapar
  type: auto-linked
- target: heuristic-dev-quando-refatorar-produ-o-sem-testes-e2e-trocar-modulariza
  type: auto-linked
- target: sess-o-evolu-o-04-mai-2026-marco-hist-rico
  type: auto-linked
- target: dashboard-data-freshness-toda-tabela-operacional-precisa-de-updated-at
  type: auto-linked
- target: pixel-rollout-safe-fases
  type: auto-linked
- target: heur-stica-dev-instrumenta-o-leve-modulariza-o-full-sem-testes-e2e
  type: auto-linked
- target: clienteexemplo-pacote-c-consolida-o-completa-abr-2026
  type: auto-linked
- target: workflow-execution
  type: related
- target: ids-principles
  type: related
- target: coderabbit-integration
  type: related
- target: mcp-usage
  type: related
- target: story-lifecycle
  type: related
- target: dashboard-data-freshness-toda-tabela-operacional-precisa-de-updated-at
  type: related
- target: external-api-patterns
  type: related
- target: plano-correcao-framework-05-set-2026
  type: related
axis: meta
---

# Production Refactor Protocol — Instrumentação leve antes de modularização full

## Princípio

Em **produção sem cobertura E2E**, **instrumentação leve** entrega valor com risco mínimo. **Modularização full** entrega valor com risco alto. Escolha proporcional ao seu nível de cobertura de testes.

> **Regra de ouro:** "Sem testes E2E, você não está refatorando — está reescrevendo às cegas."

---

## Decisão Matrix

| Situação do código | Cobertura E2E | Decisão recomendada |
|---|---|---|
| Sistema novo/greenfield | qualquer | Modularize desde o início |
| Legado com 50%+ E2E | alta | Modularize por módulo, com testes guardando |
| Legado com 20-50% E2E | média | Modularize **só o módulo crítico**, mantenha resto |
| Legado <20% E2E ou sem CI/CD | baixa | **Instrumentação leve apenas** — modularização vira débito |
| Produção crítica em uso | qualquer | **Sempre instrumentação leve primeiro** — refactor depois |

## O que é "Instrumentação Leve"

Adicionar observabilidade ao código existente **sem mudar arquitetura**:

1. **State tracker em memória** (counters, last_success, last_error)
2. **Endpoint /api/health** rico expondo o tracker + DB stats + módulos carregados
3. **Plug nos pontos chave** existentes (success/error logs já presentes)
4. **Zero refactor** de rotas, schemas, ou estrutura

### Exemplo (validado CLIENTE_EXEMPLO)

```js
const healthState = {
  mia: { last_success: null, last_error: null, success_count: 0, error_count: 0 },
  capi: { last_success: null, last_error: null, success_count: 0, error_count: 0 },
};
function trackMiaSuccess(payload) { healthState.mia.last_success = { at: new Date().toISOString(), ...payload }; healthState.mia.success_count++; }
```

Plugue no `console.log('[Mia] OK', ...)` existente. **Zero risco** de quebrar nada.

## Quando o Refactor Vira Necessário

- Time de 3+ pessoas tocando o mesmo arquivo
- Hot path com >10 bugs nos últimos 3 meses
- Performance hit mensurável (P99 >1s)
- Onboarding de novo dev leva >1 semana só pra ler código

## Quando Refactor é Mais Risco que Recompensa

- Time solo (sem code review natural)
- Sem CI/CD com smoke tests automáticos
- Próxima entrega de cliente em <2 semanas
- Sistema funcionando estavelmente há >3 meses sem incidentes graves

## Origem

Validado em **CLIENTE_EXEMPLO Pacote C (Abr/2026)**: `server.js` de 6906 linhas. Refactor full estimado em 4-6h com risco alto de regressão sem suite de testes. Instrumentação leve resolveu observabilidade em 30min com zero regressão. Modularização foi documentada como débito técnico (nota CORTEX) para sessão dedicada.