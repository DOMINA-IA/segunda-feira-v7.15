---
name: orchestrate
description: Roteador multi-IA inteligente — recebe descrição de tarefa, decide o melhor LLM (Claude Opus/Sonnet, GPT-5.5 via Codex, DeepSeek V4), executa via subprocess se necessário, retorna resultado + métricas. Use ANTES de tarefas não-triviais para economizar custo e ganhar capacidade específica.
---

# Skill — Orchestrate (Multi-IA Router)

## Quando usar

Antes de delegar tarefa não-trivial. O orchestrator decide automaticamente qual LLM usar baseado em:
1. **Tipo de tarefa** — keyword matching contra tabela de routing
2. **Disponibilidade** — CLI instalado + credencial OK
3. **Budget restante** — hard-limit diário em ~/.env (`BUDGET_DAILY_USD`)

## Como invocar

```bash
# Modo simples (decisão + execução)
python3 ~/framework/orchestrator/execute.py "extrair temas de 50 PDFs"

# Modo decisão apenas (sem executar)
python3 ~/framework/orchestrator/route.py "refatorar módulo de auth"
```

## Stack atual de roteamento (22-Mai-2026)

| Tipo de tarefa (keyword regex) | LLM escolhido | Via | Custo /1K tokens |
|------|------|------|------|
| `refator│arquitetur│migração│debug profundo│trade-off│decisão crítica` | Claude **Opus 4.7** | nativo (recomenda trocar no UI) | $0.015/$0.075 |
| `review│crítica│audit│adversarial│threat model│security` | **GPT-5.5** | Codex CLI | $0 (ChatGPT Pro) |
| `extrai│extract│classific│resumi│massivo│batch│bulk│50 PDFs` | **DeepSeek V4** | Aider direto | $0.00027/$0.0011 |
| `design│UI│UX│CSS│animation│component│imagem│PDF│video` | Gemini 3.5 Flash | agy (PENDENTE) | — |
| **Default** | Claude **Sonnet 4.6** | nativo | $0.003/$0.015 |

## Output esperado

```
DECISION:
  Model: <llm>
  CLI:   <cli>
  Available: true|false
  Estimated cost: $X.XXXX
  Justification: <razão>
  [Budget alert se exceder]
  [Fallback reason se CLI indisponível]

EXECUTING:
  Latency: Xs
  Tokens used: N
  Actual cost: $X.XXXX
  Success: true|false

OUTPUT:
  <resposta do LLM>
```

## Logs e métricas

Cada execução grava em `~/framework/orchestrator/logs/orchestrator-YYYY-MM-DD.jsonl`:
- timestamp, decisão completa, prompt preview, output preview, cost, latency, tokens

Para analisar gastos:
```bash
# Custo total hoje
jq -s 'map(.cost_usd) | add' ~/framework/orchestrator/logs/orchestrator-$(date +%Y-%m-%d).jsonl

# Tarefas por LLM
jq -r '.llm_used' ~/framework/orchestrator/logs/orchestrator-*.jsonl | sort | uniq -c
```

## Integração com framework

- **Consciousness**: cada /orchestrate registra episode via `record-episode.sh` no agente apropriado (valência baseada em sucesso)
- **Cost-watchdog**: lê logs JSONL para alerta Telegram se gasto > BUDGET_DAILY_USD
- **Feedback-loop**: após N execuções, métricas viram heurística em `~/feedback-loop/cross-call-quality.json` (qual LLM funcionou melhor por tipo)

## Anti-patterns

- **NÃO usar para tarefas <2s** — overhead de subprocess + decisão > ganho
- **NÃO ignorar fallback_reason** — se CLI X não disponível, entender por que antes de seguir
- **NÃO desabilitar BUDGET_DAILY_USD** — único guard contra gastos descontrolados
- **NÃO confiar 100% no roteamento** — heurística por keyword tem 80% de acerto. Em casos críticos, override manual.

## Como funciona internamente

1. `route.py` recebe descrição → aplica regex em `ROUTING_RULES` → retorna decision dict
2. `route.py` valida CLI exists + credencial via `check_credential()`
3. `route.py` calcula `estimated_cost_usd` baseado em tokens estimados (2000 default) + tabela de preço
4. `route.py` checa budget restante via `get_daily_budget_remaining()` (lê logs JSONL hoje)
5. Se primary > budget → downgrade pra DEFAULT_LLM (Sonnet) + warning
6. `execute.py` recebe decision + prompt → roteia para `exec_codex()` ou `exec_aider_deepseek()` ou retorna instrução nativa
7. `execute.py` parseia output + custo + tokens + latência → grava em log JSONL
8. Caller (skill ou agente) recebe dict completo

## Próximas iterações (não implementadas ainda)

- **Fallback chain automática**: se primary falha (timeout, balance, error), tenta próximo da chain
- **Quality scoring**: comparar output cross-LLM em N tarefas, refinar routing automaticamente
- **Caching**: tarefas idênticas reutilizam resposta (hash do prompt)
- **Batch mode**: agrupar tarefas similares + rodar em paralelo

## Validação

Smoke test (22-Mai-2026):
- T1 "refator módulo auth" → Opus ($0.075) ✅
- T2 "review crítico segurança" → GPT-5.5 ($0) ✅
- T3 "extrair temas 50 PDFs" → DeepSeek ($0.0012) ✅
- T4 "responder pergunta" → Sonnet ($0.015) ✅

Routing-decision 100% correto. Execução real validada para Codex e DeepSeek (sessão upgrade multi-IA 22-Mai-2026).
