---
id: model-routing-multi-llm-full
title: Multi-LLM Model Routing (completo)
type: rule
domain:
- meta
triggers:
- model routing
- provider
- litellm
- overlay
- dual-mode
- gemini
- deepseek
- ollama
- z.ai
- glm
- tier 0
- tier 4
- multi-provider
- bs-benchmark
- qwen
links:
- target: token-economy
  type: auto-linked
- target: .archived-model-routing
  type: auto-linked
- target: model-routing
  type: auto-linked
- target: multi-ia-portability
  type: auto-linked
---

# Multi-LLM Model Routing — Economia Estratégica de Tokens

> **Severidade:** SHOULD | **Aplica-se a:** Todos os agentes, todas as skills
> **Origem:** Absorção ruflo 3-Tier Routing (24-Mai-2026) + INEMA TRIAD multi-modelo + diretriz CEO "baratear custos de tokens"

## Princípio

Token mais caro que precisa = orçamento queimado. Token barato que basta = inteligência preservada. O framework deve **descer de tier** sempre que possível e **subir de tier** apenas quando justificado.

**Regra de ouro:** "O modelo que basta. Não o mais caro disponível."

---

## 4-Tier Routing (estendido de 3 do ruflo)

### Tier 0 — Local/WASM ($0)
**Quando usar:** transformação determinística, parsing, embeddings, search local

| Operação | Tecnologia |
|----------|-----------|
| Refactor mecânico (var→const, add types simples, async/await) | Agent Booster WASM (ruflo) ou tree-sitter |
| Embedding semântico (384d) | ONNX `all-MiniLM-L6-v2` local |
| Search no CORTEX | Python+índice local |
| Coverage parsing | Jest/pytest JSON |
| AST analysis | tree-sitter Node/Python |
| Sintetizar dados (mocks, factories) | faker, jsf |

**Latência:** <1ms — **Custo:** $0

### Tier 1 — Haiku 4.5 (~$0.0002/call)
**Quando usar:** classificação, extração, boilerplate, transformação simples

| Operação | Justificativa |
|----------|---------------|
| Classificar severidade de log | classificação binária/multi-class |
| Extrair campos de texto livre para JSON | extração estruturada |
| Renomeação de variável (sugestão única) | mecânico |
| Test boilerplate (describe/beforeEach) | template-driven |
| Geração de fakes/factories de teste | template-driven |
| Resumo de 1 linha de mensagem longa | redução |
| Aquecimento de cache (NoOp warm calls) | irrelevante o output |

**Latência:** ~500ms — **Custo:** $0.0002

### Tier 2 — Sonnet 4.6 (~$0.003/call)
**Quando usar:** execução padrão da maioria dos agentes

| Operação | Justificativa |
|----------|---------------|
| Implementar feature (story comum) | balanço custo/qualidade |
| Análise de dados | raciocínio padrão |
| Code review | precisão linguística |
| Spec generation (@spec-engineer) | rigor sem profundidade extrema |
| Synthesize multi-source | recall + redação |
| Conteúdo Instagram (post, caption) | criatividade + correção |
| Geração de teste com lógica não-trivial | precisão de asserts |

**Latência:** 2-5s — **Custo:** $0.003-0.015

### Tier 3 — Opus 4.7 (~$0.015-0.075/call)
**Quando usar:** raciocínio profundo + impacto alto

| Operação | Justificativa |
|----------|---------------|
| Decisão arquitetural crítica (@architect) | impacto alto, irreversível |
| Conselho deliberativo (@mestre-do-conselho) | múltiplas perspectivas |
| Validar elevação de heurística para rule | mudança constitucional |
| Spec critique cross-cutting | raciocínio sistêmico |
| Refactor de codebase grande (>100 files) | visão holística |
| Análise adversarial (@advogado-do-diabo) em decisão de R$10k+ | risco alto |

**Latência:** 5-15s — **Custo:** $0.015-0.075

### Tier 4 — Multi-Provider Fallback
**Quando usar:** workload massivo OU resiliência

| Provider | Use case |
|----------|----------|
| **Gemini 3.5 Flash** (via `agy` CLI) | scan massivo de codebase, multimodal, contexto longo barato (100x mais barato que Sonnet) |
| **GPT-5.5** (via `codex` CLI, login ChatGPT) | revisão crítica adversarial, dual-mode com Claude para cross-validation |
| **DeepSeek V4** (via OpenRouter) | tarefas massivas baratas (100x mais barato que Sonnet), classificação em escala |
| **Ollama local** (qwen3, llama 3) | privacy-critical, $0, latência ms-em-rede |

---

## Decision Matrix — Como Escolher

```
Pergunta 1: Operação é determinística (regra fixa)?
  SIM → Tier 0 (local/WASM)
  NÃO → Pergunta 2

Pergunta 2: Output é classificação/extração simples?
  SIM → Tier 1 (Haiku)
  NÃO → Pergunta 3

Pergunta 3: Decisão é irreversível OU impacto >R$5k?
  SIM → Tier 3 (Opus)
  NÃO → Pergunta 4

Pergunta 4: Volume é massivo (>1000 chamadas estimadas)?
  SIM → Tier 4 (Gemini Flash ou DeepSeek)
  NÃO → Tier 2 (Sonnet) — DEFAULT
```

## Model Overlays — Voz por Modelo (absorvido do gstack, 26-Jun-2026)

O routing acima decide **qual** modelo. Os overlays decidem **como falar com cada um** — porque cada modelo tem vícios e forças distintos. São patches comportamentais, **subordinados** à instrução da skill/agente (nunca a sobrescrevem).

Diferença do conceito do gstack: overlays **não são tiers de fallback** — são preferências de comportamento, composáveis por herança (`opus` herda de `claude`).

**Localização:** `~/.claude/model-overlays/` — um `.md` por modelo (`claude`, `opus`, `sonnet`, `haiku`, `gpt`, `gemini`, `deepseek`) + `README.md`.

**Como aplicar:** ao delegar para um modelo (Agent tool com `model` diferente, ou CLI `agy`/`codex`), injete o overlay no prompt:
```bash
OVERLAY=$(cat ~/.claude/model-overlays/gemini.md)
agy "$OVERLAY"$'\n\n'"<tarefa real>"
```

**Voz por modelo (resumo):**

| Modelo | Patch comportamental |
|--------|----------------------|
| Opus | nega raciocínio superficial; expõe alternativas em decisão irreversível |
| Sonnet | equilíbrio; executa mecânico sem narrar; sinaliza quando escalar p/ Opus |
| Haiku | saída mínima/estruturada; declara quando precisa de Sonnet |
| GPT-5.5 | anti-verbosidade; papel cético (refutar, não elogiar) |
| Gemini Flash | aproveita contexto longo/multimodal; recall sobre prosa |
| DeepSeek | volume; saída estruturada; volta p/ Claude validar |

---

## Dual-Mode (Claude + Codex) — quando justifica

Adaptação do ruflo dual-mode protocol. Use quando:

- **Cross-validation de código**: Claude implementa, Codex revisa (ou vice-versa)
- **Velocidade paralela**: 4 workers Codex implementam em paralelo, 1 Claude orchestrador
- **Custo + qualidade**: Codex barato para bulk transforms, Claude pontual para edge cases

**Setup verificado (26-Jun-2026):**
- `codex` CLI instalado globalmente (`~/.npm-global/bin/codex`, v0.142.2)
- Modelo real: **`gpt-5.5`** (não "GPT-5" genérico)
- Auth: **login via ChatGPT** (`codex login status` → "Logged in using ChatGPT") — consome a assinatura, **NÃO** a API key paga por token. O pressuposto antigo de "API key OpenAI separada + custo adicional" está **superado** para uso pessoal/dev.
- Defaults seguros: `approval: never` + `sandbox: read-only` — Codex só lê e responde por padrão, ideal para o papel de revisor adversarial.

**Wrapper canônico:** `~/scripts/dual-review.sh` (Claude implementa → Codex revisa o diff).
```bash
~/scripts/dual-review.sh                       # revisa git diff do repo atual
~/scripts/dual-review.sh --staged              # revisa apenas mudanças staged
~/scripts/dual-review.sh arquivo1.ts arquivo2.ts   # revisa arquivos específicos
~/scripts/dual-review.sh --task "descrição"    # contexto extra para o revisor
```

Chamada crua equivalente (quando precisar de controle fino):
```bash
codex exec --skip-git-repo-check "Revise adversarialmente este diff e aponte bugs:\n$(git diff)"
```

NOTA: `--skip-git-repo-check` só é necessário fora de um repo git. Em projetos versionados, o Codex roda sem a flag. Dual-mode com 4+ workers paralelos só justifica em features grandes onde o paralelismo paga a complexidade de orquestração.

---

## Provider-Fallback em Agentes/Skills

Toda skill/agente DEVE declarar provider-fallback no frontmatter:

```yaml
---
name: my-skill
provider-fallback:
  - anthropic/claude-sonnet-4-6     # primário
  - openai/gpt-5.5                  # fallback se Anthropic overloaded (via codex CLI)
  - google/gemini-3.5-flash         # fallback barato
---
```

Quando o primário falha (rate limit, overload), o sistema tenta o próximo automaticamente.

---

## Cache Awareness (Anthropic Prompt Cache)

TTL do cache: **300 segundos**. Estratégias:

| Cenário | Estratégia |
|---------|------------|
| Background worker rodando em loop | `ScheduleWakeup(270s)` — fica dentro da janela |
| Mesma sessão >5min | Cache miss inevitável — não otimizar |
| Briefings carregados frequentemente | `/preload` skill aquece cache no início do dia |
| Hooks rápidos | NÃO mexer em cache, foco em latência |

Economia esperada com cache hit: **~90%** sobre cold call do mesmo prefixo.

---

## Métricas e Observabilidade

Rastrear (via `/benchmark` weekly):
- Custo $ por agente / por skill / por dia
- Hit rate de cache do Anthropic
- Distribuição de chamadas por tier (Tier 0/1/2/3/4)
- Custo por feature completada via SDC/SPARC-SDC

Meta: **>60% das chamadas em Tier 0/1**, **<10% em Tier 3+**

---

## ⚠️ ALERTA CRÍTICO — Claude Code CLI rodando em Opus

**Detectado por `@cost-watchdog` (signals.json):**
- 13 a 24-Mai (11 dias): **R$ X.XXX em 6 alertas**
- Padrão recorrente: Bash + Edit + Write dominantes (>200 tools/sessão) com modelo Opus
- Custo médio/dia: R$ X.XXX
- Anualizado linear: R$ X,X MM

**Diagnóstico:** sessões Claude Code CLI rodando em Opus 4.7 (1M context) sem necessidade de raciocínio profundo. Bash/Edit/Write são execução mecânica — Tier 2 (Sonnet) basta.

**Recomendação operacional:**

| Quando usar Opus 4.7 CLI | Quando usar Sonnet 4.6 CLI |
|--------------------------|-----------------------------|
| Análise comparativa profunda (ruflo vs SF) | Implementação de feature (Bash+Edit) |
| Conselho deliberativo (multi-perspectiva) | Refactor mecânico |
| Decisão arquitetural irreversível | Sprint review |
| Spec critique cross-cutting | Code review de PR |
| Avaliação de proposta de R$10k+ | Cleanup, organização, docs |

**Trocar mid-session:**
```
/model sonnet
```

**Trocar default permanente:** adicionar em `~/.claude/settings.json`:
```json
{"model": "sonnet"}
```

Mantém Opus disponível via `/model opus` quando necessário.

---

## Anti-Patterns

| Evitar | Por quê |
|--------|---------|
| Usar Opus para tarefa que Haiku resolve | Desperdício 10x |
| Não declarar fallback em skill | Quebra quando Anthropic está down |
| Embeddings via API (OpenAI text-embedding) | ONNX local faz mesmo com $0 |
| Sonnet para extração de campos JSON | Haiku faz com mesma precisão |
| Opus para "ser cuidadoso" sem decisão real | Premium sem ROI |
| Skip de cache warming em background workers | Custo desnecessário |
| Loop de retry no mesmo modelo após failure | Usar fallback chain |

---

## Integração com Outras Rules

| Rule | Como interage |
|------|---------------|
| `cost-optimizer` (agente) | Monitora distribuição de tiers, sugere descidas |
| `model-routing-multi-llm.md` (rule always, resumo) | Esta é a versão estendida — 3 tiers → 4 tiers, mapeamento agente→modelo absorvido nesta full |
| `multi-ia-portability.md` | Frontmatter `harnesses` + `provider-fallback` |
| `token-economy.md` | Tier 1/2/3 são as práticas dessa rule |

---

## Onde os ganhos aparecem

| Otimização | Economia esperada |
|------------|-------------------|
| Tier 0 (WASM/local) para 30% das ops | -10% custo total |
| Tier 1 (Haiku) para 40% das ops antes em Sonnet | -25% custo total |
| Cache hit consistente em background workers | -15% custo total |
| Multi-provider para workloads massivos (Gemini Flash) | -50% em scan/extract |
| Provider fallback (resiliência) | mantém uptime sem custo de premium |

**Meta agregada do framework v7.7:** -40% custo total de tokens em comparação com v7.6, mantendo ou melhorando qualidade.

---

## Absorção INEMA (2026-06-28)

### 1. bs-benchmark INEMA — Calibração por Confiabilidade

Fonte: https://inematds.github.io/bs-benchmark/viewer/index.v2.html

O bs-benchmark INEMA mede **confiabilidade** (menos alucinação + mais consistência entre rodadas), não apenas capacidade geral. Essa métrica é mais relevante para agentes em produção do que LMSys Elo puro, que mede preferência humana em chat.

**Como usar nas decisões de routing:**
- Consultar bs-benchmark + LMSys Elo em conjunto antes de promover/rebaixar um modelo de tier
- Preferir modelos com bs-score alto para agentes que fazem afirmações factuais (@analyst, @market-intel, @traffic)
- Modelo com Elo alto mas bs-score baixo = bom para brainstorming, arriscado para lookup de dados

### 2. Tier 0 Expandido — Gemma 4 e Qwen2.5-Coder-7B via Ollama

Dois modelos locais validados para ~80% das tarefas mecânicas de coding:

**Gemma 4 (Google):**
```bash
ollama pull gemma4
# Expor para Claude Code via base URL local:
ANTHROPIC_BASE_URL=http://localhost:11434/v1 claude
```
Custo: $0. Ideal para: refactor mecânico, extração estruturada, boilerplate de testes.

**Qwen2.5-Coder-7B (Alibaba):**
```bash
ollama pull qwen2.5-coder:7b
```
Requisito: 16-32 GB RAM. Janela: 128K contexto. Melhor que Gemma 4 para tarefas de coding com lógica não-trivial.

**Quando descer para Ollama local ao invés de Haiku:**
- Tarefa de coding repetitiva em loop (ex: transformar 100 arquivos)
- Privacidade: código de cliente que não pode sair da máquina
- Rate limit da API Anthropic/Google

### 3. Tier 4 — Qwen3.6-Plus (Alibaba) — Raciocínio Persistente

**Capacidade única:** raciocínio persistente ENTRE etapas — outros modelos resetam contexto a cada turn; Qwen3.6-Plus mantém estado de raciocínio ao longo de um workflow multi-etapa.

**Setup:**
```bash
npm install -g @qwen-code/qwen-code@latest
# Autenticação via OAuth (login único)
# Quota gratuita: 1.000 chamadas/dia
```

**Quando usar:**
- Agentic coding longo (>10 steps) onde perder o fio de raciocínio é custoso
- Tasks tipo "planeje E implemente E valide E documente" em uma sessão contínua
- Alternativa a Opus quando o problema é persistência de raciocínio, não profundidade episódica

**Quando NÃO usar:**
- Tarefas curtas (overhead de setup)
- Quando privacy é crítica (serviço cloud Alibaba)

### 4. Z.AI Base URL — GLM-4.6 como Provider Barato

Provider alternativo compatível com Anthropic SDK — troca apenas a base URL:

```bash
export ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
export ANTHROPIC_DEFAULT_OPUS_MODEL=glm-4.6-thinking
export ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4.6
export ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.6-flash
```

Permite rodar Claude Code CLI apontando para GLM-4.6 sem mudar código. Útil quando:
- Anthropic está com rate limit alto
- Custo de tokens precisa ser reduzido ainda mais
- Teste de comportamento cross-provider sem mudar tooling

**Nota de qualidade:** GLM-4.6 é competitivo em código mas inferior ao Sonnet em nuance e reasoning profundo. Use como Tier 4 de fallback, não como default.

### 5. Monitorar (não absorver ainda) — Claude Mythos/Capybara

Nova tier CLIENTE_EXEMPLO Opus em testes internos Anthropic (sem data de release pública). Expectativa: contexto ainda maior + raciocínio multi-domínio mais robusto. Absorver somente quando:
- Preço/performance comparado ao Opus for avaliado com bs-benchmark INEMA
- Tier de uso (Tier 3 substituto ou nova Tier 5?) estiver definido
- Disponível via API sem waitlist

---

## Mapeamento Agente → Modelo (absorvido de model-routing.md, 07-Jul-2026)

| Agente | Modelo Padrão | Justificativa |
|--------|--------------|---------------|
| @architect, @advogado-do-diabo, @mestre-do-conselho | Opus | Decisão irreversível / síntese deliberativa multi-perspectiva |
| @po, @pm, @dev, @qa, @sm, @analyst, @market-intel, @content, @devops, @data-engineer, @copywriter, @traffic | Sonnet | Execução padrão — balanço custo/qualidade |
| Subtarefas mecânicas delegadas por qualquer agente (validar JSON, extrair campos, boilerplate) | Haiku | Economia — ver Tier 1 |

**Escalação:** Haiku falha → sobe Sonnet → falha → sobe Opus → falha → escala humano. Critérios de escalação: resposta genérica/superficial, erro lógico, raciocínio multi-step que o modelo não sustenta, confidence score < 0.5 (`confidence-guardrails.md`).

**Economia estimada por cenário:** sprint típica (20 tasks) sem roteamento = 20x Opus; com roteamento (4 Opus + 12 Sonnet + 4 Haiku) = ~60% economia. QA Loop (5 iterações) Sonnet vs Opus = ~80%. Extração em lote (50 items) Haiku vs Opus = ~90%.

**Mapeamento por fase de fluxo:** SDC Create/Validate/Implement/QA Gate = Sonnet (Opus se crítico); Spec Pipeline Gather/Write = Sonnet, Assess/Critique = Opus; Brownfield Discovery arquitetura = Opus, coleta de dados = Sonnet; tarefa avulsa simples = Haiku.

---

## Origem

- ruflo 3-Tier Model Routing (ADR-026)
- ruflo Agent Booster (WASM, $0 transforms)
- ruflo Dual-Mode (Claude + Codex parallel)
- INEMA 20-Mai-2026: TRIAD multi-modelo (Gemini Flash + Claude + GPT-5 + DeepSeek)
- Diretriz CEO 24-Mai-2026: "baratear custo de tokens"
- Verificação prática 26-Jun-2026: `codex` v0.142.2 instalado + testado (`codex exec`), modelo `gpt-5.5`, auth ChatGPT confirmada. Wrapper `~/scripts/dual-review.sh` criado.
- Absorção INEMA 28-Jun-2026: bs-benchmark, Gemma 4/Qwen2.5-Coder via Ollama, Qwen3.6-Plus, Z.AI base URL.
