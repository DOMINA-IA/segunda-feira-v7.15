---
name: trajectory-eval
description: "Avalia a trajetória de execução de uma story SDC — compara a sequência real de tool calls do @dev com a trajetória esperada definida no AC (score 0-1, detecta steps faltando ou extras). Use após @dev completar a implementação e antes do @qa-gate, em stories com AC complexo, ou para auditoria retroativa quando suspeitar que uma etapa foi pulada."
axis: meta
harnesses:
  claude-code: full
  codex: limited
  cursor: limited
  aider: limited
model-routing:
  parse: local  # leitura determinística do JSONL
  score: google/gemini-2.5-flash  # via agy, score contextual
  fallback: anthropic/claude-haiku-4-5  # se agy indisponível
provider-fallback:
  - google/gemini-2.5-flash
  - anthropic/claude-haiku-4-5
tags: [trajectory, evals, tester, qa, sdc, mastra]
related:
  - testgaps
  - tester (agent)
  - mastra-evals-sistema-avaliacao-agentes
---

# /trajectory-eval — Avaliação de Trajetória de Execução

Inspirado no Trajectory Scorer do Mastra Evals. Compara a sequência real de tool calls usadas pelo `@dev` durante uma story contra a trajetória esperada definida no AC ou no bloco `## Trajectory Expectation` da story.

## Quando usar

- Após `@dev` completar implementação, antes de `@qa-gate`
- Em histórias SDC com AC complexo (múltiplos steps obrigatórios)
- Quando suspeitar que `@dev` pulou etapas (lint, typecheck, testes)
- Auditoria retroativa de stories recentes

## Pré-requisitos

O hook `trajectory-logger.py` deve estar ativo (PostToolUse). Verifica:
```bash
ls ~/.claude/.session-state/*-trajectory.jsonl 2>/dev/null | tail -3
```

## Formato esperado na Story

Adicionar seção ao arquivo da story (opcional — se ausente, usa trajetória padrão SDC):

```yaml
## Trajectory Expectation
expected_tools:
  - tool: Read
    description: "Ler story e arquivos relacionados"
    required: false
  - tool: Edit
    description: "Implementar os AC"
    required: true
  - tool: Bash
    description: "Rodar lint e typecheck"
    required: true
    cmd_contains: "lint|typecheck|tsc|eslint"
  - tool: Bash
    description: "Rodar testes"
    required: true
    cmd_contains: "test|pytest|jest|vitest"
  - tool: Write
    description: "Atualizar checkboxes na story"
    required: true
order: loose  # loose = presença importa; strict = ordem exata
```

Se `## Trajectory Expectation` ausente, usa trajetória padrão SDC:
```
required: Edit (implementação) + Bash com lint + Bash com test
```

## Como executar

```bash
# Usar sessão atual
/trajectory-eval

# Especificar story
/trajectory-eval --story docs/stories/story-2-1.md

# Especificar session_id (retroativo)
/trajectory-eval --session {session_id}

# Usar trajetória padrão SDC (sem ler story)
/trajectory-eval --default-sdc
```

## Pipeline interno

### Step 1 — Localizar log de trajetória

```bash
SESSION_ID=${CLAUDE_SESSION_ID:-default}
TRAJ_LOG=~/.claude/.session-state/${SESSION_ID}-trajectory.jsonl

# Listar últimas 5 sessões com log
ls -t ~/.claude/.session-state/*-trajectory.jsonl 2>/dev/null | head -5
```

### Step 2 — Parsear trajetória real

```python
import json

with open(traj_log) as f:
    actual = [json.loads(line) for line in f if line.strip()]

# Resumo: lista de tools em ordem de execução
tool_sequence = [(e["seq"], e["tool"], e.get("cmd",""), e.get("file","")) for e in actual]
```

### Step 3 — Parsear trajetória esperada

Lê o bloco `## Trajectory Expectation` da story file, ou usa padrão SDC:

```python
# Padrão SDC (fallback)
DEFAULT_SDC_TRAJECTORY = [
    {"tool": "Edit",  "required": True,  "description": "Implementação"},
    {"tool": "Bash",  "required": True,  "cmd_contains": "lint|typecheck|tsc|eslint",
     "description": "Lint/typecheck"},
    {"tool": "Bash",  "required": True,  "cmd_contains": "test|pytest|jest|vitest",
     "description": "Testes"},
]
```

### Step 4 — Score determinístico (code scorer)

```python
def score_trajectory(expected, actual_tools):
    required = [e for e in expected if e.get("required")]
    hits = 0
    missing = []
    extra = []

    for exp in required:
        found = any(
            a["tool"] == exp["tool"] and
            (not exp.get("cmd_contains") or
             any(p in a.get("cmd","") for p in exp["cmd_contains"].split("|")))
            for a in actual_tools
        )
        if found:
            hits += 1
        else:
            missing.append(exp["description"])

    score = hits / len(required) if required else 1.0
    return score, missing
```

### Step 5 — Score contextual (agy, opcional)

Para histórias sem `## Trajectory Expectation`, usa `agy` para avaliar se a sequência real faz sentido para a feature implementada:

```bash
export GEMINI_API_KEY=$(grep "^GEMINI_API_KEY=" ~/.env | cut -d= -f2-)
GEMINI_CLI_TRUST_WORKSPACE=true agy --skip-trust \
  -p "Avalie se esta trajetória de tool calls faz sentido para implementar [feature X]: [tool_sequence]" \
  --model gemini-2.5-flash
```

## Output

```
TRAJECTORY EVAL — Story {id}
─────────────────────────────────────────
Session:  {session_id}
Tools:    {N} calls registradas
─────────────────────────────────────────
✅ Edit         — implementação presente
✅ Bash(lint)   — lint/typecheck rodado
❌ Bash(test)   — NENHUM teste rodado!
─────────────────────────────────────────
Score: 0.67 | CONDICIONAL

Missing steps:
  - Bash com test/pytest/jest (required)

Extra steps detectados:
  - Nenhum

Recomendação: @dev deve rodar suite de testes antes do @qa-gate.
```

## Integração no SDC

```
@dev completa story
  → trajectory-logger registrou {N} tool calls durante a sessão
  → @tester roda /trajectory-eval
  → Score ≥ 0.8: prosseguir para @qa-gate
  → Score 0.5-0.8: CONDICIONAL (documentar missing steps)
  → Score < 0.5: BLOQUEADO (retornar ao @dev)
```

## Thresholds de decisão

| Score | Decisão | Ação |
|-------|---------|------|
| ≥ 0.9 | APROVADO | Prosseguir para @qa-gate |
| 0.7-0.9 | CONDICIONAL | Documentar + prosseguir com ressalva |
| 0.5-0.7 | ALERTA | Notificar @dev via mailbox |
| < 0.5 | BLOQUEADO | Retornar ao @dev, listar missing steps |

## Anti-patterns

| Evitar | Por quê |
|--------|---------|
| Trajectória esperada muito rígida (strict mode para tudo) | @dev tem autonomia de método; punir ordem exata é over-engineering |
| Não definir `cmd_contains` para Bash | "rodou Bash" não garante que foi lint — pode ser qualquer comando |
| Ignorar score < 0.5 | Story sem lint/test não deve ir para @qa-gate |
| Usar trajectory-eval em tasks triviais | Só faz sentido em stories SDC com AC de implementação |
