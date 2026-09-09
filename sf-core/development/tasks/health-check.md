## Task Definition (AIOS Task Format V1.0)

```yaml
task: healthCheck()
responsável: Sentinel (Guardian)
responsavel_type: Agente
trigger: '*health-check'
elicit: false
mode: autonomous
```

## Purpose

Full infrastructure health check across all VPS services, databases, tokens, and project health.

## Execution Steps

### Step 1: PM2 Status Check
```bash
ssh root@${VPS_HOST} "pm2 jlist" # Parse JSON output
```

**Check for each process:**
- Status (online/stopped/errored)
- Uptime (< 1h = recently crashed)
- Restart count (high = instability)
- RAM usage (flag if > 200MB for Node.js, > 50MB for Python bots)
- CPU usage (flag if > 30% sustained)

### Step 2: Database Health
```bash
# CLIENTE_EXEMPLO DB
PGPASSWORD=${DB_PASS} psql -h localhost -U ${USER} -d ${USER} -c "
  SELECT count(*) as connections FROM pg_stat_activity;
  SELECT pg_database_size('${USER}') / 1024 / 1024 as size_mb;
"

# CLIENTE_EXEMPLO Dashboard DB
PGPASSWORD=${DB_PASS} psql -h localhost -p 5433 -U cliente_user -d cliente_dashboard -c "
  SELECT count(*) as connections FROM pg_stat_activity;
  SELECT pg_database_size('cliente_dashboard') / 1024 / 1024 as size_mb;
"
```

### Step 3: Disk Usage
```bash
df -h /opt /var /tmp
du -sh /opt/CLIENTE_EXEMPLO/ /opt/CLIENTE_EXEMPLO-dashboard/ /opt/video-pipeline/
du -sh /opt/video-pipeline/tmp/  # Flag if > 50MB
```

### Step 4: Token Validity
```bash
# CLIENTE_EXEMPLO Meta token
curl -s http://localhost:3000/api/meta/token-check

# Check Instagram token (same token, different endpoint)
curl -s "https://graph.facebook.com/v21.0/me?fields=id,name&access_token=$TOKEN"
```

### Step 5: Sync Status
```bash
# Last Eduzz sync
PGPASSWORD=${DB_PASS} psql -h localhost -p 5433 -U cliente_user -d cliente_dashboard -c "
  SELECT plataforma, status, \"iniciadoEm\", registros
  FROM \"SyncLog\" ORDER BY \"iniciadoEm\" DESC LIMIT 5;
"
```

### Step 6: SSL Certificates
```bash
echo | openssl s_client -connect seudominio.com.br:443 2>/dev/null | openssl x509 -noout -dates
echo | openssl s_client -connect seudominio.com.br:443 2>/dev/null | openssl x509 -noout -dates
```

## Output Format

```
🛡️ HEALTH CHECK — {date}
═══════════════════════════════

📊 SERVICES
  ✅ CLIENTE_EXEMPLO      | online | 60MB  | 9h uptime
  ✅ CLIENTE_EXEMPLO-dashboard  | online | 57MB  | 22h uptime
  ✅ pixel-bot      | online | 23MB  | 28m uptime
  ✅ whatsapp-bot   | online | 131MB | 3d uptime
  ⛔ telegram-bot   | stopped
  ✅ CLIENTE_EXEMPLO_4      | online | 36MB  | 9d uptime

💾 DATABASES
  ${USER}:  {size}MB | {connections} connections
  cliente_dashboard: {size}MB | {connections} connections

🔑 TOKENS
  Meta (CLIENTE_EXEMPLO): {status} — {days_left} days
  Meta (UTM Manager): {status}

🔄 SYNCS
  Eduzz: last {date} — {count} records
  Asaas: last {date}

💿 DISK
  /opt: {usage}

⚠️ ALERTS
  {list of issues found}

OVERALL: {score}/10
```

## Alerts — Telegram Notification

If any CRITICAL alert found, send via Telegram immediately:
```
🚨 ALERT: {issue description}
System: {system name}
Action needed: {what to do}
```
