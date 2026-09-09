# Architect API Integration Checklist

> **Version:** 1.0.0
> **Agent:** @architect (Aria)
> **Trigger:** Story envolve integração com API externa (ASAAS, Eduzz, Greenn, Meta, etc.)
> **Reference:** `rules/external-api-patterns.md`

## Pre-Implementation Gate (BLOCKING)

### 1. Data Access Pattern
```yaml
check: data_access_pattern
severity: blocking
question: "A UI vai ler dados diretamente de uma API externa?"
pass: "Não — dados vêm do DB local (sync prévio)"
fail: "Sim — redesenhar para SYNC → DB → UI"
```

### 2. Schema Completeness
```yaml
check: schema_completeness
severity: blocking
question: "Todos os campos que a UI precisa existem no schema local?"
pass: "Sim — schema tem todos os campos com tipos corretos"
fail: "Não — adicionar campos faltantes ao Prisma schema antes de implementar"
action: "Listar campos da API que a UI consome → garantir 1:1 no schema"
```

### 3. Sync Exists
```yaml
check: sync_mechanism
severity: blocking
question: "Existe um sync que popula esses campos no DB?"
pass: "Sim — sync roda periodicamente e salva todos os campos necessários"
fail: "Não — implementar sync ANTES de implementar a UI"
```

### 4. Rate Limit Global
```yaml
check: rate_limit_shared
severity: blocking
question: "Se múltiplos endpoints usam a mesma API, o rate limit é compartilhado?"
pass: "Sim — módulo global (ex: asaas-rate-limit.ts) usado por todos"
fail: "Não — criar módulo compartilhado de rate limit"
```

## Design Review (WARNING)

### 5. Cache Strategy
```yaml
check: cache_location
severity: warning
question: "O cache está em memória (Map/Object) ou no DB?"
prefer: "DB — sobrevive a restarts"
accept: "Memória apenas como camada extra sobre DB, não como source of truth"
reject: "Memória como única fonte de dados"
```

### 6. Sync Window
```yaml
check: sync_window
severity: warning
question: "O sync cobre dados antigos que podem mudar de status?"
pass: "Sim — janela de 90+ dias para cobrir mudanças de status tardias"
fail: "Não — ampliar janela ou adicionar full sync periódico"
```

### 7. Error Isolation
```yaml
check: error_isolation
severity: warning
question: "Se a API externa falhar, a UI continua funcionando?"
pass: "Sim — UI lê do DB local, sync falha silenciosamente"
fail: "Não — UI mostra erro quando API falha"
```

## Post-Implementation Verification (INFO)

### 8. Zero Real-Time Calls
```yaml
check: no_realtime_reads
severity: info
question: "Os route handlers GET fazem ZERO chamadas a APIs externas?"
verify: "grep -r 'axios.get\\|fetch(' nos route handlers de leitura"
```

### 9. Sync Monitoring
```yaml
check: sync_monitoring
severity: info
question: "Existe SyncLog ou similar para monitorar sucesso/falha do sync?"
verify: "Tabela SyncLog com registros recentes, sem erros consecutivos"
```

### 10. Backfill Done
```yaml
check: backfill_complete
severity: info
question: "Dados históricos foram sincronizados (backfill)?"
verify: "Contagem de registros no DB vs total na API externa"
```

---

## Workflow Integration

Este checklist é executado pelo @architect (Aria) durante:
- **Story Development Cycle — Phase 2 (Validate):** Se story envolve API externa
- **Spec Pipeline — Phase 2 (Assess):** Na avaliação de complexidade
- **Brownfield Discovery — Phase 1:** Na análise de arquitetura existente

## Scoring

| Score | Meaning | Action |
|-------|---------|--------|
| 10/10 | Todos passam | Aprovar implementação |
| 7-9/10 | Warnings pendentes | Aprovar com observações |
| <7/10 | Blocking checks falhando | BLOQUEAR — redesenhar antes |
