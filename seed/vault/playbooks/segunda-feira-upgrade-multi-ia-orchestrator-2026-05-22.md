---
id: segunda-feira-upgrade-multi-ia-orchestrator-2026-05-22
title: Segunda-feira — Upgrade Multi-IA Orchestrator (Roadmap 5 Fases)
type: playbook
status: active
created: '2026-05-22'
last_verified: '2026-05-22'
domain:
- framework
- ai-orchestration
agents:
- sf-master
- architect
- automation-architect
- dev
- people-ops
tags:
- segunda-feira
- multi-ia
- orchestrator
- codex
- antigravity
- agents-md
- model-routing
decay_rate: 0.02
axis: meta
links:
- target: inema-delta-22-mai-a-11-ago-2026-skills-como-unidade-de-trabalho
  type: auto-linked
- target: multi-ia-portability
  type: auto-linked
- target: inema-delta-2026-05-22-orchestrator-multi-ia
  type: derived_from
- target: agent-teams-claude-code
  type: relates_to
- target: voice-orchestrator-5-agents
  type: relates_to
- target: framework-vps-deployment-fase-a-2026-05-22
  type: relates_to
- target: inema-delta-2026-05-22-orchestrator-multi-ia
  type: related
- target: cli-model-default-decision
  type: related
- target: namespaces-readme
  type: related
- target: framework-optimization-roadmap
  type: related
- target: segunda-feira-v7-5-consolida-o-total
  type: related
- target: paperclip-patterns-absorvidos-story-epic-1
  type: related
- target: mastra-arquitetura-geral-ultralearn-2026-05-24
  type: related
---

# Segunda-feira — Upgrade Multi-IA Orchestrator

## Princípio

O Segunda-feira atual é **agnóstico em conceito mas dependente em runtime do Claude Code**. Para virar orquestrador real de IA, precisa ganhar 3 camadas:

1. **Convenção cross-IA** (AGENTS.md, skills multi-harness, prompts portáveis)
2. **CLIs alternativos instalados** (codex, agy, aider) que o Claude Code pode invocar
3. **Camada de model-routing** que decide qual LLM por tarefa, com fallback chain

Cada fase é **idempotente, reversível, e entrega valor isolado**. Ordem é por confidence × custo crescente.

## Validação externa (do INEMA 22-Mai)

O design do Segunda-feira já está alinhado com a tese Karpathy/Anthropic:
- ✅ Memória 3 níveis (consciousness episódica + semântica + procedural)
- ✅ Comandos autônomos (`/goal`)
- ✅ Skills auto-geradas (heurísticas do Consciousness)
- ✅ Workflows estruturados (CLAUDE.md + rules + briefings)
- ❌ Switch livre entre modelos (só Claude hoje)
- ❌ Cross-IA convention (só CLAUDE.md, não AGENTS.md)
- ❌ CLIs alternativos instalados

Esta nota cobre os 3 ❌.

---

## FASE A — Convenção cross-IA (zero-risco, 1h)

Objetivo: Segunda-feira passa a ser legível por **qualquer agente IA** (Codex, Cursor, Aider, Gemini CLI, future tools).

### A1. Symlink AGENTS.md → CLAUDE.md
```bash
ln -s ~/.claude/CLAUDE.md ~/AGENTS.md
ln -s /opt/segunda-feira/.claude/CLAUDE.md /opt/segunda-feira/AGENTS.md
```
Resultado: qualquer agente IA que procurar `AGENTS.md` no projeto encontra. Padrão emergente Codex/Cursor/Aider.

### A2. Adicionar seção "AI-Agnostic" no CLAUDE.md
Esclarece que o framework não é exclusivo do Claude, lista compatibilidades:
```markdown
## Multi-IA Compatibility
Este framework é IA-agnóstico. Convenções cross-platform:
- `AGENTS.md` (symlink) — Codex, Cursor, Aider
- `CLAUDE.md` — Claude Code primary
- `.cursorrules` — Cursor (planned)
- `.aiderconfig` — Aider (planned)
```

### A3. Rule constitucional `multi-ia-portability.md`
Always-loaded, severity SHOULD. Documenta:
- Skills devem evitar comandos Claude-specific (`/btw`, `/fork`) sem fallback
- Prompts devem evitar persona-specific ("você é Claude...")
- Outputs devem ser parseáveis por qualquer LLM (não confiar em emoji-format-fluency)

### A4. Skill `/route-llm` (sugestão de modelo por tarefa)
Chat-skill que recebe descrição da tarefa e sugere LLM ideal:
- Input: "preciso analisar 50 PDFs e extrair temas"
- Output: "Use Gemini 3.5 Flash via `agy` (multimodal + barato + 1M context)"

**Esforço total Fase A:** ~1h. **Risco:** zero (apenas adiciona; nada quebra).

---

## FASE B — Instalar CLIs alternativos (baixo risco, 2h)

Objetivo: Claude Code pode invocar `codex`, `agy`, `aider` como subprocessos para delegar tarefas específicas.

### B1. Instalar `codex` CLI
```bash
brew install openai/tap/codex
# OU: curl -fsSL https://codex.openai.com/install.sh | sh
codex --version  # validar
codex auth      # autenticar (OpenAI account)
```

### B2. Instalar `agy` Antigravity CLI
```bash
# Conforme docs Google (URL pendente — agy lançado 20-Mai)
npm install -g @google-labs/antigravity-cli
# OU via brew quando disponível
agy --version
agy auth   # Google account
```

### B3. Instalar `aider` (open source, Sonnet via OpenRouter)
```bash
pip install aider-chat
# Config OpenRouter
echo 'OPENROUTER_API_KEY=...' >> ~/.env
aider --model openrouter/anthropic/claude-3.5-sonnet
```

### B4. Skill `/cross-call` (Claude chama outro LLM)
```yaml
---
name: cross-call
description: Invoca outro LLM (Codex, Antigravity, Aider) via CLI para delegação
---
Recebe: tarefa + qual LLM usar
Executa: subprocess.run("codex" | "agy" | "aider", input=task)
Retorna: output do LLM externo
```

**Validação:** rodar tarefa simples em cada CLI, confirmar autenticação.

**Esforço:** ~2h. **Risco:** baixo (instalações isoladas em PATH, removíveis com `brew uninstall`/`pip uninstall`).

---

## FASE C — Model-routing inteligente (médio risco, 4h)

Objetivo: orquestrador decide automaticamente qual LLM usar por tipo de tarefa.

### C1. Tabela de roteamento (decisão por keyword + custo)

```python
# ~/orchestrator/route.py
ROUTING_RULES = [
    # (keyword_match, model, cli, reasoning)
    (r"design|UI|UX|figma|color", "gemini-3.5-flash", "agy", "multimodal + design"),
    (r"refactor|debug|coding|architecture", "claude-opus-4-7", "claude", "dev premium"),
    (r"review|critique|audit|reasoning", "gpt-5", "codex", "revisão + raciocínio"),
    (r"summarize|extract|classify", "deepseek-v4", "openrouter", "tarefa barata massiva"),
    (r"scraping|automation|workflow", "claude-sonnet-4-6", "claude", "balanced"),
]
```

### C2. Fallback chain
Se LLM primário falhar (rate limit, timeout, error), tenta próximo:
```python
def call_with_fallback(task, primary, fallbacks=["gemini", "deepseek"]):
    for llm in [primary] + fallbacks:
        try: return call_llm(llm, task)
        except: continue
    raise Exception("Todos fallback exauridos")
```

### C3. Slash command `/orchestrate`
```
Uso: /orchestrate <descrição da tarefa>
Resultado: Claude analisa, decide LLM ideal, invoca, retorna resultado
```

### C4. Métricas de roteamento
Cada chamada cross-LLM registra: tarefa, LLM escolhido, latência, custo, sucesso. Vai pro Consciousness Engine. Após N execuções, heurística refina automaticamente.

**Esforço:** ~4h. **Risco:** médio (depende das credenciais Fase B; bugs em routing podem gerar custos extras).

---

## FASE D — Skills multi-harness (alto valor, 6h)

Objetivo: as 32 skills do segunda-feira passam a rodar em **qualquer IDE/CLI** (Claude Code, Codex, Cursor, Gemini).

### D1. Auditar skills atuais
Identificar Claude-specific:
- `Bash`/`Read`/`Edit` tool calls são padronizados → portáveis
- `@agente-name` invocações são Claude-only → criar abstração

### D2. Formato Impeccable-like
Estrutura proposta para skills cross-IA:
```yaml
---
name: skill-name
description: ...
harnesses:
  - claude-code: full
  - codex: native
  - cursor: native
  - aider: limited
provider-fallback:
  - anthropic
  - openai
  - google
---

## Behavior
[instruções em natural language, sem comandos Claude-specific]

## Tool requirements
[lista de tools necessárias, com fallback para shell]
```

### D3. Migrar top 5 skills mais usadas
- `campaign-report`
- `conteúdo-semanal`
- `crm-funnel-analysis`
- `whatsapp-bot`
- `deploy-hostinger`

### D4. Publicar repo público (opcional, marketing)
`github.com/${CEO_INSTAGRAM}/segunda-feira-skills` — Apache 2.0, like Impeccable. Atrai contribuidores + valida design no INEMA.

**Esforço:** ~6h (1h por skill). **Risco:** baixo (skills antigas continuam funcionando).

---

## FASE E — Codex Automations + cleanup crons (médio risco, 3h)

Objetivo: aproveitar **Codex Automations** built-in para crons agendados, reduzindo dependência de cron sistema.

### E1. Migrar `inema-weekly-scout.sh` para Codex Automation
Codex aceita automation em natural language ("toda sexta 9h, raspar grupos INEMA"). Mais legível, mais auditável.

### E2. Migrar `daily-digest.sh` similar

### E3. Manter no sistema apenas crons "infraestrutura" (consolidação CORTEX noturna, signal-router)

**Esforço:** ~3h. **Risco:** médio (depende da estabilidade do Codex Automations — recurso novo, pode mudar).

---

## Resumo executivo

| Fase | Esforço | Risco | Valor entregue |
|------|---------|-------|----------------|
| A — Convenção cross-IA | 1h | Zero | AGENTS.md + rule portabilidade |
| B — CLIs instalados | 2h | Baixo | codex, agy, aider rodáveis localmente |
| C — Model-routing | 4h | Médio | Orquestrador decide LLM por tarefa |
| D — Skills multi-harness | 6h | Baixo | Skills rodam em qualquer IDE |
| E — Codex Automations | 3h | Médio | Reduz dependência cron sistema |
| **Total** | **16h** | — | Segunda-feira vira **AI-agnostic orchestrator** |

## Sequência sugerida

1. **A1+A2** (15min): symlinks + seção CLAUDE.md
2. **A3+A4** (45min): rule + skill /route-llm
3. **B1** (30min): instalar codex
4. **B4** (30min): skill /cross-call simples
5. *Pausa para validar com tarefa real antes de B2 (agy) — economizar tempo se algo bloquear*
6. Sequência B2, B3, C, D, E conforme prioridade do CEO

## Métricas de sucesso

- [ ] AGENTS.md acessível em ~/ e /opt/segunda-feira
- [ ] Claude Code consegue invocar `codex` via Bash sem erro
- [ ] Pelo menos 1 tarefa real foi delegada para outro LLM com sucesso
- [ ] Skill `/orchestrate` roteou >5 tarefas em produção
- [ ] Custo cross-LLM <30% do custo total Claude Code (Gemini Flash $0.075/M é 167x mais barato que Opus $12.50/M input)
- [ ] Heurísticas extraídas no Consciousness sobre quando cada LLM é melhor

## Riscos a monitorar

- **Vendor lock-in de credencial:** múltiplas API keys vivendo em ~/.env. Mitigação: 1Password + .env por vendor com chmod 600.
- **Drift de comportamento:** GPT vs Claude vs Gemini respondem diferente. Skills devem ter prompt parameterizado.
- **Custo descontrolado:** cross-LLM sem limit pode gastar muito. Mitigação: orchestrator usa cost-watchdog do framework (já existe).
- **Antigravity CLI ainda é beta** (lançado 20-Mai-2026): Fase B2 pode ter problemas iniciais. Não bloquear A se B2 falhar.

## Próxima ação

Aguardar aprovação do CEO sobre quais Fases executar nesta sessão. Recomendação: **A1+A2+A3+A4 agora** (~1h, zero risco, alta visibilidade) + **B1+B4** (1h, baixo risco) = entrega visível em 2h.