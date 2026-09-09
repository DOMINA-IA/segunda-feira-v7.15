---
name: user-model
description: "Modelo vivo do CEO ${CEO_NAME} (estilo cognitivo, contexto de negócio, relacionamentos, log evolutivo) em ~/cortex/vault/user-model/. Use ANTES de perguntar algo já modelado, de recomendação grande ou de propor mudança em cliente. NOT for: dados…"
axis: meta
harnesses:
  claude-code: full
  codex: native
  cursor: limited
  aider: limited
model-routing:
  primary: local-heuristic-tier0
  optional-llm: anthropic/claude-haiku-4-5
---

# /user-model — Modelo Dialético do CEO

## Quando usar
- **Sempre que agente precisar entender** preferências/contexto do CEO (consulte ANTES de perguntar)
- Antes de fazer recomendação grande (cross-check com `cognitive-style`)
- Antes de propor mudança em cliente (cross-check com `business-context`)
- Para entender quem é quem (`relationship-graph`)
- Mensalmente para ver evolução (`evolutive-log`)

## Como funciona

Adaptação SF do conceito Honcho (NousResearch hermes-agent). SEM dependência de serviço externo — implementação 100% local em markdown + Python.

### Dialética em prática

| Fase | Onde mora |
|------|-----------|
| **TESE** (o que sei agora) | `cognitive-style.md` + `business-context.md` + `relationship-graph.md` |
| **ANTÍTESE** (sinais novos) | Episódios das últimas 14 dias + mailbox + signals |
| **SÍNTESE** (mudança preservada) | `evolutive-log.md` (append-only) |

### 4 arquivos do modelo

| Arquivo | O que contém |
|---------|--------------|
| `cognitive-style.md` | Como CEO decide, comunica e pensa |
| `business-context.md` | Estado DOMINA + clientes + métricas snapshot |
| `relationship-graph.md` | Squad SF + stakeholders externos + autoridades |
| `evolutive-log.md` | Append-only de mudanças qualitativas detectadas |

## Operações

### Consultar (todo agente DEVE fazer)
```bash
cat ~/cortex/vault/user-model/cognitive-style.md      # como ele decide
cat ~/cortex/vault/user-model/business-context.md     # estado negócio
cat ~/cortex/vault/user-model/relationship-graph.md   # quem é quem
cat ~/cortex/vault/user-model/evolutive-log.md        # mudanças recentes
```

### Atualizar (automático ou manual)
```bash
# Dry-run (vê sinais sem modificar)
python3 ~/cortex/scripts/user_model_updater.py --days 14 --dry-run

# Atualização real (só escreve se houver mudança qualitativa)
python3 ~/cortex/scripts/user_model_updater.py --days 14

# Forçar update mesmo sem mudança (debug)
python3 ~/cortex/scripts/user_model_updater.py --days 14 --force

# JSON estruturado
python3 ~/cortex/scripts/user_model_updater.py --days 30 --json
```

## Critério de mudança qualitativa

Updater só adiciona entry se detectar:
- ≥1 decisão CEO referenciada nos episódios
- OU ≥2 atualizações de cliente
- OU ≥1 preferência revelada (anti-padrão, regra de ouro, etc)
- OU ≥2 mudanças estratégicas (versão bump, sprint complete, absorção)

Caso contrário: modelo é considerado ESTÁVEL e nada é escrito.

## Como agentes devem usar

### Antes de perguntar ao CEO
```
1. Consultar user-model
2. Se resposta está lá → use sem perguntar
3. Se contradiz seu plano → ajustar plano OU sinalizar contradição
4. Se ausente → perguntar (e a resposta deve atualizar o modelo)
```

### Em briefings
Briefings dos agentes devem incluir referências aos 4 arquivos no `cortex-auto.py` hook (futuro: adicionar injection automática quando keywords detectadas).

## Heurísticas

- **H1:** Modelo estável (0 changes em 14 dias) = bom. Não force entries.
- **H2:** Entry com 0 "decisões CEO" mas muitas "client updates" = mudança operacional, não estratégica.
- **H3:** Top agents da janela revela ONDE o CEO investiu tempo (sinal de prioridade).
- **H4:** Valência média alta (>0.6) = sessões positivas; baixa (<0.3) = atrito/retrabalho.

## Multi-LLM

| Operação | Tier |
|----------|------|
| Detecção de padrões via regex | Tier 0 (local Python) — $0 |
| Append entry ao log | Tier 0 — $0 |
| Síntese refinada (--llm flag) | Tier 1 (Haiku) — ~$0.01 |
| Re-escrita dos 3 arquivos canon | Tier 2 (Sonnet) — ~$0.05 por arquivo |

Default: 100% Tier 0. Custo ~$0 por execução, ~3s em 200 episódios.

## Cron sugerido

```cron
# User model update mensal (1º dia 02h BRT)
0 2 1 * * cd ~ && /usr/bin/python3 ~/cortex/scripts/user_model_updater.py --days 30 >> ~/logs/user-model.log 2>&1
```

Já instalado (verificar com `crontab -l | grep user_model`).

## Diferença vs MEMORY.md

| Sistema | Onde | O que captura |
|---------|------|---------------|
| `MEMORY.md` (auto-memory) | `~/.claude/projects/.../memory/` | Pontos discretos memoráveis (decisões logbook) |
| `user-model/` (este) | `~/cortex/vault/user-model/` | Modelo VIVO de quem o CEO é (evolui dialeticamente) |

**Complementares**, não redundantes. MEMORY.md responde "o que sei?". user-model responde "como ele pensa?".

## Origem

Conceito **Honcho dialectic user modeling** (Plastic Labs, integrado ao hermes-agent via memory_provider plugin). Hermes pluga em serviço FastAPI externo. SF implementa essência sem dependência externa — markdown + Python heurístico + flag LLM opcional. Trade-off: menos sofisticado (sem embeddings sobre dialogue history), mas auto-contido e $0.

Sources:
- [hermes-agent hermes_cli/memory_setup.py](https://github.com/NousResearch/hermes-agent/blob/main/hermes_cli/memory_setup.py)
- Honcho: https://honcho.dev (referência conceitual, não usada)
