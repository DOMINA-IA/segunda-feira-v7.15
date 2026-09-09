---
name: proactive-leads
description: "Monitora o pipeline de leads no CRM do CLIENTE_EXEMPLO — identifica leads sem follow-up (>24h), sequências WhatsApp falhadas/pausadas e picos ou quedas de volume, sugere ações de nutrição e notifica via Telegram quando há leads precisando de atenção. Roda via cron a cada 1h (08h-22h) — não é auto-invocada pelo modelo, usar /proactive-leads para rodar manualmente."
disable-model-invocation: true
---

# /proactive-leads — Monitoramento de Pipeline de Leads

## Objetivo

Verificar o pipeline de leads no CRM do CLIENTE_EXEMPLO, identificar leads sem follow-up (mais de 24h), verificar sequências WhatsApp pendentes, sugerir ações de nutrição e notificar via Telegram quando houver leads precisando de atenção.

---

## Fontes de Dados

| Fonte | Acesso |
|-------|--------|
| CRM CLIENTE_EXEMPLO DB | SSH → VPS ${VPS_HOST} → `/opt/CLIENTE_EXEMPLO/` |
| CLIENTE_EXEMPLO API | https://seudominio.com.br/api/ |
| WhatsApp Bot | VPS porta 3003 |

### Regras de Leads (memória)

- **Nutrição e vendas via WhatsApp**, NÃO email marketing
- CRM tem pipeline kanban com estágios definidos
- Sequências WhatsApp automatizadas no CLIENTE_EXEMPLO
- Follow-up máximo aceitável: 24h após entrada

---

## Execução — Passo a Passo

### 1. Consultar Pipeline de Leads

Conectar via SSH na VPS e consultar o CRM:

```bash
ssh -o StrictHostKeyChecking=no root@${VPS_HOST} << 'REMOTE'
cd /opt/CLIENTE_EXEMPLO
node -e "
const db = require('./src/database');

// Leads novos (últimas 48h)
db.query('SELECT * FROM contacts WHERE created_at >= datetime(\"now\", \"-48 hours\") ORDER BY created_at DESC');

// Leads sem follow-up (criados há mais de 24h, sem interação)
db.query('SELECT c.* FROM contacts c LEFT JOIN interactions i ON c.id = i.contact_id WHERE c.created_at <= datetime(\"now\", \"-24 hours\") AND i.id IS NULL');

// Leads em cada estágio do pipeline
db.query('SELECT pipeline_stage, COUNT(*) as total FROM contacts WHERE pipeline_stage IS NOT NULL GROUP BY pipeline_stage');

// Sequências WhatsApp pendentes
db.query('SELECT * FROM sequences WHERE status = \"pending\" OR status = \"paused\" ORDER BY next_send_at');

// Leads com sequência falhada
db.query('SELECT * FROM sequences WHERE status = \"failed\" ORDER BY updated_at DESC LIMIT 20');
"
REMOTE
```

### 2. Analisar Pipeline

| Verificação | Critério | Classificação |
|-------------|----------|---------------|
| Lead sem follow-up | > 24h sem interação | CRÍTICO |
| Lead sem follow-up | 12-24h sem interação | ATENÇÃO |
| Sequência falhada | Envio WhatsApp falhou | ATENÇÃO |
| Sequência pausada | Precisa de ação manual | ATENÇÃO |
| Pipeline estagnado | Leads parados > 3 dias no mesmo estágio | ATENÇÃO |
| Volume anômalo | 2x mais leads que média diária | INFO (positivo) |
| Volume anômalo | 50% menos leads que média | ATENÇÃO |

### 3. Verificar WhatsApp Bot

Verificar se o bot está ativo e processando:

```bash
ssh -o StrictHostKeyChecking=no root@${VPS_HOST} << 'REMOTE'
# Status do WhatsApp Bot
pm2 describe whatsapp-bot 2>/dev/null | grep status
# Mensagens enviadas nas últimas 24h
cd /opt/CLIENTE_EXEMPLO
node -e "
const db = require('./src/database');
db.query('SELECT COUNT(*) as total FROM whatsapp_messages WHERE sent_at >= datetime(\"now\", \"-24 hours\") AND direction = \"outbound\"');
db.query('SELECT COUNT(*) as total FROM whatsapp_messages WHERE sent_at >= datetime(\"now\", \"-24 hours\") AND direction = \"inbound\"');
"
REMOTE
```

### 4. Gerar Recomendações

| Situação | Ação Recomendada |
|----------|-----------------|
| Lead novo sem follow-up > 24h | Enviar mensagem de boas-vindas URGENTE |
| Lead quente (interagiu recentemente) sem próximo passo | Agendar call/demo |
| Sequência falhou | Verificar número WhatsApp + reenviar manualmente |
| Pipeline estagnado | Mover para estágio adequado ou qualificar |
| Pico de leads | Verificar fonte (campanha nova?) + priorizar qualificação |
| Lead frio (sem interação > 7 dias) | Reativar com conteúdo de valor ou mover para nurturing |

### 5. Registrar Observações

Atualizar `~/framework/observations/leads-pipeline.md`:

```markdown
# Leads Pipeline — Última verificação

**Timestamp:** YYYY-MM-DD HH:MM:SS
**Estado Geral:** SAUDÁVEL | ATENÇÃO | CRÍTICO
**Leads novos (24h):** XX
**Leads sem follow-up:** XX
**Sequências ativas:** XX
**Sequências com problema:** XX

## Pipeline Summary

| Estágio | Quantidade | Variação |
|---------|-----------|----------|
| Novo | XX | +X/-X |
| Qualificado | XX | +X/-X |
| Em Negociação | XX | +X/-X |
| Fechado/Ganho | XX | +X/-X |
| Perdido | XX | +X/-X |

## Leads Precisando de Atenção

| Lead | Telefone | Estágio | Sem Follow-up | Prioridade |
|------|----------|---------|---------------|------------|
| Nome | +55... | Novo | 36h | ALTA |

## Sequências WhatsApp

| Sequência | Leads Ativos | Status | Problema |
|-----------|-------------|--------|----------|
| Boas-vindas | XX | Ativa | — |
| Nutrição 7d | XX | Ativa | — |
| Reativação | XX | Pausada | Verificar |

## Recomendações

| Ação | Leads Afetados | Prioridade |
|------|---------------|------------|
| Follow-up urgente | XX | ALTA |
| Reativar sequência | XX | MÉDIA |
| Qualificar leads parados | XX | MÉDIA |

## Histórico

| Data | Leads Novos | Sem Follow-up | Estado |
|------|------------|---------------|--------|
| DD/MM HH:MM | XX | XX | OK |
```

### 6. Notificar se Necessário

**Notificar via Telegram se:**
- Leads sem follow-up > 24h (quantidade > 0)
- Sequência WhatsApp falhada ou pausada
- WhatsApp Bot offline
- Pico incomum de leads (oportunidade)
- Pipeline sem movimentação > 48h

**Formato:**

```
👥 PIPELINE DE LEADS — [SAUDÁVEL/ATENÇÃO/CRÍTICO]

⏰ [timestamp]
📥 Leads novos (24h): XX
⚠️ Sem follow-up: XX

🔴 Urgente:
• XX leads há mais de 24h sem contato
• Sequência [nome] com falha em XX leads

📊 Pipeline:
• Novos: XX | Qualificados: XX | Negociação: XX

📋 Ações recomendadas:
• Follow-up urgente em XX leads
• Verificar sequência [nome]
• Qualificar XX leads parados

📊 Detalhes: ~/framework/observations/leads-pipeline.md
```

**Se pipeline saudável:** Apenas registrar, sem notificação.

---

## Parâmetros

| Parâmetro | Descrição | Default |
|-----------|-----------|---------|
| --chat-id | Chat ID Telegram | (obrigatório 1ª vez) |
| --followup-threshold | Horas sem follow-up para alertar | 24 |
| --force-notify | Notificar mesmo se saudável | false |

---

## Frequência Recomendada

- **Cron:** A cada 1 hora (08:00 - 22:00)
- **Trigger:** `proactive-leads`
- **Horário crítico:** 09:00 (início do dia) e 17:00 (antes do fim)

---

## Dependências

- Acesso SSH à VPS CLIENTE_EXEMPLO (CRM DB)
- WhatsApp Bot ativo (porta 3003)
- MCP Telegram ativo
- Diretório `~/framework/observations/` existente
- Regras de leads em memória (`crm-CLIENTE_EXEMPLO.md`, `feedback_whatsapp_over_email.md`)
