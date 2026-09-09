---
id: multi-ia-portability
title: Multi-IA Portability — Skills e Prompts IA-Agnósticos
type: rule
domain:
- meta
triggers:
- skill
- harness
- portável
- portavel
- portabilidade
- codex
- cursor
- aider
- gemini cli
- frontmatter
- prompt
- comando
- command
- agente
- agent
- criar skill
- persona
- refator
- slash
- delegar
links:
- target: axis-separation-full
  type: auto-linked
- target: model-routing-multi-llm-full
  type: auto-linked
- target: inema-delta-2026-05-22-orchestrator-multi-ia
  type: auto-linked
- target: segunda-feira-upgrade-multi-ia-orchestrator-2026-05-22
  type: auto-linked
---

# Multi-IA Portability — Skills e Prompts IA-Agnósticos

> **Severidade:** SHOULD | **Aplica-se a:** Todos os agentes, especialmente os que criam skills/prompts
> **Origem:** Decisão CEO 22-Mai-2026 após análise INEMA delta (Codex feature-parity + Antigravity 2.0 + TRIAD multi-modelo). Framework deve ser usável por qualquer LLM agentic — não só Claude Code.

## Princípio

Segunda-feira é um **orquestrador de IA**, não um wrapper do Claude. Skills, prompts, rules e workflows devem ser portáveis para Codex (OpenAI), Antigravity (`agy`), Cursor, Aider, Gemini CLI, e futuras ferramentas.

**Regra de ouro:** "Se sua skill só funciona porque é Claude Code rodando, ela não é uma skill do framework — é um truque do Claude."

---

## O que evitar (Claude-specific patterns)

| Anti-pattern | Por que falha em outros LLMs | Alternativa portável |
|--------------|------------------------------|----------------------|
| Comandos `/btw`, `/fork`, `/dream`, `/auto-mode` | Específicos do Claude Code | Documentar comportamento equivalente em natural language |
| Persona "você é Claude..." em system prompt | GPT/Gemini ignoram ou re-interpretam | Persona neutra: "você é um agente de tráfego DOMINA.IA" |
| Tool calls com nome específico (`Glob`, `WebSearch`) | Não existem em Codex/Aider | Usar `Bash` (universal) ou descrever em natural language |
| Output esperando markdown muito específico (`★ Insight`) | Estilo específico do Claude Code Explanatory | Output estruturado por seção, não por glifo |
| Sintaxe `@agent-name` para spawn paralelo | Só funciona via Agent tool do Claude Code | Documentar como "delegar para agente X" — cada IA implementa diferente |
| Esperar `Read`/`Edit`/`Write` como tools nomeadas | Codex tem outros nomes | Usar `Bash` (cat, sed, tee) ou aceitar variação |

## O que adotar (cross-IA patterns)

### 1. AGENTS.md como instrução canônica
- Symlink `AGENTS.md → CLAUDE.md` (já feito em ~/ e /opt/segunda-feira)
- Codex reconhece nativamente (https://developers.openai.com/codex/guides/agents-md)
- Cursor lê via .cursorrules + AGENTS.md
- Aider lê CONVENTIONS.md ou AGENTS.md

### 2. Skill frontmatter declara harnesses suportadas
```yaml
---
name: campaign-report
description: Gera relatório completo de campanha Meta Ads
harnesses:
  - claude-code: full
  - codex: native
  - cursor: limited (sem subagentes)
  - aider: limited (sem MCP)
provider-fallback:
  - anthropic/claude-opus-4-7
  - openai/gpt-5
  - google/gemini-3.5-flash
---
```

### 3. Prompts parametrizados por modelo
Quando comportamento difere entre modelos, declarar:
```
# Para Claude (premium): análise multi-camada, EROS veredito
# Para GPT-5 (reasoning): focar em raciocínio passo-a-passo
# Para Gemini (multimodal): aproveitar imagens/PDFs sem encoding
```

### 4. Outputs neutros vs decorados
- Output funcional: lista markdown, tabelas, código (todos LLMs renderizam)
- Decoração extra (emoji bordas, ★ insights): só quando harness é Claude Code

### 5. Tool calls como Bash quando possível
```bash
# Portável em Claude Code, Codex, Cursor, Aider:
cat ~/cortex/vault/infra/vps-principal.md | grep -i "porta"

# Claude-specific:
Read({file_path: "~/cortex/vault/infra/vps-principal.md"})
```

---

## Schema Canônico de Frontmatter (decisão 2026-07-07 — Sprint 2 Nota 9)

Todo frontmatter novo ou refatorado DEVE seguir este schema. Formatos divergentes legados são migrados em batch.

### Skills (`~/.claude/skills/*.md` ou `<dir>/SKILL.md`)
```yaml
---
name: nome-da-skill                    # kebab-case, = nome do arquivo
description: "Faz X — Use quando Y. NOT for: Z (isso é /outra-skill)."  # gatilho + fronteira SEMPRE
user-invocable: true                   # com HÍFEN (user_invocable é typo legado)
disable-model-invocation: true         # APENAS quando só cron/humano deve invocar (side-effects)
allowed-tools:                         # lista YAML (formato único; 'tools:' em skill é legado)
  - Read
  - Bash
harnesses: [claude-code]               # mínimo; adicionar codex/agy/cursor quando testado
axis: meta                             # meta | ops (mesmo critério da rule axis-separation)
---
```

### Agentes (`~/.claude/agents/{meta,ops}/*.md`)
```yaml
---
name: nome-do-agente
description: "Faz X — Use quando Y. NOT for: Z (isso é @outro-agente)."  # superfície de roteamento do Agent tool
model: sonnet                          # haiku=mecânico · sonnet=DEFAULT · opus=só deliberação crítica
tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]  # array JSON, mínimos necessários
---
```

Campos proibidos em qualquer frontmatter: credenciais, paths de `~/Downloads`, referências a `.aios-core`.

## Como aplicar em skill nova

Antes de criar/refator skill, perguntar:

1. **A skill depende de tool Claude-only?** Se sim, declarar `harnesses` reduzidos.
2. **O prompt assume comportamento Claude?** Se sim, generalizar.
3. **A skill chama outro agente via `@nome`?** Se sim, abstrair como "delegar para [função]".
4. **O output usa formatação Claude Code (Explanatory style)?** Se sim, ter fallback texto puro.
5. **Há fallback se LLM primário falhar?** Documentar próximo na chain.

## Quando NÃO se aplica

Skills que SÓ fazem sentido no Claude Code podem permanecer Claude-specific se:
- Não há equivalente real em outras ferramentas (ex: hook PostToolUse)
- O custo de generalizar > valor da portabilidade
- Audience é exclusivamente Claude Code (skill interna de admin)

Declarar `harnesses: {claude-code: full, codex: none, cursor: none}` é honesto — melhor que pretender portabilidade que não existe.

---

## Validação automática (futuro)

Pre-commit hook (não implementado ainda) que scaneia skills novas por:
- Comandos slash exclusivos sem fallback
- Tool calls com nomes Claude-only
- Frontmatter sem campo `harnesses`

Por enquanto: revisão manual + esta rule como guideline.

---

## Integração com outras rules

| Rule | Como interage |
|------|---------------|
| `axis-separation.md` | Portabilidade é META (sobre processo), não OPS |
| `eros-quality.md` | Portão 5 (Liberação) deve incluir "skill é portável?" para skills novas |
| `credentials-handling.md` | Cada LLM tem credencial separada — .env por vendor |
| `cortex-usage.md` | Notas CORTEX são markdown puro — já portáveis |
