---
name: feed-quick
description: Atalho rápido para registrar resultado no feedback loop. Wrapper de feed-results.sh
  sem fricção sintática.
---

# /feed-quick — Registro Rápido no Feedback Loop

Wrapper para `~/framework/scripts/feed-results.sh` que aceita registro em frase única, sem precisar lembrar argumentos exatos.

## Uso

```
/feed-quick {categoria} {descrição livre}
```

## Categorias

| Categoria | Quando usar | Exemplo |
|-----------|-------------|---------|
| `campaign` | Resultado de campanha Meta Ads | `/feed-quick campaign "AI FIRST V3 — CPL R$8,40 R$200/dia ROAS 4.2"` |
| `content` | Performance de post/Reel/carrossel | `/feed-quick content "Reel hook 'Você está pagando 5x' — 18% reach, 240 saves"` |
| `whatsapp` | Taxa de broadcast/conversão | `/feed-quick whatsapp "Lista quente — 47% open, 12 responderam"` |
| `sales` | Venda fechada | `/feed-quick sales "Pacote IA R$ X.XXX — origem WhatsApp via Israel"` |
| `offers` | Mudança de oferta/preço | `/feed-quick offers "Mentoria 12x R$497 → 12x R$597 + bônus Workshop"` |
| `summary` | Resumo executivo do dia/semana | `/feed-quick summary "Semana 18 — 3 vendas, R$ X.XXX, CPL médio R$15"` |

## Comportamento

1. Parse categoria + descrição
2. Invocar `bash ~/framework/scripts/feed-results.sh {categoria} --note "{descrição}" --date $(date +%Y-%m-%d)`
3. Validar que `~/feedback-loop/results.json` recebeu update (mtime atualizado)
4. Emitir sinal `result_logged` no broadcast (silencioso, não notifica)
5. Confirmar ao CEO em 1 linha: `✓ Registrado em feedback-loop:{categoria}`

## Quando o agente DEVE sugerir o uso

Após qualquer interação que gere resultado mensurável:
- Análise de campanha completa → sugerir `/feed-quick campaign`
- Post agendado e publicado → sugerir `/feed-quick content`
- Conversa de venda fechada → sugerir `/feed-quick sales`

## Por que existe

`feed-results.sh` original tem CLI verbosa que cria fricção. `/feed-quick` reduz registro para 1 frase, aumentando hábito de alimentar o feedback-loop.

Resolve o problema operacional identificado em 04-Mai-2026: feedback-loop estava 119h sem update porque sintaxe original era barreira psicológica.
