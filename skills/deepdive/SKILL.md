---
name: deepdive
description: "Investiga um tópico cruzando CORTEX, web, RSS, Reddit, HN, INEMA e briefings em síntese única. Use para pergunta com 3+ ângulos, decisão de mercado, avaliação de tecnologia nova ou preparo de mentoria. NOT for: pesquisa web de um passo — é /research."
context_fork: true
axis: meta
harnesses:
  claude-code: full
  codex: native
  cursor: limited
  aider: limited
model-routing:
  retrieval: anthropic/claude-haiku-4-5
  synthesis: anthropic/claude-sonnet-4-6
  deep-analysis: anthropic/claude-opus-4-7
---

# /deepdive — Investigação Multi-Fonte

## Quando usar
- Pergunta com >3 ângulos possíveis
- Decisão estratégica que envolve "o que está acontecendo no mercado?"
- Antes de adotar tecnologia/ferramenta nova
- Para preparar mentoria com client sobre tópico que ele trouxe

## Como difere de /research

| Skill | Foco | Velocidade | Custo |
|-------|------|------------|-------|
| `/research` | Web pesado, único pass | Médio | Médio |
| `/deepdive` | Multi-source orquestrado | Lento | Alto-Médio |

## Pipeline (5 fases)

### Fase 1 — INTERNAL FIRST (CORTEX + briefings)
```bash
python3 ~/cortex/scripts/cortex_engine.py query "{topic}"
cat ~/cortex/briefings/{relevant-agent}.md
grep -l "{topic}" ~/consciousness/memory/procedural/heuristics.jsonl
```

Se CORTEX tem ≥5 notas relevantes com confidence alta, talvez nem precise external sources.

### Fase 2 — EXTERNAL (web + RSS + Reddit + HN)
```bash
# Multi-source paralelo
WebSearch "{topic} {current-year}"
mcp__rss-reader__fetch_feed_entries # feeds técnicos relevantes
mcp__reddit__get_subreddit_top_posts # subreddit do nicho
mcp__hacker-news__getTopStories # HN para tópicos tech
```

### Fase 3 — INEMA (se aplicável)
```bash
grep -ri "{topic}" ~/projetos/telegram-scraper/output/*.txt | head -30
```

INEMA tem 125K+ mensagens em 32 grupos Telegram de comunidades IA brasileiras. Para tópicos de mentoria IA, é fonte primária.

### Fase 4 — CROSS-VALIDATE
Compare findings entre fontes. Conflitos? Sinalize. Confluência? Confidence sobe.

### Fase 5 — SYNTHESIZE
Gera nota CORTEX com:
- Resumo executivo (5 linhas)
- Top findings (5-10 bullets com source attribution)
- Conflitos não resolvidos
- Recomendação acionável (com confidence)
- Links para sources primários
- Next steps

## Output Format

```markdown
# Deepdive — {Topic} ({date})

## Resumo Executivo
{5 linhas máximas}

## Findings

### CORTEX (interno)
- [{slug}](path) — finding 1 [confidence: 0.9]
- ...

### Web
- [Artigo](url) — finding 2 [confidence: 0.7]
- ...

### Reddit/HN
- [Thread](url) — sentiment + key insights
- ...

### INEMA (se aplicável)
- Grupo X mencionou Y em N ocasiões — finding [confidence: 0.8]

## Cross-Validation

✅ Confluência: A, B, C confirmados por ≥3 fontes
⚠️ Conflito: Source X diz P, Source Y diz não-P. Verificar.

## Recomendação

{Acionável, com confidence score declarado}

## Next Steps

- [ ] {ação concreta 1}
- [ ] {ação concreta 2}
```

## Quality Gate

- [ ] ≥3 fontes diferentes consultadas
- [ ] Cada finding tem source attribution
- [ ] Conflitos explicitamente sinalizados
- [ ] Confidence declarado em afirmações factuais
- [ ] Recomendação é acionável (verbo + objeto)

## Multi-LLM Economia

| Fase | Modelo | Justificativa |
|------|--------|---------------|
| 1 — Internal | Local search | $0 |
| 2 — External fetch | API/Web (não LLM) | $0 |
| 3 — INEMA grep | Local | $0 |
| 4 — Cross-validate | Haiku | classificação simples |
| 5 — Synthesize | Sonnet | linguagem natural |
| 5+ — Deep analysis (opcional) | Opus | apenas se sinalização pede |

Custo típico de um deepdive completo: $0.30-1.50 dependendo da profundidade.

Origem: ruflo worker `deepdive` + nossa skill `/research` + INEMA scraper.
