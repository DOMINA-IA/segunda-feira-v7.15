---
name: testgaps
description: "Detecta gaps de cobertura: funções sem teste, critérios de aceite sem teste correspondente, edge cases descobertos. Use antes do @qa-gate, na auditoria mensal, ou quando falha em produção indicar caminho sem teste. Trabalha com @tester. NOT for:…"
axis: meta
harnesses:
  claude-code: full
  codex: native
  cursor: limited
  aider: full
model-routing:
  parse: anthropic/claude-haiku-4-5
  analysis: anthropic/claude-sonnet-4-6
---

# /testgaps — Detecção de Gaps de Teste

## Quando usar
- Antes de @qa-gate
- Mensalmente para auditoria
- Após onboarding (`/cortex-ultralearn` revelou cliente sem testes)
- Quando feature failure indica falta de teste no path

## Como funciona

### 1. Coverage map
```bash
# Node
npm test -- --coverage --json > /tmp/coverage.json

# Python
pytest --cov=. --cov-report=json:/tmp/coverage.json
```

### 2. Identifica funções sem teste
- Coverage <50% por arquivo → flag
- Coverage 0% em arquivo de produção → CRITICAL

### 3. Cross-check com AC
Para cada story em `docs/stories/`:
- Lê AC
- Procura teste com nome/descrição correspondente
- Sinaliza AC sem teste

### 4. Edge case detection
Analisa código de produção para detectar:
- Try/catch sem teste de exception path
- If/else onde else nunca foi testado
- Switch sem default coverage
- Loops com break/continue sem teste

## Output

```markdown
# Test Gap Report — {project} — {date}

## Coverage Resumo
- Total: 72% (lines), 65% (branches)
- Threshold: ≥80%
- Status: ❌ ABAIXO

## Top 10 Gaps Críticos

### 🔴 Zero coverage
1. `src/api/payments.ts` — 0% — produção crítica!
2. `src/auth/sessionRefresh.ts` — 0%

### 🟠 Cobertura parcial
3. `src/api/users.ts` — 45% — falta: error handling paths
4. `src/utils/email.ts` — 60% — falta: edge case de email vazio

## AC sem Teste
- STORY-042 AC #3 "Sistema deve aceitar email com +" — sem teste
- STORY-067 AC #1 "Limite de 5 tentativas" — sem teste

## Edge Cases Detectados

```typescript
// src/auth.ts:45 — catch nunca testado
try {
  await authenticate(creds);
} catch (e) {  // ← este path está sem teste
  logger.error(e);
  throw new AuthError();
}
```

## Sugestões Acionáveis
1. Pedir @tester gerar testes para `payments.ts` (P0)
2. Adicionar 4 testes para AC sem cobertura (P1)
3. Criar issue para edge cases em batch (P2)
```

## Quality Gate

- [ ] Cobertura por arquivo medida
- [ ] AC vs tests cross-check completo
- [ ] ≥3 sugestões concretas com prioridade
- [ ] Linha exata de cada gap reportada
- [ ] Sumário executivo claro

## Integração com @tester

Ao completar, envia mailbox para @tester:
```json
{
  "from": "/testgaps",
  "to": "@tester",
  "type": "request",
  "subject": "Test gaps detectados — payments.ts (0% coverage)",
  "priority": "high",
  "data": {
    "files_zero_coverage": ["src/api/payments.ts"],
    "ac_without_test": ["STORY-042/AC-3", "STORY-067/AC-1"],
    "edge_cases": [{"file": "src/auth.ts", "line": 45, "kind": "uncaught_exception_path"}]
  }
}
```

## Multi-LLM Economia

| Sub-tarefa | Modelo |
|------------|--------|
| Coverage parsing | Python/Node — $0 |
| AST analysis para edge cases | tree-sitter local — $0 |
| Cross-check AC ↔ tests (semantic) | Embeddings ONNX 384d — $0 |
| Sugestão de teste novo | Haiku |
| Análise de coverage report grande | Sonnet apenas se necessário |

## Heurísticas

- H1: Arquivo de produção com 0% coverage é P0 sempre
- H2: AC sem teste = bug factory. Bloquear @qa-gate
- H3: Edge case detectado em path crítico (auth, payment) → P0
- H4: Coverage <80% por 3 sprints seguidos = sinal de débito técnico crescente

Origem: ruflo worker `testgaps` + nossa rule EROS (Portão 4).
