---
name: cross-call
description: Delega uma tarefa para outro LLM (Codex/GPT-5, Aider/Sonnet via OpenRouter, ou Gemini via API). Use quando uma tarefa específica é melhor servida por outro modelo (custo, capacidade, velocidade). Funciona como subprocess shell — Claude Code chama o CLI externo, espera resposta, traz resultado de volta.
---

# Skill — Cross-Call (Multi-LLM delegation)

## Quando usar

Antes de delegar tarefa não-trivial, use `/route-llm` para decidir qual LLM. Depois use esta skill para EXECUTAR a delegação.

Casos típicos:
- Code review profundo → delegar para GPT-5 via Codex CLI
- Refator longo de arquivo único → delegar para Aider (mais focado em arquivos individuais)
- Análise de muitos PDFs/imagens → marcar como pendente (Antigravity CLI ainda não disponível publicamente)
- Tarefa massiva barata → Aider via OpenRouter (DeepSeek)

## CLIs disponíveis localmente (após Fase B do upgrade multi-IA — 22-Mai-2026)

| CLI | Comando | Versão | LLMs |
|-----|---------|--------|------|
| **Codex** | `~/.npm-global/bin/codex` | 0.133.0 | **gpt-5.5** (atual default), gpt-5, gpt-4o (OpenAI) — auth via ChatGPT account ✅ funcional |
| **Aider** | `~/.local/bin/aider` | 0.86.2 | **APENAS DeepSeek** via OpenRouter (Sonnet roda nativo no Claude Code, não rotear via proxy) |
| **Antigravity** | `agy` | NÃO INSTALADO | Pendente — Google ainda não publicou no npm público |

## Como invocar

### Codex CLI (OpenAI / GPT-5.5)

**Auth status (22-Mai-2026):** ✅ JÁ autenticado via ChatGPT account (verificar com `codex login status`).
Não precisa configurar `OPENAI_API_KEY` no `.env`.

```bash
# Verificar login
~/.npm-global/bin/codex login status
# Output esperado: "Logged in using ChatGPT"

# Tarefa não-interativa (stdin → stdout) ← MODO VALIDADO 22-Mai
echo "review esta função: $(cat file.py)" | ~/.npm-global/bin/codex exec --skip-git-repo-check

# Tarefa em projeto (modo interativo)
cd /path/to/project
~/.npm-global/bin/codex "Corrija o bug em src/auth.py e gere testes"

# Diagnose
~/.npm-global/bin/codex doctor
```

**Output format do `exec`:** o stdout vem com cabeçalho (`OpenAI Codex v0.133.0`, workdir, model, session_id) + bloco `user` + bloco `codex` (resposta) + linha `tokens used`. Para parsear apenas a resposta:
```bash
... | sed -n '/^codex$/,/^tokens used$/p' | sed '1d;$d'
```

### Aider (DeepSeek API DIRETA — sem proxy OpenRouter)

**Decisão CEO 22-Mai-2026:**
- Aider é usado **APENAS para DeepSeek** (modelo barato que Claude Code não acessa nativamente)
- DeepSeek via **API direta** (`DEEPSEEK_API_KEY`), NÃO via OpenRouter proxy
- NÃO usar Aider/OpenRouter para Sonnet/Opus — já temos via Claude Code nativo
- OpenRouter como fallback se DeepSeek direto cair (mas requer créditos)

**Vantagem do API direto:** sem proxy fee do OpenRouter (DeepSeek cobra $0.27/M input direto, OpenRouter cobra spread por cima).

**Modelos DeepSeek disponíveis (preços via OpenRouter, USD/M tokens):**

| Model ID | Input | Output | Context |
|----------|-------|--------|---------|
| `deepseek/deepseek-v4-pro` | $0.435 | $0.87 | 1M |
| `deepseek/deepseek-v4-flash` | $0.112 | $0.224 | 1M |
| `deepseek/deepseek-chat` | $0.32 | $0.89 | 164K |
| `deepseek/deepseek-r1` (reasoning) | $0.70 | $2.50 | 164K |
| `deepseek/deepseek-r1-0528` | $0.50 | $2.15 | 164K |

**Use caso típico:**
- Tarefas massivas baratas (extração, classificação, resumo de 100+ arquivos)
- Cabe em contexto Claude Code, mas custaria $X em Opus → DeepSeek faz por $X/100

```bash
# Aider com DeepSeek DIRETO (preferência — sem proxy)
# Precisa DEEPSEEK_API_KEY em ~/.env (key em platform.deepseek.com/api_keys)
export $(grep "^DEEPSEEK_API_KEY=" ~/.env | xargs)
~/.local/bin/aider --model deepseek/deepseek-chat \
  --no-auto-commits --no-git --yes \
  --message "Extraia keywords desses 50 arquivos" \
  *.md

# Para tarefa de reasoning (math, code-review profundo):
~/.local/bin/aider --model deepseek/deepseek-reasoner ...

# Não-interativo (stdin → stdout)
echo "Classifique cada linha deste log..." | ~/.local/bin/aider --model deepseek/deepseek-chat --no-stream

# Fallback OpenRouter (apenas se DEEPSEEK_API_KEY falhar):
~/.local/bin/aider --model openrouter/deepseek/deepseek-v4-flash ...
```

**Models DeepSeek direto disponíveis** (preços oficiais platform.deepseek.com, USD/M tokens, padrão off-peak 16:30-00:30 BJT tem 50-75% desconto):

| Model ID | Input | Output | Context | Caso de uso |
|----------|-------|--------|---------|-------------|
| `deepseek/deepseek-chat` | $0.27 | $1.10 | 64K | Tarefas massivas baratas |
| `deepseek/deepseek-reasoner` | $0.55 | $2.19 | 64K | Math, code review profundo |
| `deepseek/deepseek-coder` | $0.27 | $1.10 | 64K | Coding focado |

**Status créditos (22-Mai-2026):**
- ✅ DeepSeek API direto: depende de `DEEPSEEK_API_KEY` (free trial ~$5 inicial)
- ⚠️ OpenRouter free tier: providers downstream (Crucible) exigem crédito mesmo nos `:free`. Mínimo $5 em openrouter.ai/settings/credits

### Antigravity CLI (`agy`) — PENDENTE

Lançado Google I/O 20-Mai-2026, mas pacote npm público ainda não disponível em 22-Mai. Quando publicado, comando esperado:
```bash
agy --model gemini-3.5-flash "tarefa"
```
Alternativa imediata: usar Gemini via Google AI Studio API direto (Python SDK `google-generativeai`).

## Setup de credenciais

Conforme rule `credentials-handling.md`: **NUNCA commitar key em arquivo do projeto**.

Variáveis esperadas (configurar em `~/.env` com chmod 600 OU 1Password):

```bash
# OpenAI (Codex)
OPENAI_API_KEY=sk-...

# OpenRouter (Aider multi-provider)
OPENROUTER_API_KEY=sk-or-...

# Anthropic (opcional, se quiser Aider chamando Claude direto)
ANTHROPIC_API_KEY=sk-ant-...

# Google AI (para Gemini quando agy disponível)
GOOGLE_AI_API_KEY=...
```

## Fluxo recomendado de delegação

1. **Decidir modelo**: chame `/route-llm` com descrição da tarefa
2. **Verificar credencial**: `grep OPENROUTER_API_KEY ~/.env` (ou variant)
3. **Executar via subprocess**:
   ```bash
   # Exemplo: delegar audit pra GPT-5
   echo "audit security de src/auth.ts" | ~/.npm-global/bin/codex exec --skip-git-repo-check
   ```
4. **Capturar output**: gravar em `/tmp/cross-call-YYYYMMDD-HHMM.md` para inspeção
5. **Avaliar qualidade**: se resultado é pior que esperado, fallback (próximo na chain)
6. **Registrar episódio Consciousness**: `@dev` ou agente apropriado, com valência baseada em utilidade

## Modelos de prompt cross-LLM

Cada modelo responde diferente. Templates:

### Para GPT-5 (Codex)
- Mais formal, espera output estruturado
- Bom em chains-of-thought longos
- Prefere ver código completo em vez de snippets
- Exemplo: "Avalie esta função e sugira melhorias seguindo SOLID."

### Para Sonnet via Aider
- Pode tratar como instrução de edição direta
- Aider já aplica os diffs automaticamente (não precisa pedir "gere o patch")
- Exemplo: "Refator este arquivo para usar async/await em vez de promises encadeadas."

### Para DeepSeek (via OpenRouter)
- Excelente em compreensão técnica, fraco em raciocínio criativo
- Bom para tarefas repetitivas (extração, classificação, resumo)
- Exemplo: "Para cada linha deste log, extraia: timestamp, level, message."

## Validação após delegação

Sempre validar output de outro LLM:
- Código gerado roda? (`npm test`, `pytest`, etc)
- Output corresponde ao formato esperado?
- Tem alucinação visível (referência a arquivo inexistente, função imaginária)?

Se OK: registrar episódio success. Se não OK: registrar episódio failure + heurística sobre qual tipo de tarefa esse LLM não serve.

## Cost-watchdog integration

O framework já tem `cost-watchdog` (cron + alertas Telegram). Quando usar cross-call:
- Logar custo em `~/feedback-loop/cross-call-costs.json`
- Pulse diário compara: quanto economizou vs delegação direta no Claude Code
- Heurística futura: se gasto > $X com modelo Y mas qualidade não justifica → desativar para tipo de tarefa Z

## Anti-patterns

- **NÃO** usar cross-call para tarefas pequenas (<2s no Claude Code) — overhead de subprocess maior que ganho
- **NÃO** usar cross-call sem validar credencial primeiro — erros silenciosos custam tempo
- **NÃO** delegar tarefa multi-step que requer tool calls coordenados — outros CLIs são mais limitados
- **NÃO** confiar 100% no output sem validação — cada LLM tem padrões de alucinação diferentes

## Roadmap (não implementado ainda)

- C: routing automático via `/orchestrate` (decide LLM sem perguntar)
- C: fallback chain automática (se primary falha, segue para next)
- C: métricas de custo/qualidade por LLM em dashboard
- D: skills multi-harness (mesmo skill roda em todos LLMs)
