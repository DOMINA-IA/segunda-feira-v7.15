---
name: proactive-monitor
description: "Monitora a saúde da infraestrutura (VPS CLIENTE_EXEMPLO, Hostinger, apps PM2, sites públicos) — disco, memória, load average, status de cada app e tempo de resposta dos sites — registra o estado e alerta via Telegram só em caso de ATENÇÃO/CRÍTICO ou recuperação. Roda via cron a cada 30min (06h-23h) — não é auto-invocada pelo modelo, usar /proactive-monitor para rodar manualmente."
disable-model-invocation: true
---

# /proactive-monitor — Monitoramento de Infraestrutura

## Objetivo

Verificar a saúde completa da infraestrutura (VPS CLIENTE_EXEMPLO, Hostinger, apps PM2, sites públicos), registrar o estado em `~/framework/observations/server-health.md` e notificar via Telegram apenas se houver problemas.

---

## Infraestrutura Monitorada

| Recurso | Host | Porta SSH | Usuário | Senha |
|---------|------|-----------|---------|-------|
| VPS CLIENTE_EXEMPLO | ${VPS_HOST} | 22 | root | chave SSH (`ssh CLIENTE_EXEMPLO`) |
| Hostinger | ${VPS_HOST} | 65002 | — | (ver ~/.claude/projects/) |

### Apps PM2 na VPS CLIENTE_EXEMPLO

| App | Porta | Endpoint |
|-----|-------|----------|
| CLIENTE_EXEMPLO | 3001 | https://seudominio.com.br |
| CLIENTE_EXEMPLO-dashboard | 3002 | https://seudominio.com.br |
| whatsapp-bot | 3003 | — |
| domina-ia | 3004 | — |

### Sites na Hostinger

| Site | URL |
|------|-----|
| LP Principal | https://seudominio.com.br |
| Desafio MI | https://seudominio.com.br |
| CLIENTE_EXEMPLO_4 | https://seudominio.com.br |
| CLIENTE_EXEMPLO | https://seudominio.com.br |

---

## Execução — Passo a Passo

### 1. Verificar VPS CLIENTE_EXEMPLO via SSH

Conectar via Bash (SSH) na VPS e executar os comandos abaixo. Usar `sshpass` ou `expect` conforme disponível:

```bash
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@${VPS_HOST} << 'REMOTE'
echo "===PM2_STATUS==="
pm2 jlist 2>/dev/null || echo "PM2_UNAVAILABLE"
echo "===DISK==="
df -h / /opt 2>/dev/null
echo "===MEMORY==="
free -m
echo "===UPTIME==="
uptime
echo "===DOCKER==="
docker ps --format "{{.Names}} {{.Status}}" 2>/dev/null || echo "NO_DOCKER"
REMOTE
```

**Interpretar resultados:**

| Métrica | OK | ATENÇÃO | CRÍTICO |
|---------|-----|---------|---------|
| Disco (/) | < 70% | 70-85% | > 85% |
| Memória | < 70% | 70-85% | > 85% |
| PM2 app status | online | stopping/errored (< 5 restarts) | errored (> 5 restarts) |
| Load average (1min) | < 2.0 | 2.0-4.0 | > 4.0 |

### 2. Verificar Sites Respondendo

Para cada URL monitorada, executar curl e verificar HTTP status:

```bash
curl -s -o /dev/null -w "%{http_code} %{time_total}" --connect-timeout 10 --max-time 30 <URL>
```

**Interpretar resultados:**

| HTTP Code | Tempo | Classificação |
|-----------|-------|---------------|
| 200/301/302 | < 3s | OK |
| 200/301/302 | 3-10s | ATENÇÃO (lento) |
| 200/301/302 | > 10s | CRÍTICO (muito lento) |
| 4xx/5xx | — | CRÍTICO |
| Timeout/erro | — | CRÍTICO |

### 3. Verificar Hostinger via SSH

```bash
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -p ${SSH_PORT} <user>@${VPS_HOST} << 'REMOTE'
echo "===DISK==="
df -h / /home
echo "===MEMORY==="
free -m 2>/dev/null || echo "SHARED_HOSTING"
REMOTE
```

Se SSH falhar (hosting compartilhado), verificar apenas via curl nos sites.

### 4. Comparar com Estado Anterior

Ler `~/framework/observations/server-health.md` (se existir) e comparar:
- Algum serviço que estava OK agora está com problema? → DEGRADAÇÃO
- Algum problema que existia foi resolvido? → RECUPERAÇÃO
- Disco/memória crescendo consistentemente? → TENDÊNCIA

### 5. Classificar Estado Geral

```
CRÍTICO — Qualquer serviço down, disco > 85%, memória > 85%, site não responde
ATENÇÃO — Alguma métrica entre 70-85%, site lento, PM2 com restarts
OK      — Tudo dentro dos limites normais
```

### 6. Registrar Observações

Atualizar `~/framework/observations/server-health.md` com o formato:

```markdown
# Server Health — Última verificação

**Timestamp:** YYYY-MM-DD HH:MM:SS
**Estado Geral:** OK | ATENÇÃO | CRÍTICO

## VPS CLIENTE_EXEMPLO (${VPS_HOST})

| Métrica | Valor | Status |
|---------|-------|--------|
| Disco (/) | XX% | OK/ATENÇÃO/CRÍTICO |
| Memória | XX% | OK/ATENÇÃO/CRÍTICO |
| Load Avg | X.XX | OK/ATENÇÃO/CRÍTICO |
| PM2 apps | X/X online | OK/ATENÇÃO/CRÍTICO |

### PM2 Apps

| App | Status | Restarts | Uptime |
|-----|--------|----------|--------|
| CLIENTE_EXEMPLO | online | 0 | Xd Xh |
| CLIENTE_EXEMPLO-dashboard | online | 0 | Xd Xh |
| whatsapp-bot | online | 0 | Xd Xh |
| domina-ia | online | 0 | Xd Xh |

## Sites

| Site | HTTP | Tempo | Status |
|------|------|-------|--------|
| seudominio.com.br | 200 | 0.5s | OK |
| seudominio.com.br | 200 | 0.8s | OK |
| seudominio.com.br | 200 | 0.3s | OK |
| seudominio.com.br | 200 | 0.4s | OK |
| seudominio.com.br | 200 | 0.3s | OK |
| seudominio.com.br | 200 | 0.5s | OK |

## Histórico (últimas 10 verificações)

| Data | Estado | Observações |
|------|--------|-------------|
| YYYY-MM-DD HH:MM | OK | Tudo normal |
```

### 7. Notificar se Necessário

**Se estado = ATENÇÃO ou CRÍTICO:**

Usar MCP Telegram (`mcp__plugin_telegram_telegram__reply`) para enviar alerta formatado:

```
🔴 ALERTA INFRAESTRUTURA — [CRÍTICO/ATENÇÃO]

⏰ [timestamp]

Problemas encontrados:
• [descrição problema 1]
• [descrição problema 2]

Ação recomendada:
• [sugestão 1]
• [sugestão 2]

📊 Detalhes completos em ~/framework/observations/server-health.md
```

**Se estado = OK:**
- Apenas registrar em `~/framework/observations/server-health.md`
- NÃO notificar via Telegram (evitar spam)

**Exceção — Recuperação:**
Se o estado anterior era CRÍTICO/ATENÇÃO e agora é OK, notificar:

```
✅ RECUPERAÇÃO — Infraestrutura normalizada

⏰ [timestamp]

Resolvido:
• [o que voltou ao normal]
```

---

## Parâmetros

| Parâmetro | Descrição | Default |
|-----------|-----------|---------|
| --chat-id | Chat ID do Telegram para notificações | (obrigatório na 1ª execução, salvo em config) |
| --force-notify | Notificar mesmo se tudo OK | false |
| --skip-ssh | Pular verificação SSH (só curl) | false |
| --verbose | Mostrar detalhes da execução | false |

---

## Frequência Recomendada

- **Cron:** A cada 30 minutos
- **Trigger:** `proactive-monitor`
- **Horário ativo:** 06:00 - 23:00 (não acordar de madrugada)

---

## Dependências

- Acesso SSH à VPS (senha em memória)
- MCP Telegram configurado e ativo
- Diretório `~/framework/observations/` existente
