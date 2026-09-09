---
id: mastra-arquitetura-geral-ultralearn-2026-05-24
title: Mastra — Arquitetura Geral (ultralearn 2026-05-24)
type: meta
status: active
created: '2026-05-24'
last_verified: '2026-05-24'
domain:
- framework
agents:
- sf-master
- architect
tags:
- mastra
- typescript
- multi-llm
- a2a
- framework
- research
decay_rate: 0.01
links:
- target: mastra-modelbyinputtokens-roteamento-por-tier-de-tokens
  type: auto-linked
- target: mastra-a2a-protocol-contratos-de-capacidade-inter-agente
  type: auto-linked
- target: mastra-evals-sistema-avaliacao-agentes
  type: auto-linked
- target: segunda-feira-upgrade-multi-ia-orchestrator-2026-05-22
  type: related
- target: inema-delta-2026-05-22-orchestrator-multi-ia
  type: related
---

# Mastra — Arquitetura Geral (ultralearn 2026-05-24)

# Mastra — Framework TypeScript (YC W25)

## Identidade
- **GitHub:** mastra-ai/mastra | 22k+ stars | Apache 2.0
- **Stack:** TypeScript (monorepo pnpm/turbo), 9247 arquivos, 210MB
- **Posicionamento:** Framework TypeScript para apps AI — agentes, workflows, memória, MCP
- **Relevância para SF:** 27/40 no benchmarking. 5/5 em Multi-LLM. Padrões absorvíveis.

## Subsistemas Identificados (packages/)
| Subsistema | Localização | Relevância |
|-----------|-------------|------------|
| Core (agentes, workflows, harness) | packages/core/ | ALTA |
| Memory + Observational Memory | packages/memory/ | MUITO ALTA — equivale ao Consciousness Engine |
| RAG | packages/rag/ | MÉDIA |
| Evals (avaliação de qualidade) | packages/evals/ | ALTA — equivale ao EROS |
| MCP servers | packages/mcp/ | MÉDIA |
| Auth + RBAC | packages/auth/ | ALTA — análogo à authority matrix |
| Stores (25+ backends) | stores/ | BAIXA para SF single-tenant |
| Workflows Temporal/Inngest | workflows/ | MÉDIA |
| A2A | packages/core/src/a2a/ | ALTA — protocolo inter-agente padronizado |

## Stores disponíveis (25+)
pg, libsql, mongodb, redis, elasticsearch, pinecone, chroma, qdrant, lance, s3vectors, upstash, cloudflare, convex, dynamodb, duckdb, mssql — ampla base de storage para projetos cliente.

## Stack de LLMs
Suporte via ai-sdk-v4, ai-sdk-v5, ai-v6 — provedor-agnóstico. 81 providers via Vercel AI SDK. ModelByInputTokens faz roteamento por tier de token.

## Referência
Clonado em: ~/clientes/_research/mastra/ (depth 1, 2026-05-24)