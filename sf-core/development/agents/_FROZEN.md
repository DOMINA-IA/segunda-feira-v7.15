# ⚠️ CAMADA CONGELADA — NÃO EDITAR

> **Congelada em:** 2026-07-07 · **Decisão:** CEO, com base na auditoria multi-agente do framework
> **Plano de referência:** `~/framework/improvements/PLANO-MELHORIA-2026-07-07.md` (item 2.1 — Fonte única de agentes)

## Hierarquia de agentes vigente

| Camada | Papel | Editável? |
|---|---|---|
| `~/.claude/agents/{meta,ops}/` | **FONTE CANÔNICA** — lida pelo Agent tool do harness | ✅ SIM — edite aqui |
| `~/.claude/commands/segunda-feira/agents/` | Camada DERIVADA — sincronizada a partir da canônica (rodapé `DERIVADO` nos arquivos reconciliados) | ❌ NÃO — editar a fonte e re-sincronizar |
| `~/.sf-core/development/agents/` (este diretório) | **LEGADO CONGELADO** — histórico da era aios/BMAD | ❌ NÃO |

## Contexto

Auditoria de 2026-07-07 confirmou tripla definição divergente de @dev, @analyst e @video-producer
(diffs de 116-844 linhas entre camadas editadas em paralelo). A reconciliação semântica foi feita
em 2026-07-07 e o resultado gravado na fonte canônica.

- Backup completo pré-reconciliação: `~/framework/improvements/backups/agentes-20260707/`
- Agentes sem via de invocação (quick-flow, tech-writer, video-editor) arquivados em `~/.sf-core/_archive/agents-sem-invocacao-20260707/`
- **NUNCA re-rodar ide-sync a partir desta camada** — sobrescreveria a evolução manual das camadas vivas.
