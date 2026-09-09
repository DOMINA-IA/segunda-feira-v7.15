---
name: refactor-suggest
description: "Analisa o git diff HEAD e sugere refactorings com localização e confidence: duplicação, método longo, naming, magic numbers, nesting, tipos genéricos. Use antes de commit >50 linhas ou antes do @qa-gate. NOT for: caça a bugs de lógica — é…"
axis: meta
harnesses:
  claude-code: full
  codex: native
  cursor: full
  aider: full
model-routing:
  primary: sonnet
  simple-renames: anthropic/claude-haiku-4-5
---

# /refactor-suggest — Sugestões de Refator Diff-Aware

## Quando usar
- Antes de commitar mudança grande (>50 linhas)
- Antes do @qa-gate quando @dev terminou implementação
- Quando @architect identifica padrão repetitivo
- Em PR review (antes de @devops pushar)

## Como funciona

1. Lê `git diff HEAD` (ou diff vs branch base)
2. Detecta padrões:
   - **Duplicação** (DRY violation): mesma lógica em ≥2 lugares
   - **Long methods**: funções >40 linhas
   - **Naming pobre**: variáveis `x`, `tmp`, `data`, `result` sem contexto
   - **Magic numbers/strings**: literais que aparecem ≥2 vezes
   - **Conditional complexity**: nesting >3 níveis
   - **Type holes**: `any`, `unknown` sem narrow
   - **Dead branches**: if/else onde else nunca dispara
3. Para cada padrão, gera sugestão concreta com:
   - Localização exata (`file:line`)
   - Tipo de smell
   - Refactor recomendado (extract, inline, rename, etc)
   - Confidence (0-1)

## Execução

```bash
# Diff atual
bash ~/.claude/skills/scripts/refactor-suggest.sh

# Diff vs main
bash ~/.claude/skills/scripts/refactor-suggest.sh --base main

# Apenas em arquivos específicos
bash ~/.claude/skills/scripts/refactor-suggest.sh --files "src/auth/*"

# Output formatado para revisão
bash ~/.claude/skills/scripts/refactor-suggest.sh --format markdown
```

## Output Format

```markdown
## Refactor Suggestions — {timestamp}

### 🔴 High confidence (auto-aplicar)
1. **Duplicação** — `src/auth.ts:45` e `src/auth.ts:78`
   - Mesmo bloco de validação de email (12 linhas)
   - Sugestão: extrair `validateEmail(email: string): boolean`
   - Confidence: 0.95

### 🟡 Medium confidence (revisar)
2. **Long method** — `src/api/users.ts:120`
   - `handleCreateUser` tem 68 linhas
   - Sugestão: extrair `validateInput`, `persistUser`, `sendWelcomeEmail`
   - Confidence: 0.7

### 🟢 Low confidence (avaliar)
3. **Naming** — `src/utils.ts:23`
   - Variável `data` em escopo de função genérico
   - Sugestão: renomear para `userPayload` baseado no uso
   - Confidence: 0.5
```

## Quality Gate

- [ ] ≥1 sugestão de high confidence executada OU justificada (false positive)
- [ ] Suite de testes verde após refactors aplicados
- [ ] Diff resultante não introduz novo smell
- [ ] Commit message lista refactors aplicados

## Padrões Detectados (taxonomia)

| Smell | Sintoma | Refactor recomendado |
|-------|---------|----------------------|
| Duplicação | Mesmo bloco em 2+ lugares | Extract function |
| Long method | >40 linhas | Extract sub-functions |
| Long parameter list | >5 params | Introduce parameter object |
| God class | Classe >500 linhas | Extract class |
| Feature envy | Método usa outra classe mais que a própria | Move method |
| Magic literals | Mesmo valor 2+ vezes | Extract constant |
| Comments | Comentário explicando WHAT | Renomear variável (faça o nome falar) |
| Nested conditionals | >3 níveis | Guard clauses ou strategy pattern |

## Multi-LLM

| Sub-tarefa | Modelo |
|------------|--------|
| Parse de diff + AST análise | Python local (tree-sitter) — $0 |
| Detecção de duplicação | Algoritmo + embeddings ONNX — $0 |
| Sugestão de nome melhor | Haiku |
| Refactor estrutural complexo (extract class) | Sonnet |
| Apenas se diff >1000 linhas | Opus seletivo |

## Integração com Agent Booster (ruflo absorption)

Quando refactor é **mecânico** (var→const, add types simples, async/await), pular LLM e aplicar via tooling local:

```bash
# WASM-based AST transform (ruflo Agent Booster pattern, $0)
node ~/.claude/skills/scripts/agent-booster.mjs \
  --intent var-to-const \
  --file src/auth.ts
```

Intents disponíveis (todos $0):
- `var-to-const` / `let-to-const`
- `add-types` (simples)
- `add-error-handling` (try/catch boilerplate)
- `async-await` (promise.then → async)
- `add-logging` (console.log estruturado)
- `remove-console` (limpar debug)

## Heurísticas

- H1: Refactor sem suite de testes verde = roleta russa. Bloquear.
- H2: 3 sugestões por arquivo é teto. Mais que isso, é review, não refactor.
- H3: High confidence aplicar automaticamente em branch de refactor dedicada
- H4: Refactor que muda contrato público vira issue + spec → SDC completo

Origem: ruflo loop-worker `refactor` + Agent Booster 3-tier routing.
