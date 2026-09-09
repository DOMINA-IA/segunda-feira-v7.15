---
id: dashboard-data-freshness-toda-tabela-operacional-precisa-de-updated-at
title: Dashboard Data Freshness — Toda tabela operacional precisa de updated_at
type: rule
status: active
created: '2026-04-30'
last_verified: '2026-04-30'
domain:
- dev
- meta
- architect
agents:
- architect
- data-engineer
- dev
- qa
tags:
- rule
- schema
- observability
- dashboard
- data-freshness
- production
decay_rate: 0.01
links:
- target: heuristic-dev-quando-comparar-tempo-em-sqlite-via-pdo-com-uma-expressao-a
  type: auto-linked
- target: heuristic-dev-toda-migracao-idempotente-protegida-por-try-catch-precisa-de
  type: auto-linked
- target: production-refactor-protocol-instrumenta-o-leve-antes-de-modulariza-o-full
  type: auto-linked
- target: heur-stica-dev-schema-sem-updated-at-esconde-estagna-o-operacional
  type: auto-linked
- target: heur-stica-architect-toda-tabela-operacional-precisa-de-updated-at
  type: auto-linked
- target: external-api-patterns
  type: related
- target: workflow-execution
  type: related
- target: coderabbit-integration
  type: related
- target: production-refactor-protocol-instrumenta-o-leve-antes-de-modulariza-o-full
  type: related
- target: ids-principles
  type: related
- target: story-lifecycle
  type: related
axis: meta
triggers:
- dashboard
- tabela
- updated_at
- freshness
- migration
- schema
- banco de dados
- sync
- coluna
---

# Dashboard Data Freshness — Toda tabela operacional precisa de updated_at

## Princípio

Toda tabela que registra **estado mutável** (tasks, leads, contatos, campanhas, ofertas, conteúdo agendado) precisa de coluna que rastreia última mudança — **`updated_at`** — sob pena de **estagnação operacional invisível**.

> **Regra de ouro:** "Se a operação parou e ninguém percebeu, é problema de schema, não de UI."

---

## Quando aplicar (MUST)

Toda nova tabela criada por @architect, @data-engineer ou @dev que tenha:
- **Estado mutável** (status, stage, fase, etc.)
- **Lifecycle longo** (registros vivem semanas/meses)
- **Múltiplos editores** (humanos ou automações)

## Pattern obrigatório

### SQLite
```sql
CREATE TABLE X (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ...
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
```

**Migration idempotente em produção** (quando descobrir tabela legada sem updated_at):
```sql
ALTER TABLE X ADD COLUMN updated_at TEXT;  -- em try/catch
UPDATE X SET updated_at = COALESCE(completed_at, created_at) WHERE updated_at IS NULL;
```

**Atualizar manualmente em cada PATCH** (trigger AFTER UPDATE pode causar loop):
```js
updates.push("updated_at = datetime('now')");
```

### PostgreSQL/MySQL

```sql
CREATE TRIGGER X_updated_at BEFORE UPDATE ON X
FOR EACH ROW EXECUTE FUNCTION moddatetime(updated_at);
```

## Como detectar violação

Em qualquer dashboard, se ao perguntar "qual o status atual?" você precisa **assumir** ao invés de **consultar**, faltou `updated_at`.

```sql
-- Auditoria: tabelas operacionais sem updated_at
SELECT name FROM sqlite_master WHERE type='table'
AND sql NOT LIKE '%updated_at%';
```

## Anti-patterns

| Evitar | Por quê |
|--------|---------|
| `completed_at` substitui `updated_at` | Só rastreia conclusão, não pausas/reaberturas |
| Trigger AFTER UPDATE sem WHEN | Loop infinito (UPDATE dispara trigger que faz UPDATE...) |
| Atualizar updated_at via cron periódico | Stale data; cron pode falhar; mascara realidade |

## Origem

Validado em **CLIENTE_EXEMPLO Pacote C (Abr/2026)**: 47 tasks paradas há 30 dias pareciam normais porque `tasks.updated_at` não existia. Após migration + UI badge "⏱ Xd parada", problema operacional ficou impossível de ignorar.