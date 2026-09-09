---
id: axis-separation-full
title: Axis Separation (completo)
type: rule
domain:
- meta
triggers:
- axis
- meta vs ops
- eixo
- separação de eixo
- separacao de eixo
- conformidade axis
links:
- target: heuristic-architect-quando-cliente-entrega-prompt-de-agente-como-pedido-trata
  type: auto-linked
- target: credentials-handling-full
  type: auto-linked
- target: visual-rendering-safety
  type: auto-linked
- target: multi-ia-portability
  type: auto-linked
- target: cross-collaboration-mandate
  type: auto-linked
- target: eros-quality-full
  type: auto-linked
---

# Axis Separation — Eixos META vs OPS

> **Severidade:** MUST | **Aplica-se a:** Todos os agentes
> **Origem:** Decisão arquitetural CEO em 22-Mai-2026, após detectar mistura de escopos no relatório final do deploy VPS Fase A.

## Princípio

Todo trabalho no framework Segunda-feira pertence a **um de dois eixos mutuamente exclusivos**:

| Eixo | Pergunta que responde | Quem produz |
|------|----------------------|-------------|
| **META** 📐 | "Como o sistema funciona?" | @sf-master, @architect, @dev, @devops, @people-ops, @qa, @pm, @po, @sm, @advogado-do-diabo, @security-auditor, @prompt-engineer, @vibe-coder, @rag-architect, @automation-architect, @knowledge-builder, @cost-optimizer, @swarm-simulator, @tool-curator, @inema-scout, @workflow-orchestrator, @mestre-do-conselho, @fabio-soares |
| **OPS** 🎯 | "O que o sistema produz para o mercado?" | @traffic, @content, @copywriter, @creative-director, @video-producer, @offer-engineer, @launch-strategist, @challenge-funnel, @market-intel, @cro-specialist, @growth-hacker, @cold-outreach, @whatsapp-specialist, @voice-ai-specialist, @analyst, @contract-analyst, @closer, @ux-design-expert, @sdr, @sales, @cs, @cs-retention, @collector |

**Regra de ouro:** "Se a entrega vai para o MERCADO (campanha, conteúdo, oferta, KPI de negócio), é OPS. Se a entrega vai para o SISTEMA (rule, infra, agente, hook, governança), é META."

---

## O que pertence a cada eixo

### META — sistema, framework, governança

- Rules constitucionais (`~/.claude/rules/`)
- Infraestrutura (VPS, deploys, systemd, hooks, mailbox)
- Engenharia do framework (refactor de scripts, IDS audit, heurísticas técnicas)
- Auditoria interna e governance (autoridade, qualidade EROS, cross-project protocol)
- Knowledge management (CORTEX, consciousness, briefings, sinais)
- Curadoria de ferramentas (tool-curator, inema-scout, cost-optimizer)
- Notas com `type ∈ {rule, infra, meta, architecture, agent}`
- Heurísticas de @dev/@devops/@sf-master/@architect/@security-auditor

### OPS — operação, produção, mercado

- Campanhas Meta Ads, ângulos, criativos, ofertas
- Conteúdo Instagram (posts, Reels, carrosséis, copy)
- Funis de venda, LPs, CRO, tracking, eventos, lançamentos
- KPIs de negócio: CPL, ROAS, conversão, ticket médio, receita
- Operação de clientes (CLIENTE_EXEMPLO, CLIENTE_EXEMPLO_2, CLIENTE_EXEMPLO, CLIENTE_EXEMPLO, CLIENTE_EXEMPLO, Dominantes)
- WhatsApp Bot operacional, automações de vendas
- Notas com `type ∈ {project, playbook (campanha/conteúdo/oferta), feedback (campanha)}`
- Heurísticas de @traffic/@content/@copywriter/@offer-engineer

### Caso especial: agentes que operam em ambos

| Agente | Eixo principal | Quando vai pro outro |
|--------|---------------|---------------------|
| @dev | META | Builds em produto cliente são applied work, mas o ofício técnico permanece META |
| @analyst | OPS | Análise de framework usage (token economy, heurísticas) é META |
| @architect | META | Decisões de arquitetura de produto cliente seguem regra de processo |
| @devops | META | Deploy de feature cliente é applied work; governança continua META |

Notas geradas por esses agentes herdam o eixo do **artefato produzido**, não do agente.

---

## Marcação obrigatória

### Em notas CORTEX

Todo frontmatter DEVE conter `axis: meta` ou `axis: ops`:

```yaml
---
id: minha-nota
type: pattern
axis: meta
---
```

O `cortex_engine.py build-index` valida presença do campo. Notas sem `axis` ficam em modo legacy (tratadas como META por default conservador) mas aparecem em report de health como pendentes.

### Em agentes

Arquivos em `~/.claude/agents/meta/` ou `~/.claude/agents/ops/`. Symlinks de retrocompat em `~/.claude/agents/<name>.md` para Agent tool legacy.

### Em briefings

Auto-gerados em `~/cortex/briefings/meta/` ou `~/cortex/briefings/ops/` pelo `build_all_briefings()`.

### Em crons VPS (futuro)

Systemd units com prefixo:
- `sf-meta-<task>.timer` (consolidate, build-briefings, signal-router, mailbox-ttl, cortex-sync)
- `sf-ops-<task>.timer` (cost-watchdog, daily-digest, daily-scan, meta-smoke, notifications)

### Em CORTEX Alerts

Hook `router.py` (`$HOME/brain/thalamus/router.py`) deve prefixar alertas:
- `[META]` para framework, infra, hooks, audit
- `[OPS]` para campanhas, leads, conversão, KPIs

---

## Por que esses dois eixos especificamente

A confusão original veio de tratar tudo no mesmo nível:
- CPL alto (problema de campanha — OPS) chegava junto com deploy fase A (problema de infra — META)
- @people-ops engagement (META) misturava com performance LPs (OPS)
- Mesma mailbox, mesmo briefing, mesmo CORTEX Alert

Os dois eixos têm **dinâmicas temporais diferentes**:
- META muda raramente (refator de framework é evento, não rotina)
- OPS muda toda semana (campanha, oferta, conteúdo)

Tratar os dois com a mesma cadência polui contexto e dilui foco. Separar permite:
- Daily standup OPS focado em CPL, leads, criativos
- Weekly review META focada em saúde framework, dormentes, heurísticas
- Cron schedules apropriados a cada
- Quem entra no contexto certo no momento certo

---

## Anti-Patterns

| Anti-Pattern | Correção |
|-------------|----------|
| Listar problema OPS (CPL alto) entre pendências META (deploy fase B) | Separar em duas listas |
| Criar nota CORTEX sem `axis:` | Sempre marcar no frontmatter |
| Briefing de @traffic falando de qualidade EROS no detalhe | EROS é META, vai no briefing de @sf-master |
| Daily digest misturar "saúde framework" e "leads do dia" | Dois reports separados |
| Squad OPS recebendo notificação de heurística @dev | Filtrar broadcast por axis |

---

## Integração com outras rules

| Rule | Como interage |
|------|---------------|
| `cortex-usage.md` | Queries CORTEX podem filtrar `--axis meta` ou `--axis ops` |
| `feedback-loop.md` | Loop OPS consulta apenas resultados OPS; loop META consulta heurísticas técnicas |
| `agent-communication.md` | Broadcast pode ter scope axis; mensagens OPS↔META precisam ser justificadas |
| `eros-quality.md` | EROS aplica a ambos eixos com mesmos portões, mas critérios diferentes |
| `consciousness-engine.md` | Episódios herdam axis do agente (META se sf-master, OPS se traffic) |

---

## Comando para verificar conformidade

```bash
# Listar notas sem axis
python3 ~/cortex/scripts/cortex_engine.py query "" --no-axis 2>/dev/null

# Health por eixo
ls ~/cortex/vault/_index_by_axis/meta/ | wc -l   # 621 esperado
ls ~/cortex/vault/_index_by_axis/ops/ | wc -l    # 243 esperado

# Briefings por eixo
ls ~/cortex/briefings/meta/ | wc -l   # 30
ls ~/cortex/briefings/ops/ | wc -l    # 19
```
