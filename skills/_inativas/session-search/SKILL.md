---
name: session-search
description: "Busca full-text (FTS5/SQLite, custo zero) sobre todo o histórico de sessões — episódios, mailbox e signals — em 3 modos: discovery (busca por termo), browse (recentes cronológico), context (janela ao redor de um evento). Use quando precisar recuperar contexto de tarefa antiga, localizar heurística mencionada em sessão passada, ou verificar se já passou por algo ANTES de pesquisar na web. NOT for: recapitular só o dia de hoje — isso é /today-recap."
axis: meta
harnesses:
  claude-code: full
  codex: native
  cursor: limited
  aider: limited
model-routing:
  primary: local-sqlite-fts5
  optional-summary: anthropic/claude-haiku-4-5
---

# /session-search — Busca FTS5 no Histórico de Sessões

## Quando usar
- "O que eu fiz ontem sobre X?"
- "Onde estava quando lidei com Y?"
- Procurar heurística mencionada em sessão passada
- Recuperar contexto de tarefa antiga
- ANTES de gh search, web search, ou pergunta — verifique se já passou por isso

## Como usar (3 modos)

### Modo 1 — DISCOVERY (busca por query)
```bash
python3 ~/cortex/scripts/sessions_db.py search "termo"
python3 ~/cortex/scripts/sessions_db.py search "deploy clienteexemplo" --limit 5
python3 ~/cortex/scripts/sessions_db.py search "ruflo" --agent sf-master
python3 ~/cortex/scripts/sessions_db.py search "campanha" --type episodic
```

Filtros disponíveis:
- `--limit N` (default 10)
- `--type {episodic|mailbox|signal}` para restringir fonte
- `--agent {nome}` para restringir agente
- `--json` para output estruturado

### Modo 2 — BROWSE (recentes cronológicos)
```bash
python3 ~/cortex/scripts/sessions_db.py browse --limit 20
```

Útil quando não sabe o termo exato — mostra o que aconteceu ultimamente.

### Modo 3 — CONTEXT (janela em torno de um id)
```bash
python3 ~/cortex/scripts/sessions_db.py context 2382 --window 5
```

Após um `search`, pega o id retornado e usa context para ver o que veio antes/depois.

## Sintaxe FTS5

Query FTS5 suporta:
- **AND implícito:** `deploy node` → DEVE ter ambos
- **OR explícito:** `deploy OR push OR release`
- **Frase exata:** `"docker networking"`
- **Boolean:** `python NOT java`
- **Prefixo wildcard:** `deploy*` (pega deploy, deployed, deploying)
- **NEAR:** `deploy NEAR/5 production` (próximos em 5 palavras)

## O que está indexado

| Fonte | Conteúdo | Quantidade típica |
|-------|---------|-------------------|
| `episodic` | Episódios do consciousness (summary + heurística + worked/failed) | ~2500+ |
| `mailbox` | Mensagens inter-agente (subject + body) | 30-50 |
| `signal` | Sinais broadcast (type + message + payload) | 50+ |

**Não indexa ainda:**
- Transcripts brutos de sessões Claude Code (gap futuro)
- Notas CORTEX (use `cortex_engine.py query` para isso)

## Manutenção

```bash
# Reindexar (após muitas sessões novas)
python3 ~/cortex/scripts/sessions_db.py rebuild

# Estatísticas
python3 ~/cortex/scripts/sessions_db.py stats
```

Recomendação: rebuild semanal (cron sexta 23h) OU sob demanda quando search retorna menos do que esperava.

## Diferença vs CORTEX query

| Sistema | Indexa | Quando usar |
|---------|--------|-------------|
| `cortex_engine.py query` | Notas markdown do vault (1.7k notas) | Conhecimento estruturado, padrões, heurísticas curadas |
| `/session-search` | Episódios + mailbox + signals (~2500 entries) | "O que aconteceu quando" — busca temporal |

São **complementares**, não redundantes.

## Heurísticas

- **H1:** Antes de perguntar "como resolvi X?", rode `/session-search "X"` — geralmente está lá
- **H2:** Busca FTS5 é gratuita (zero LLM). Use à vontade, é mais barato que perguntar
- **H3:** Após search com hit relevante, use `context` para reconstruir o flow completo
- **H4:** Para análise temporal, browse > search (não precisa termo)

## Multi-LLM

| Operação | Tier |
|----------|------|
| Search FTS5 | Tier 0 (SQLite local) — $0 |
| Browse | Tier 0 — $0 |
| Context window | Tier 0 — $0 |
| Sumarização de hit longo (opcional) | Tier 1 (Haiku) |

Default 100% Tier 0. Zero custo de tokens para uso normal.

## Origem

Adaptado de [hermes-agent/tools/session_search_tool.py](https://github.com/NousResearch/hermes-agent/blob/main/tools/session_search_tool.py) — versão simplificada do single-shape tool de 3 modos do Hermes. Mantém a semântica DISCOVERY/SCROLL/BROWSE.
