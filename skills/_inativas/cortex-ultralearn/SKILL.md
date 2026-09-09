---
name: cortex-ultralearn
description: "Faz scan profundo de um codebase/projeto novo e popula o vault CORTEX com notas estruturadas (multi-LLM — Gemini Flash para scan, Sonnet para síntese). Use na primeira sessão em um cliente novo, após refator grande (≥100 arquivos), ou quando um agente disser 'não conheço esse projeto'."
context_fork: true
axis: meta
harnesses:
  claude-code: full
  codex: native
  cursor: limited
  aider: limited
model-routing:
  scan: google/gemini-3.5-flash
  synthesis: anthropic/claude-sonnet-4-6
  embedding: onnx-local-384d
---

# /cortex-ultralearn — Aprendizado Profundo de Codebase

## Quando usar
- Primeira sessão em projeto cliente novo (ex: chegar em CLIENTE_EXEMPLO, CLIENTE_EXEMPLO, CLIENTE_EXEMPLO_2)
- Após refator grande (≥100 arquivos mudados)
- Para popular CORTEX com conhecimento técnico do projeto antes de iterar
- Quando agente diz "não conheço esse projeto"

## Como funciona

Pipeline em 4 fases (cada fase usa o modelo certo para baratear tokens):

### Fase 1 — INVENTORY (Gemini Flash, multimodal, contexto longo barato)
```bash
# Lista tudo
find {project_root} -type f \( -name "*.md" -o -name "*.ts" -o -name "*.tsx" \
  -o -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.go" \
  -o -name "*.rs" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" \
  -o -name "*.toml" -o -name "*.sql" -o -name "Dockerfile" \) \
  -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/dist/*" \
  > /tmp/ultralearn-files.txt
```

Saída: contagem total, distribuição por linguagem, tamanho do codebase.

### Fase 2 — EXTRACT (Gemini Flash em batch)
Para cada arquivo relevante:
- Extrair: package name, dependências, exports, imports
- Classificar: tipo (entry, lib, test, config, docs)
- Identificar: padrões arquiteturais (DDD, MVC, etc)

Modelo: **`gemini-2.5-flash` via `agy` CLI** — 100x mais barato que Sonnet para extração estruturada.
Invocar: `GEMINI_CLI_TRUST_WORKSPACE=true agy --skip-trust -p "..." --model gemini-2.5-flash`
(gemini-2.0-flash tem quota 0 no free tier — usar 2.5-flash validado em 24-Mai-2026)

### Fase 3 — SYNTHESIZE (Sonnet apenas)
Consolidar em notas CORTEX estruturadas:

```yaml
---
id: {slug}-architecture
type: architecture
axis: meta
project: {project_name}
client: {client_if_applicable}
---

# Arquitetura — {Project}

## Stack
{detected}

## Bounded Contexts
{detected via DDD heuristics}

## Hot Paths
{top 10 files by inlinks}

## Pain Points
{detected anti-patterns}
```

Gera 5-15 notas por projeto:
- `{slug}-architecture.md`
- `{slug}-stack.md`
- `{slug}-conventions.md`
- `{slug}-dependencies.md`
- `{slug}-pain-points.md`
- `{slug}-hot-paths.md`
- `{slug}-test-coverage.md` (se houver testes)

### Fase 4 — INDEX
```bash
python3 ~/cortex/scripts/cortex_engine.py build-index
python3 ~/cortex/scripts/cortex_engine.py build-briefings
```

Atualiza briefings de @dev, @architect com novo conhecimento do projeto.

## Quality Gate

- [ ] ≥5 notas geradas
- [ ] Toda nota tem `axis:` no frontmatter
- [ ] `cortex_engine.py query "{project_name}"` retorna ≥3 resultados
- [ ] Briefings de @dev/@architect incluem novo projeto
- [ ] Relatório executivo gerado em `~/cortex/reports/ultralearn-{project}-{date}.md`

## Execução

```bash
# Modo padrão
bash ~/cortex/scripts/ultralearn.sh --project ~/clientes/CLIENTE_EXEMPLO --client CLIENTE_EXEMPLO

# Modo deep (inclui análise de teste coverage, security audit superficial)
bash ~/cortex/scripts/ultralearn.sh --project ~/clientes/CLIENTE_EXEMPLO --client CLIENTE_EXEMPLO --deep

# Modo cheap (apenas Gemini, sem Sonnet)
bash ~/cortex/scripts/ultralearn.sh --project ~/clientes/CLIENTE_EXEMPLO --client CLIENTE_EXEMPLO --cheap
```

## Economia de Tokens

| Fase | Modelo | Custo estimado (codebase ~500 files) |
|------|--------|---------------------------------------|
| Inventory | Bash/find | $0 |
| Extract | Gemini 3.5 Flash | ~$0.05 |
| Synthesize | Sonnet | ~$0.40 |
| Index | Python local | $0 |
| **Total** | | **~$0.45** |

VS rodar tudo em Opus: ~$15. **Economia: 97%.**

## Anti-Patterns

| Evitar | Por quê |
|--------|---------|
| Rodar em codebase >5000 arquivos sem `--cheap` | Custo explode |
| Pular index após gerar notas | Briefings não atualizam |
| Não marcar `client:` no frontmatter | Mistura conhecimento entre clientes |
| Rodar sem `--deep` em cliente crítico | Insights superficiais |

Origem: ruflo loop-worker `ultralearn` + INEMA multi-LLM strategy (Gemini para velocidade barata).
