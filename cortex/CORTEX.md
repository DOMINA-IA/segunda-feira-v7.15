# CORTEX — O Cérebro do Segunda-feira

> Knowledge Management System AI-Native | v1.0

## O Que é

CORTEX é o sistema de conhecimento do framework Segunda-feira. Diferente de arquivos flat ou ferramentas como Obsidian, o CORTEX foi projetado para **agentes de IA** — otimizado para tokens, queries programáticas, e auto-curadoria.

## Princípios

1. **Retrieval > Storage** — não carregue tudo, busque o que precisa
2. **Freshness > Completeness** — dado atualizado vale mais que dado completo
3. **Agent-scoped > Global** — cada agente recebe só o relevante
4. **Links tipados > Links flat** — saber COMO se relaciona, não só QUE se relaciona
5. **Auto-curadoria** — o vault se limpa, alerta e consolida sozinho

## Estrutura

```
~/cortex/
  vault/          → Conhecimento (notas markdown com frontmatter)
  index/          → Índices computados (graph, tags, search, freshness)
  briefings/      → Resumos pré-computados por agente
  scripts/        → CLI do CORTEX
  templates/      → Templates de nota por tipo
```

## Uso Rápido

```bash
# Buscar conhecimento
~/cortex/scripts/query.sh "CPL campanha CLIENTE_EXEMPLO"

# Adicionar nota
~/cortex/scripts/ingest.sh --title "Nova campanha X" --type project --domain traffic

# Criar link entre notas
~/cortex/scripts/link.sh source_id target_id depends_on

# Verificar saúde do vault
~/cortex/scripts/health-check.sh

# Reconstruir índices
~/cortex/scripts/build-index.sh

# Gerar briefings dos agentes
~/cortex/scripts/build-briefings.sh

# Marcar nota como verificada
~/cortex/scripts/refresh.sh note_id

# Migrar memórias atuais
~/cortex/scripts/migrate.sh
```

## Formato de Nota

Toda nota CORTEX tem frontmatter YAML + corpo markdown. Ver `templates/` para exemplos.

## Tipos de Link

| Tipo | Significado |
|------|------------|
| `depends_on` | Preciso saber isso primeiro |
| `extends` | Expande/aprofunda esse conhecimento |
| `supersedes` | Substituiu essa nota (nota antiga = deprecated) |
| `contradicts` | Aprendizado oposto — precisa resolução |
| `instance_of` | Caso específico de um padrão geral |
| `learned_from` | Extraído desse feedback/resultado |
| `related` | Relacionado genericamente |

## Decay Rates por Tipo

| Tipo de nota | Decay/semana | Justificativa |
|-------------|-------------|---------------|
| infra | 0.15 | Portas, IPs, configs mudam frequentemente |
| project (active) | 0.05 | Projetos ativos são acompanhados |
| project (paused) | 0.10 | Podem ter mudado sem acompanhamento |
| pattern | 0.03 | Padrões validados duram mais |
| playbook | 0.02 | Conhecimento conceitual é estável |
| rule | 0.01 | Regras mudam raramente |
| feedback | 0.08 | Resultados perdem relevância com o tempo |

## Integração

- **Consciousness Engine**: episódios alimentam CORTEX via `learned_from`
- **Feedback Loop**: results.json sincroniza com `vault/feedback/`
- **Nervous System**: health-check emite sinais de alerta
- **CLAUDE.md**: aponta para CORTEX ao invés de carregar tudo

---
*CORTEX v1.0 — Segunda-feira Framework*
