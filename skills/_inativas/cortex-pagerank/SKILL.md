---
name: cortex-pagerank
description: "Ranqueia notas do CORTEX por importância (PageRank no grafo de [[links]] × frequência de acesso × decay temporal), listando top 50 load-bearing e bottom 50 candidatas a archive. Use mensalmente para auditar o vault, antes de propor remoção de notas, ou para identificar notas pivô/órfãs."
axis: meta
harnesses:
  claude-code: full
  codex: native
  cursor: full
  aider: full
model-routing:
  primary: sonnet
  embedding: onnx-local-384d
---

# /cortex-pagerank — Análise de Importância no Grafo CORTEX

## Quando usar
- Mensalmente para auditar saúde do vault
- Antes de propor remoção de notas
- Para identificar "notas pivô" que muitos agentes consultam
- Para detectar "notas órfãs" (zero links de entrada)

## Como funciona

PageRank clássico adaptado para o grafo de notas markdown do CORTEX:

```
score(N) = (1 - d) + d × Σ (score(M) / outlinks(M))
          para cada M que linka para N
```

Onde:
- `d` = damping factor (0.85)
- Convergência via iteração (até epsilon=1e-6 ou max 100 iters)
- Boost por frequência de acesso: `score *= (1 + log(access_count + 1) / 10)`
- Decay temporal: `score *= exp(-days_since_access / 365)`

## Execução

```bash
python3 ~/cortex/scripts/cortex_pagerank.py \
  --vault ~/cortex/vault \
  --damping 0.85 \
  --epsilon 1e-6 \
  --max-iter 100 \
  --include-access-stats \
  --include-temporal-decay \
  --output ~/cortex/reports/pagerank-$(date +%Y-%m-%d).json
```

Saída JSON:
```json
{
  "computed_at": "ISO-8601",
  "total_notes": 912,
  "top_50_loadbearing": [
    {"slug": "cortex-system", "score": 0.0421, "inlinks": 87, "access_count": 234},
    ...
  ],
  "bottom_50_orphans": [
    {"slug": "old-test", "score": 0.0001, "inlinks": 0, "access_count": 0, "days_since_access": 412},
    ...
  ],
  "axis_breakdown": {
    "meta": {"avg_score": 0.0023, "count": 621},
    "ops": {"avg_score": 0.0015, "count": 243},
    "unmarked": {"count": 48}
  }
}
```

## Quality Gate

- [ ] Convergência alcançada (epsilon < threshold)
- [ ] Top 50 inclui notas conhecidas como load-bearing (validation manual)
- [ ] Bottom 50 não tem nenhuma nota crítica acidentalmente

## Workflow Pós-Análise

1. **Top 50:** garantir frontmatter completo, links bidirecionais, atualização <90 dias
2. **Bottom 50:** revisar manualmente. Candidatos a:
   - ARCHIVE (`~/cortex/archive/`) se contexto morto
   - LINK (adicionar referências para conectar ao grafo)
   - DELETE (apenas se duplicata clara)

## Integração

- Roda via cron mensal: `0 3 1 * * python3 ~/cortex/scripts/cortex_pagerank.py`
- Resultado vira input para @heuristic-curator
- Top scores influenciam ordem de injeção do CORTEX hook (notas load-bearing primeiro)

## Heurísticas

- H1: Nota com score >0.01 NUNCA deletar sem revisar (load-bearing)
- H2: Nota com inlinks=0 E access=0 E age>180d = candidata forte a archive
- H3: Embeddings ONNX local (384d) são gratuitos — usar para detectar similaridade semântica entre orphans

## Multi-LLM
| Sub-tarefa | Modelo |
|------------|--------|
| Computar PageRank | Python puro (NumPy) — $0 |
| Embeddings de notas órfãs | ONNX local 384d — $0 |
| Decisão archive vs delete | Sonnet (envio só metadata) |
| Relatório executivo | Sonnet |

Origem: ruflo agent-pagerank-analyzer + sublinear-time-solver patterns.
