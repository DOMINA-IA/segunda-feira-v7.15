## Task Definition (AIOS Task Format V1.0)

```yaml
task: tokenLifecycle()
responsável: Sentinel (Guardian)
responsavel_type: Agente
trigger: '*token-check'
elicit: false
mode: autonomous
```

## Purpose

Check all API tokens across systems — Meta, Instagram, Claude, Eduzz — verify validity, extend if possible, alert if expiring.

## Token Registry

| System | Token Var | Location | Auto-Refresh |
|--------|-----------|----------|-------------|
| CLIENTE_EXEMPLO | META_ADS_TOKEN | VPS /opt/CLIENTE_EXEMPLO/.env | Yes — /api/meta/token-check |
| UTM Manager | META_ACCESS_TOKEN | Local ~/projetos/utm-manager/.env | Yes — token_refresh.py (crontab Mon 8h) |
| CLIENTE_EXEMPLO Dashboard | META token in .env | VPS /opt/CLIENTE_EXEMPLO-dashboard/.env | No — client (${PESSOA}) responsibility |
| WhatsApp Bot | ANTHROPIC_API_KEY | VPS /opt/CLIENTE_EXEMPLO/.env | No — never expires (API key) |
| Content Studio | Freepik API | Local content-studio config | No — API key, verify monthly |
| Video Pipeline | TG Bot Token | VPS /opt/video-pipeline/config.py | No — bot token, rarely expires |

## Execution Steps

### Step 1: CLIENTE_EXEMPLO Meta Token
```bash
curl -s http://localhost:3000/api/meta/token-check
```
- If `status: "permanent"` → OK
- If `daysLeft < 14` → extend via APP_ID/APP_SECRET
- If `valid: false` → ALERT CRITICAL

### Step 2: UTM Manager Meta Token (local)
```bash
cd ~/projetos/utm-manager && python3 token_refresh.py
```
- Auto-extends if < 14 days
- Updates .env automatically
- Also updates VPS CLIENTE_EXEMPLO .env

### Step 3: CLIENTE_EXEMPLO Dashboard Meta Token
```bash
# Read token from .env
TOKEN=$(grep META_TOKEN /opt/CLIENTE_EXEMPLO-dashboard/.env | cut -d= -f2)
# Verify
curl -s "https://graph.facebook.com/debug_token?input_token=$TOKEN&access_token=$TOKEN"
```
- If expired → alert ${CEO_NAME} to contact ${PESSOA}
- DO NOT extend — different organization

### Step 4: Claude API Key
```bash
# Quick verify
curl -s https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-haiku-4-5-20251001","max_tokens":5,"messages":[{"role":"user","content":"hi"}]}'
```
- If 401 → ALERT (key revoked)
- If 200 → OK

### Step 5: Instagram Token (CLIENTE_EXEMPLO)
```bash
# Same as Meta token — Instagram Graph API uses same token
curl -s "https://graph.facebook.com/v21.0/me/accounts?access_token=$TOKEN"
```
- Verify page access still works

## CRITICAL RULE: Separation

- **NEVER** use CLIENTE_EXEMPLO token for CLIENTE_EXEMPLO Dashboard or vice-versa
- **NEVER** share tokens between client and personal organizations
- Each system has its own token lifecycle independently
- CLIENTE_EXEMPLO tokens are ${PESSOA}'s responsibility — only alert ${CEO_NAME} to contact him

## Output Format

```
🔑 TOKEN LIFECYCLE CHECK — {date}
═══════════════════════════════════

CLIENTE_EXEMPLO (Meta):     ✅ Valid | Permanent | scopes: ads, instagram, pages
UTM Manager (Meta):   ✅ Valid | {days} days left | auto-refresh: active
CLIENTE_EXEMPLO Dashboard (Meta): ⚠️ Check needed — different org
Claude API:           ✅ Valid
Instagram:            ✅ Page access confirmed

OVERALL: {status}
```
