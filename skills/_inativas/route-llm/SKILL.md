---
name: route-llm
description: Sugere qual LLM (Claude, GPT, Gemini, DeepSeek) é ideal para a tarefa descrita, com fallback chain e justificativa de custo/qualidade. Use ANTES de delegar tarefa grande para economizar tokens ou ganhar capacidade específica.
---

## ⚠️ Regra obrigatória — Anti-pattern OpenRouter para Anthropic

**NUNCA rotear Sonnet ou Opus via OpenRouter.** Esses modelos já estão acessíveis nativamente via Claude Code (este harness) — usar OpenRouter adiciona proxy fee, latência extra e zero benefício.

**OpenRouter é usado APENAS para:**
- ✅ DeepSeek (V4 Pro, V4 Flash, Chat, R1) — único modelo de alto valor sem acesso nativo no Claude Code
- ❌ Sonnet/Opus/Haiku Anthropic — usar Claude Code direto (nativo, sem proxy)
- ⚠️ GPT-5/5.5/4o — preferir `codex` CLI (ChatGPT auth pago já cobre)
- ⚠️ Gemini — aguardar `agy` Antigravity CLI; alternativa Python SDK direto

# Skill — Route LLM

## Quando usar

Antes de delegar tarefa não-trivial via `/cross-call` ou Bash subprocess. A skill recebe descrição da tarefa e sugere o **LLM ideal** + **fallback chain** + **justificativa**.

Casos típicos:
- "Preciso analisar 50 PDFs e extrair temas" → Gemini (multimodal + 1M context + barato)
- "Refator complexo no codebase CLIENTE_EXEMPLO" → Claude Opus (qualidade + ambiente Claude Code)
- "Auditoria de segurança no endpoint X" → GPT-5 via Codex (raciocínio adversarial)
- "Resumir 100 arquivos de log" → DeepSeek V4 via OpenRouter (massivo barato)

## Como funciona

Aplico estes critérios em ordem:

### 1. Tipo de tarefa

| Tipo | LLM primário | Justificativa |
|------|--------------|---------------|
| Coding sério (refator, arquitetura, multi-file) | claude-opus-4-7 | Premium para dev complexo |
| Coding standard (feature, bug fix) | claude-sonnet-4-6 (Claude Code nativo) | Balanced cost/quality — SEM proxy OpenRouter |
| Review/auditoria crítica | gpt-5 via codex | Raciocínio adversarial forte |
| Análise multimodal (PDFs, imagens, vídeo) | gemini-3.5-flash via agy | Multimodal nativo + barato |
| Geração de UI/design (CSS, componentes) | gemini-3.5-flash via agy | Especialidade design |
| Extração/resumo massivo | deepseek-v4-flash via openrouter | $0.112/M input — 100x mais barato que Opus |
| Conversação rápida/curta | claude-sonnet-4-6 (Claude Code nativo) | Latência baixa, sem proxy |
| Pesquisa profunda multi-fonte | gemini-3.5-flash (1M context) | Cabem 1000+ docs no contexto |

### 2. Restrições orçamentárias

Se cost-watchdog do framework reportou gasto > R$X esta semana:
- Tarefas standard → migra para Sonnet ou DeepSeek
- Tarefas críticas → mantém Opus mas registra

### 3. Disponibilidade do harness

- Se Claude Code rodando: pode delegar via Bash subprocess (`codex`, `agy`, `aider`)
- Se outro harness rodando: usa CLI do harness primário + fallback
- Se nenhuma CLI alternativa instalada: notifica + sugere instalação

### 4. Capacidades específicas

| Capacidade necessária | LLM ideal |
|----------------------|-----------|
| Tool use complexo + thinking | claude-opus-4-7 |
| Web search nativo | gemini-3.5-flash (Grounding nativo) |
| Code execution (sandboxed) | gpt-5 via codex (sandbox built-in) |
| Image generation | gemini-omni + Whisk |
| Voice synthesis | gemini-tts ou elevenlabs (skill separada) |

## Output esperado

```
🎯 LLM RECOMENDADO

Tarefa: [descrição curta]
Primário: <model> via <cli>
Justificativa: <razão técnica>
Custo estimado: ~$X.XX
Fallback chain: [<model_2>, <model_3>]

Como invocar:
<comando bash exato OU instrução cross-call>

Riscos:
- <risco específico ao LLM>
```

## Anti-patterns

- **NÃO** rotear para Opus tarefas triviais (resumir 1 arquivo, classificar) — desperdício
- **NÃO** rotear para DeepSeek tarefas críticas (review de segurança, refator complexo) — qualidade insuficiente
- **NÃO** rotear para Gemini tarefas com tool calls múltiplos sequenciais — context window é grande mas tool-orchestration ainda é melhor no Claude
- **NÃO** ignorar fallback chain — se primário falhar (rate limit, error), próximo da chain deve estar pronto

## Integração

- Lê `~/cortex/vault/news/inema-delta-2026-05-22-orchestrator-multi-ia.md` para preço/benchmark atualizado
- Lê `~/feedback-loop/results.json` para histórico de qual LLM funcionou melhor por tipo
- Consciousness Engine registra rotina decision_made após delegar (valência baseada em sucesso)
- Cost-watchdog alimenta limite orçamentário

## Logs e métricas (absorvido de orchestrate.md)

Se a decisão de roteamento for executada via `$HOME/framework/orchestrator/` (`route.py` + `execute.py`), cada execução grava em `$HOME/framework/orchestrator/logs/orchestrator-YYYY-MM-DD.jsonl`:
- timestamp, decisão completa, prompt preview, output preview, cost, latency, tokens

Para analisar gastos:
```bash
# Custo total hoje
jq -s 'map(.cost_usd) | add' $HOME/framework/orchestrator/logs/orchestrator-$(date +%Y-%m-%d).jsonl

# Tarefas por LLM
jq -r '.llm_used' $HOME/framework/orchestrator/logs/orchestrator-*.jsonl | sort | uniq -c
```

## Próximos passos (não implementado ainda)

- Skill `/cross-call` que executa a delegação proposta aqui
- Heurística automática: após N tarefas roteadas, refina critérios via consciousness
- Integração com `cost-watchdog` para limite hard em $X/dia
