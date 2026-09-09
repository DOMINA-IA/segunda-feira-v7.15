---
name: feed-results
description: "Importa resultados reais de Meta Ads, Instagram e WhatsApp Bot para o feedback loop e atualiza os patterns validados automaticamente. Use quando houver dados novos de campanha/conteúdo para registrar — é a base de todo aprendizado dos agentes."
tools: ["Read", "Write", "Edit", "Bash", "WebFetch"]
harnesses:
  - claude-code: full
  - codex: native
  - cursor: limited
  - aider: limited
---

# /feed-results — Alimentar o Feedback Loop

> **Tipo:** Skill de coleta | **Agente padrão:** @analyst
> **Frequência:** Diária ou após cada campanha/lançamento
> **Output:** ~/feedback-loop/results.json atualizado + patterns extraídos

## Objetivo

Coletar resultados reais de todas as plataformas e alimentar o banco central de resultados que todos os agentes consultam antes de tomar decisões.

---

## Processo

### 1. Coleta de Dados

#### Meta Ads (se disponível via API ou manual)
Para cada campanha ativa/recente:
- Nome, ID, status
- CPL (custo por lead), CPA
- Leads gerados, spend total
- Ângulo do criativo usado
- Período

#### Instagram (se dados disponíveis)
Para cada post recente:
- Slug, formato (Reel/Carrossel/Post)
- Likes, saves, shares, comentários, alcance
- Ângulo/tema do conteúdo
- Data de publicação

#### WhatsApp Bot (se dados disponíveis)
- Mensagens enviadas, entregues, lidas, respondidas
- Taxa de conversão por sequência

### 2. Atualização do results.json
- Ler ~/feedback-loop/results.json
- Adicionar novos entries (sem duplicar — verificar por ID/slug)
- Atualizar entries existentes se houver dados mais recentes
- Salvar

### 3. Extração de Padrões
Após atualizar resultados, analisar automaticamente:

#### Ângulos
- Agrupar campanhas por creative_angle
- Calcular CPL médio por ângulo
- Identificar: campeões (CPL < média) e perdedores (CPL > 2x média)
- Atualizar ~/patterns/angles.md

#### Formatos
- Agrupar conteúdo por formato
- Calcular engajamento médio por formato
- Atualizar ~/patterns/formats.md

#### Ofertas
- Comparar taxas de conversão entre ofertas
- Atualizar ~/patterns/offers.md

### 4. Emissão de Sinais
Se padrão relevante detectado, emitir sinal em ~/broadcast/signals.json:
- CPL_DROP: ângulo com CPL abaixo da média
- CPL_SPIKE: campanha com CPL subindo
- ENGAGEMENT_SPIKE: conteúdo com performance excepcional

### 5. Output
Resumo em texto:
```
## Feed Results — [DATA]
- Campanhas atualizadas: X
- Posts atualizados: X
- Padrões novos: X
- Sinais emitidos: X
- Ângulo campeão atual: [nome] (CPL R$X.XX)
```

---

## Regras
- NUNCA inventar dados — só registrar o que foi coletado
- Manter histórico (nunca sobrescrever entries antigos, apenas adicionar novos)
- Confidence score obrigatório em padrões extraídos
- Se dados insuficientes (< 3 entries), marcar padrão como "preliminary"

---

## Atalho rápido (absorvido de feed-quick.md)

Para reduzir a fricção de lembrar os argumentos exatos do script, use registro em frase única por categoria:

| Categoria | Quando usar | Exemplo |
|-----------|-------------|---------|
| `campaign` | Resultado de campanha Meta Ads | `campaign "AI FIRST V3 — CPL R$8,40 R$200/dia ROAS 4.2"` |
| `content` | Performance de post/Reel/carrossel | `content "Reel hook 'Você está pagando 5x' — 18% reach, 240 saves"` |
| `whatsapp` | Taxa de broadcast/conversão | `whatsapp "Lista quente — 47% open, 12 responderam"` |
| `sales` | Venda fechada | `sales "Pacote IA R$ X.XXX — origem WhatsApp via Israel"` |
| ~~`offers`~~ (sem subcomando dedicado) | Mudança de oferta/preço | `campaign "Nova oferta: Mentoria 12x R$497 → 12x R$597 + bônus Workshop"` (nota livre dentro de `campaign` ou `summary` — ver nota de precisão abaixo) |
| `summary` | Resumo executivo do dia/semana | `summary "Semana 18 — 3 vendas, R$ X.XXX, CPL médio R$15"` |

O script real vive em `$HOME/framework/scripts/feed-results.sh` (subcomandos confirmados: `campaign`, `content`, `whatsapp`, `sales`, `summary`; cada um com suas próprias flags — ex. `--name`, `--spend`, `--leads`, `--cpl`, `--notes`). Rodar `bash $HOME/framework/scripts/feed-results.sh help` para ver a sintaxe completa por subcomando.

**Nota de precisão:** `offers` não é um subcomando gravável do script — hoje é apenas uma categoria exibida em `summary` (lida da estrutura de dados). Registrar mudança de oferta/preço como nota livre dentro de `campaign` ou `summary` até que um subcomando dedicado exista.

**Quando sugerir:** após qualquer interação que gere resultado mensurável — análise de campanha completa, post agendado e publicado, conversa de venda fechada — o agente deve sugerir rodar o atalho da categoria correspondente.

**Por que existe:** a CLI completa do script cria fricção. Resolve o problema operacional identificado em 04-Mai-2026: feedback-loop ficou 119h sem update porque a sintaxe original era barreira psicológica.
