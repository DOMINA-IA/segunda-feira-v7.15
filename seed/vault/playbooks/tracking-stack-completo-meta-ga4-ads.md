---
title: Tracking Stack Completo — Meta + GA4 + Google Ads
type: playbook
domain: traffic
tags:
- tracking
- pixel
- capi
- ga4
- measurement-protocol
- google-ads
- conversion-action
- customer-match
- lookalike
- enhanced-conversions
- dedup
agents:
- traffic
- dev
created: 2026-05-07
verified: 2026-05-07
source: implementação real DOMINIA.IA Mercado Invisível v2 (challenge funnel 5-night
  live)
status: validated-in-production
links:
- target: 2026-05-07-google-tracking-setup
  type: auto-linked
- target: heuristic-dev-quando-criar-google-ads-do-zero-pra-conta-sem-ads-ativos-us
  type: auto-linked
- target: pixel-rollout-safe-fases
  type: auto-linked
- target: capi-schedule-stage-trigger
  type: auto-linked
- target: lp-r1-tracking-fix-2026-05-05
  type: auto-linked
axis: meta
---

# Tracking Stack Completo — Meta + GA4 + Google Ads

> **Pré-requisito:** todo projeto que captura lead ou faz aquisição paga DEVE seguir este protocolo. Configurações parciais perdem 30-60% de signal quality e quebram atribuição.

## Princípio

Tracking não é "ativar pixel" — é arquitetar um pipeline com **dedup browser↔server**, **Enhanced Conversions PII hashada**, **Customer Match upload em tempo real**, e **Conversion Actions cross-platform**.

Regra de ouro: **um único `event_id` (UUID v4) atravessa 5 endpoints** sem ser perdido — Pixel browser, CAPI server, GA4 browser, GA4 Measurement Protocol server, Google Ads conversion. Esse é o único jeito de fazer dedup correta no mundo iOS 17+/cookieless.

---

## Stack Completo (8 componentes)

| # | Componente | Camada | Função |
|---|---|---|---|
| 1 | **Meta Pixel** | Browser | Track Lead/Purchase no front, AAM 11 fields |
| 2 | **Meta CAPI v22+** | Server-side PHP | Server-to-server backup, dedup via event_id, hash PII SHA-256 |
| 3 | **GA4 gtag.js** | Browser | PageView + custom events, Enhanced Conversions client-side |
| 4 | **GA4 Measurement Protocol** | Server-side PHP | Backup server-side, dual-event dispatch |
| 5 | **Google Ads gtag conversion** | Browser | `gtag('event', 'conversion', { send_to: AW-XXX/LABEL })` |
| 6 | **Customer Match Upload** | Server-side | Audiências segmentadas em tempo real (6 buckets) |
| 7 | **Lookalikes** | Cron job | Auto-criar 1% BR quando audiência hit ≥100 pessoas |
| 8 | **Domain Verification** | Meta-tag `<head>` | Necessário pra iOS 17+ AAM e atribuição cross-domain |

---

## Pipeline End-to-End (lead único disparando 5 sistemas)

```js
// Quando usuário envia formulário de lead:
const leadEventId = crypto.randomUUID();  // ÚNICO source-of-truth para dedup

// 1. Pixel Meta browser
fbq('track', 'Lead', { value: 27, currency: 'BRL', eventID: leadEventId });

// 2. CAPI server-side (POST → /capi.php)
fetch('/r1/capi.php', {
  method: 'POST',
  body: JSON.stringify({
    event_id: leadEventId,
    event_name: 'Lead',
    email, phone, first_name, last_name, country: 'BR',
    fbp, fbc, value: 27, currency: 'BRL',
    user_agent: navigator.userAgent
  })
});

// 3. GA4 browser
gtag('event', 'generate_lead', {
  transaction_id: leadEventId,
  value: 27, currency: 'BRL'
});

// 4. GA4 Measurement Protocol server-side (POST → /google.php)
//    Dispara DUAL: generate_lead + close_convert_lead (Key Event default)
fetch('/r1/google.php', {
  method: 'POST',
  body: JSON.stringify({
    _internal_secret: SHARED_SECRET,
    event_id: leadEventId,
    event_name: 'generate_lead',
    client_id: gaClientId,
    email, phone, first_name, last_name,
    value: 27, currency: 'BRL',
    gclid, fbclid, fbp, fbc
  })
});

// 5. Google Ads conversion (browser, com event_id pra dedup)
gtag('event', 'conversion', {
  send_to: 'AW-${GADS_CONVERSION_ID}',  // Conversion ID/Label
  value: 27,
  currency: 'BRL',
  transaction_id: leadEventId
});
```

---

## Setup From Zero — Checklist em 4 Fases

### FASE 1 — META (Pixel + CAPI + Customer Match)

```
[ ] Criar Pixel no Business Manager (ou usar existente)
[ ] Capturar Pixel ID + Access Token (graph_token com ads_management permission)
[ ] Implementar capi.php (template em ~/desafio/r1/capi.php — copiar e ajustar Pixel ID)
[ ] Constants no capi.php:
    - const PIXEL_ID = 'XXXXX';
    - const ACCESS_TOKEN = 'EAAt...';
    - const INTERNAL_SECRET = 'random_2026_xxx';  // shared com lead.php
    - SHA-256 hash em em, ph, fn, ln, ct, st, zp, country
[ ] AAM (Auto Advanced Matching) — 11 fields: em, ph, fn, ln, ct, st, zp, country, ge, db, external_id
[ ] Domain Verification:
    - Meta-tag <meta name="facebook-domain-verification" content="..."> no <head> do root domain (NÃO subdomain)
    - Validar: curl -A "facebookexternalhit/1.1" https://dominio.com.br | grep "facebook-domain"
[ ] Customer Match — criar 6 audiências segmentadas via Marketing API:
    - all_leads, hot_leads (score ≥80), morno_leads (60-79), decisores, faturamento, serviços
    - Subtype CUSTOM, customer_file_source USER_PROVIDED_ONLY
[ ] Vincular Ad Account ao Business Manager (POST /{biz}/owned_ad_accounts)
[ ] Aceitar TOS de Custom Audiences (subcode 1870090 = não aceito ainda)
[ ] Cron monitor: ~/desafio/cron-monitor.py rodando a cada 30min
    - Audiência size tracking
    - Domain verification status
    - Lookalike auto-creation quando audiência ≥100 pessoas
```

### FASE 2 — GA4 (Property + Stream + Measurement Protocol)

```
[ ] Criar Account + Property em analytics.google.com
    - Setor: Comércio e indústria
    - Tamanho: Pequena (1-10 funcionários)
    - Objetivo: "Gerar leads" (cria 3 Key Events default automaticamente: close_convert_lead, purchase, qualify_lead)
[ ] Criar Stream Web → capturar Measurement ID (G-${GA4_ID})
[ ] Criar Measurement Protocol API Secret:
    - Admin → Coleta e modificação → Fluxos de dados → [stream] → Chaves secretas da API do Measurement Protocol
    - Aceitar "Confirmação de coleta de dados do usuário" (GDPR/LGPD)
    - Capturar secret value (~22 chars Base64)
[ ] Property Settings (Admin → Configurações da propriedade → Detalhes):
    - Fuso horário: (GMT-03:00) Horário São Paulo (NÃO Rio Branco GMT-05)
    - Moeda: Real brasileiro (R$)
    - Confirmar com "Sim, salvar" (dialog secundário)
[ ] Implementar google.php:
    - const GA4_MEASUREMENT_ID = 'G-${GA4_ID}';
    - const GA4_API_SECRET = 'XXX';
    - DUAL DISPATCH: quando event_name='generate_lead', disparar TAMBÉM 'close_convert_lead' no mesmo payload (popula Key Event antes do primeiro hit real)
    - SHA-256 hash em user_data: sha256_email_address, sha256_phone_number, sha256_first_name, sha256_last_name
[ ] No HTML: gtag('config', 'G-XXX'), Conversion Linker, Enhanced Conversions helper
[ ] Smoke test:
    curl -X POST https://dominio.com.br/google.php \
      -d '{"_internal_secret":"...","event_id":"smoke_test","event_name":"generate_lead","client_id":"smoke","email":"usuario@example.com","value":27,"currency":"BRL"}'
    Esperar: {"ga4":{"http":204,"ok":true}}
```

### FASE 3 — GOOGLE ADS (Conta + Conversion Action + Link GA4)

**Hack importante:** o Google Ads removeu o "Expert Mode" da UI em 2024+. Pra criar conta SEM campanha ativa:

```
[ ] ads.google.com → "Nova conta do Google Ads"
[ ] Wizard step 1 (About your business):
    - Nome empresa (opcional)
    - URL do site (radio "Seu site" selected)
[ ] Step 2 (Business insights):
    - Descreva produtos/serviços (texto livre)
[ ] Step 3 (Linking accounts):
    - Clicar "Pular" — não precisa linkar YouTube/App/Profile pra Conversion Action
[ ] Step 4 (Goals):
    - 🎯 NO RODAPÉ: clicar "Configure apenas a conta" (link discreto)
    - Pula direto pro confirm settings, sem criar campanha
[ ] Confirmar configurações da conta:
    - País: Brasil
    - Fuso: GMT-03 São Paulo
    - Moeda: Real brasileiro (BRL R$)
    - ⚠️ IRREVERSÍVEIS após criação
[ ] Página de pagamento:
    - Visa cadastrada (ou novo cartão)
    - ⚠️ R$50,00 cobrança de autorização (refund automático em ~1 semana)
    - Configuração: Pagamento automático
    - Aceitar TOS
[ ] Capturar Customer ID (formato 123-456-7890 → AW-${GADS_CONVERSION_ID})
```

**Criar Conversion Action:**

```
[ ] Tools → Goals → Conversões → "Nova ação de conversão"
[ ] Categoria: "Inscrição" (= Submit lead form em PT-BR)
[ ] Selecionar fonte: site cadastrado
[ ] Modo: "Manualmente com código" (NÃO automático sem código)
[ ] Configurações de conversão:
    - Nome: "PROJETO - Lead Tipo R$XX"  (ex: "DOMINIA - Lead MIv2 R$27")
    - Valor: "Usar valores diferentes para cada conversão" + Real brasileiro + valor padrão (ex: 27)
    - Contagem: Uma (NÃO Todas — leads não devem contar múltiplas vezes)
    - Janela: 90d clique / 3d view-engaged / 1d view (defaults bons)
    - Atribuição: Modelo baseado em dados (data-driven, recomendado)
[ ] Ativar Enhanced Conversions na conta (checkbox marcado por default)
[ ] Capturar AW Conversion ID (formato AW-XXXXXXXXXX)
[ ] Capturar Conversion Label (string ~20 chars)
[ ] Snippet completo: AW-XXX/LABEL
```

**Linkar GA4 ↔ Ads:**

```
[ ] GA4 Admin → Vínculos de produtos → Contas vinculadas do Google Ads
[ ] "Vincular" → "Escolha as contas do Google Ads que eu gerencio"
[ ] Marcar checkbox da conta → Confirmar
[ ] Step 2: Personalized advertising ON + Auto-tagging ON (defaults)
[ ] Step 3: Revisar → Enviar
[ ] Confirmação: badge "VINCULAÇÃO CRIADA" verde
[ ] Dados aparecem em até 24h
```

### FASE 4 — DEPLOY + VALIDAÇÃO

```
[ ] Aplicar IDs em produção via apply-google-ids.sh:
    bash ~/desafio/apply-google-ids.sh "GA4_API_SECRET" "AW-XXXX" "LABEL"
[ ] ⚠️ BUG CONHECIDO: o script deixa o snippet gtag('event','conversion'...) COMENTADO no HTML.
    Verificar com: curl https://dominio.com/r1/ | grep "send_to"
    Se aparecer "// send_to:", descomentar manualmente via perl:
    perl -i -pe "s|// gtag\('event', 'conversion'|gtag('event', 'conversion'|g; ..." arquivo.html
[ ] SFTP zero-downtime deploy (PUT new → rename atual→prev → rename new→atual)
[ ] Smoke tests obrigatórios:
    1. curl /r1/ | grep -oE "G-[A-Z0-9]+" → matches Measurement ID
    2. curl /r1/ | grep "AW-" → matches AW Conversion ID
    3. curl /r1/ | grep "send_to: '" → matches AW/LABEL (NÃO comentado)
    4. curl /r1/google.php?action=health → ga4_api_secret: configured
    5. POST E2E lead → ga4: HTTP 204 OK + dual close_convert_lead
[ ] Validação no Realtime do GA4 (~1-2 min após primeiro lead)
[ ] Validação no Meta Events Manager (EMQ score sobe em 24-48h)
[ ] Validação no Google Ads Conversion summary (até 24h)
```

---

## Bugs Conhecidos & Resoluções

### Bug 11 — Server PHP em UTC + crm=200 (reentry) confundem debug Meta vs CLIENTE_EXEMPLO

**Sintoma:** Meta Ads Manager mostra X leads, CLIENTE_EXEMPLO mostra Y < X (X=3, Y=1 caso real). CEO acha que Pixel está inflado.

**Causa raiz dupla:**
1. **Server PHP timezone = UTC** — Hostinger não vem com `America/Sao_Paulo` por default. Logo `[2026-05-08 00:11:28]` no `lead.log` = `2026-05-07 21:11:28 BRT` (3h diferença) — entry de "hoje" no log pode ser "ontem" pro CEO.
2. **`crm=200` (HTTP) ≠ "lead novo"** — significa REENTRY (lead já existia, CLIENTE_EXEMPLO incrementa `reentry_count`, NÃO cria registro novo). Apenas `crm=201` (HTTP Created) é lead novo.
3. **Meta dedup ignora reentry** — Meta conta TODOS os Lead events (servers + browser) sem distinguir novo/reentry. CLIENTE_EXEMPLO só conta novos. Por isso o gap.

**Diagnóstico (executar nessa ordem):**
```bash
# 1. Cruzar lead.log entries com Pixel events
curl "https://graph.facebook.com/v22.0/$PIXEL/stats?access_token=$T&aggregation=event_source&event=Lead&start_time=$TODAY_UTC"
# → mostra SERVER vs BROWSER count (deduplicado)

# 2. Verificar timezone do server
echo "<?php echo date_default_timezone_get();" > tz.php
curl https://desafio.../r1/tz.php
# → se UTC, todos os timestamps do log estão 3h adiantados em relação ao BRT

# 3. Filtrar lead.log por crm=201 (novos) vs crm=200 (reentry)
grep "2026-05-08" lead.log | awk '/crm=201/' # leads NOVOS de hoje
grep "2026-05-08" lead.log | awk '/crm=200/' # reentries de hoje
```

**Fix preventivo (1 linha em lead.php + capi.php):**
```php
<?php
date_default_timezone_set("America/Sao_Paulo"); // BRT para logs
```

**Lição:** Antes de declarar discrepância de tracking como BUG, validar timezone do server e checar se CLIENTE_EXEMPLO differencia reentry de novo lead. Sintomas idênticos a "Pixel inflado" mas é problema de **leitura**, não de **dispatch**.

**Referência:** Caso 08-Mai-2026 — Meta 3 vs CLIENTE_EXEMPLO 1 lead. Análise consolidada em consciousness episode `ep_traffic_20260508140428`.

---

### Bug 1 — apply-google-ids.sh deixa snippet comentado

**Sintoma:** Após rodar o script, `curl prod | grep send_to` retorna `// send_to: 'AW-XXX/LABEL'` (comentado).

**Causa:** O sed do script substitui o ID dentro do bloco mas não remove os `// ` que comentavam o snippet inteiro.

**Fix manual:**
```bash
for f in /tmp/_r1.html /tmp/_f1.html; do
  perl -i -pe "
    s|// gtag\('event', 'conversion'|gtag('event', 'conversion'|g;
    s|//   send_to: 'AW-|  send_to: 'AW-|g;
    s|//   value: parseFloat|  value: parseFloat|g;
    s|//   currency: 'BRL'|  currency: 'BRL'|g;
    s|//   transaction_id: leadEventId|  transaction_id: leadEventId|g;
    s|// \}\);|});|g if \$prev =~ /transaction_id/;
    \$prev = \$_;
  " "$f"
done
```

### Bug 2 — GA4 Admin SPA não aceita deep-linking

**Sintoma:** `goto('/admin/streams/list')` redireciona pra `/reports/intelligenthome`.

**Workaround:** Sempre navegar via UI: clicar "Administrador" → expandir treeview → clicar item específico. Isso requer click via JS evaluate (`offsetParent !== null` filter) porque Angular Material recria refs ao expandir.

### Bug 3 — Domain Verification "Not Verified" mesmo com meta-tag correta

**Sintoma:** Meta Business Manager mostra "Falha na verificação" mesmo após `curl -A "facebookexternalhit/1.1"` confirmar tag presente em `<head>`.

**Causa:** Cache server-side do crawler do Meta (separado do cache do Sharing Debugger).

**Fix:** Aguardar até 72h. Triggerar Sharing Debugger "Extrair novamente" + clicar "Verificar domínio" 2x. Cron-monitor detecta mudança de status.

### Bug 4 — Google Ads conta nova exige cartão (R$50 autorização)

**Sintoma:** Não há "skip billing" no wizard final.

**Workaround:** R$50 é cobrança de autorização temporária — refund automático em ~1 semana. Conta criada SEM campanha ativa não gera spend recorrente. Pagamento automático só dispara quando atinge limite de faturamento.

### Bug 5 — generate_lead não aparece na lista de Key Events

**Sintoma:** GA4 → Eventos principais não permite marcar `generate_lead` com estrela porque nunca foi recebido.

**Solução:** Dual-dispatch no google.php:
```php
$events_list = [[ 'name' => $event_name, 'params' => $event_params ]];
if ($event_name === 'generate_lead') {
    $events_list[] = [ 'name' => 'close_convert_lead', 'params' => $event_params ];
}
```
Assim `close_convert_lead` (que JÁ é Key Event default) é populado imediatamente, garantindo ROI tracking sem aguardar primeiro hit real.

### Bug 10 — Páginas legacy com Pixel ID antigo poluindo ecossistema

**Sintoma:** Meta Events Manager mostra dados estranhos — Lead/Purchase events em pixels que você não reconhece, ou métricas dispersas entre múltiplos pixels.

**Causa real:** Em projetos com múltiplos lançamentos ao longo de meses/anos, páginas antigas (VIP, obrigado, confirmações, root index do subdomain) ficam com Pixel ID de campanhas anteriores. Quando o tráfego chega nelas (links antigos compartilhados, cache de redes sociais, retargeting), os events vão pro pixel errado.

**Validado em produção** — DOMINIA Mercado Invisível v2 (08-Mai-2026): descobri **3 Pixels diferentes** ativos no mesmo subdomain:
- `${PLATFORM_ID}` — DOMINIA High Ticket (correto, novo)
- `${PLATFORM_ID}` — Pixel low-ticket antigo (esquecido em /r1/obrigado/)
- `${META_PIXEL_ID}` — Pixel desconhecido VIP (em 7 páginas legacy: /, /vip.html, /obrigado-vip*, /v3.html, /confirmado-vip.html, /obrigado-vip/)

Resultado: dados Meta dispersos entre 3 pixels, atribuição quebrada, EMQ score baixo (signal fragmentado).

**Diagnóstico recursivo (mandatório em todo projeto):**

```bash
# 1. Listar TODOS arquivos HTML/PHP no servidor via SFTP
sftp host -P PORT -e "ls -R /caminho/projeto/" > _all_files.txt

# 2. Baixar todos os HTML/PHP
mkdir /tmp/audit_pixel && cd /tmp/audit_pixel
sftp ... <comandos get pra cada arquivo>

# 3. Grep recursivo todos os Pixel IDs únicos
for f in *.html *.php; do
  pixels=$(grep -oE "fbq\\('init', '[0-9]+'" "$f" | sort -u)
  [ -n "$pixels" ] && echo "📄 $f: $pixels"
done

# 4. Cross-check com Pixel ID esperado (PIXEL_OFICIAL)
# Qualquer Pixel ID diferente = páginas pra migrar
```

**Fix em batch:**
```bash
# Substituir TODOS os pixels antigos pelo correto
for f in arquivo1.html arquivo2.html ...; do
  sed -i '' 's/PIXEL_ANTIGO/PIXEL_CORRETO/g' "$f"
done

# Inclui o fallback <noscript><img src="...id=PIXEL_ID..."></noscript>
# (sed simples cobre ambos)
```

**Heurística**: "Páginas legacy frequentemente têm pixels antigos esquecidos. Auditoria recursiva (SFTP ls + grep `fbq.*init` em todos arquivos) é mandatória pra confirmar consistência cross-page do Pixel. Não confiar que 'só /r1/ importa' — qualquer página HTTP 200 que dispara fbq pode poluir relatórios."

**Quando aplicar essa auditoria:**
- Início de todo projeto novo em domain/subdomain compartilhado
- Pré-lançamento (D-3 checklist)
- Após migrar de pixel low-ticket → high-ticket
- Suspeita de discrepância em Events Manager (CPL diferente do esperado)

---

### Bug 9 — Webhook EXISTENTE apontando pra URL errada (falso positivo silencioso)

**Sintoma:** Painel do gateway de pagamento (Eduzz, Hotmart, Stripe) mostra webhook **"Ativo"**, status verde, "tudo configurado". Mas zero events chegam ao endpoint correto. ROAS dashboard fica vazio. Atribuição quebrada sem alerta.

**Causa real (mais comum que parece):** Webhook foi configurado meses atrás apontando pra URL antiga ou incorreta:
- `eduzz-webhook.php` (correto, processa payload Eduzz) **vs** `capi.php` (rejeita Eduzz format porque espera `_internal_secret`)
- `webhook.php` (deletado) vs `purchase-webhook.php` (renomeado)
- Domain antigo (`old-domain.com`) vs domain novo após migração

**Diagnóstico que confirma:**
```bash
# 1. Curl direto da URL no painel webhook do gateway:
curl -X POST <URL_CONFIGURADA_NO_PAINEL> \
  -H "Content-Type: application/json" \
  --data '{"trans_cod":"DIAG","trans_status":3,"product_cod":"X","trans_value":"27"}'

# Se retornar 401/403/forbidden → webhook está errado
# Se retornar 200 mas log local não tem entry → endpoint correto mas processamento errado
# Se retornar 200 + log mostra purchase_processed → tudo OK

# 2. Ver log de tentativas no servidor:
tail /tmp/{eduzz,hotmart,stripe}-purchases.jsonl
# Se as últimas entries têm "skipped" e nenhum "processed" → problema
```

**Fix Eduzz específico:**
1. Login: https://orbita.eduzz.com/ → Apps → Webhooks → "Acessar Developer Hub" (legacy descontinuado)
2. https://console.eduzz.com/webhook/configs → encontrar webhook existente
3. Menu "..." → **Editar** (NÃO clicar no toggle Ativo — abre modal de Desativar)
4. Trocar URL pra `https://dominio.com.br/r1/eduzz-webhook.php`
5. Clicar **Verificar URL** → esperar "Status HTTP 200 - Sucesso!"
6. Salvar configuração
7. Voltar pra lista → Menu "..." → **Testar eventos** → enviar teste real do Eduzz
8. Resultado esperado: "Eventos integrados com sucesso (1)" + `0 falhas`

**Por que esse é o bug mais traiçoeiro:**
Auditoria "feliz" valida que webhook está "Ativo" no painel — sem checar URL. Auditoria adversarial pode pegar lead.php sem rate limit mas não pega webhook URL incorreta porque esse é estado externo (no painel do gateway, não no nosso código). **Único jeito de detectar é fazer curl direto na URL configurada e ver resposta.**

### Bug 8 — Semântica de `close_convert_lead` no dual-dispatch

**Sintoma:** GA4 → Eventos principais → `close_convert_lead = N` onde N exatamente igual a `generate_lead`. Pode parecer 'taxa de conversão de funil' nos relatórios e enganar análise pós-evento.

**Causa intencional:** O dual-dispatch foi criado pra popular o Key Event default antes do primeiro hit real (Bug 5). Efeito colateral: `close_convert_lead` é uma cópia de `generate_lead`, não uma conversão de funil real.

**Mitigação documental:** Em todo report pós-evento que mencione `close_convert_lead`, adicionar nota:
> *"close_convert_lead = proxy de lead form submit. NÃO é conversão de funil. Use `purchase` para conversão real."*

**Alternativa (refactor futuro):** Renomear o evento dual no `google.php` para `lead_form_submit_server` ou só dispatchar `close_convert_lead` quando `score >= 75` (lead realmente "qualificado"). Mas isso requer refactor cuidadoso e re-treinamento de quem analisa GA4.

### Bug 7 — Endpoint `/{biz}/owned_domains` retorna #100 (deprecated/sem scope)

**Sintoma:** `cron-monitor.py` log mostra `domain check ERROR: HTTP Error 400: Bad Request` indefinidamente. Token Graph API retorna `{"error":{"message":"(#100) Tried accessing nonexisting field (owned_domains)"}}`. Tentar `/{domain_id}` direto retorna `(#10) Application does not have permission for this action`.

**Causa:** API v22+ removeu/depreciou o edge `owned_domains`. Tokens criados via Business System User não têm scope pra ler domain status diretamente, mesmo com `business_management` permission.

**Workaround validado:** Validar via meta-tag no HTML do root domain (sempre funciona, não depende de Graph API):

```python
def check_domain():
    expected = "v2xak3lln7xq8n6lnd4coja3i6e3qb"  # token de verificação Meta
    req = Request("https://dominio.com.br/", headers={
        "User-Agent": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
    })
    with urlopen(req, timeout=10) as r:
        html = r.read().decode("utf-8", "ignore")
    if expected in html and "facebook-domain-verification" in html:
        return {"status": "meta_tag_present"}
    return {"status": "META_TAG_MISSING", "alert": True}
```

**Status real (Verified/Not Verified)** só pelo Business Manager UI ou Sharing Debugger — sem API pública pra esse signal nas v20+.

### Bug 6 — LiteSpeed cacheia GET de health endpoint (Hostinger)

**Sintoma:** `curl /google.php?action=health` retorna `gads_enabled: false` mesmo após `apply-google-ids.sh` setar `GADS_API_ENABLED = true` na constante PHP.

**Causa:** LiteSpeed (servidor padrão Hostinger) cacheia respostas GET por URL exata. Como `?action=health` puro não tem query única, o cache serve a versão antiga.

**Validação que comprova o bug:**
```bash
# Cache stale — retorna estado antigo:
curl https://dominio.com/r1/google.php?action=health
# → "gads_enabled":false

# Com query buster — força recompute:
curl "https://dominio.com/r1/google.php?action=health&_=$(date +%s)"
# → "gads_enabled":true  (correto)
```

**Fix permanente (preferido):** Adicionar `Cache-Control: no-cache` ao header do PHP em GET requests:
```php
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    header('Cache-Control: no-cache, no-store, must-revalidate');
    header('Pragma: no-cache');
    header('Expires: 0');
    echo json_encode([
        'status' => 'ok',
        // ...
    ]);
    exit;
}
```

**Workaround imediato (sem redeploy):** sempre usar query buster ao auditar:
```bash
HEALTH_URL="https://dominio.com/r1/google.php?action=health&_=$(date +%s%N)"
curl -s "$HEALTH_URL"
```

**Impacto operacional:** ZERO. O server-side processa corretamente — apenas a leitura cacheada do health engana auditoria visual. Adicionar ao smoke test que sempre use query buster.

---

## Heurísticas Validadas em Produção

| Heurística | Validação |
|---|---|
| Usar **`browser_click` com target ref** em Angular Material, não `evaluate + .click()` | MAT-CHECKBOX só vincula ao FormControl via evento real do framework |
| Filtrar `offsetParent !== null` antes de clicar | Múltiplos botões com mesmo texto (sidebar + dialog) — `find` pega o primeiro errado |
| **`material-button`** vs `button` no Google Ads | UI legacy usa custom element; querySelectorAll('button') não pega |
| **"Configure apenas a conta"** (rodapé do step Goals) | Único caminho pra criar Ads sem campanha ativa em 2024+ |
| **"Inscrição" (PT-BR) = Submit lead form (EN)** | Categoria correta para Conversion Action de lead capture |
| **Contagem "Uma"** (não "Todas") em leads | Lead não converte múltiplas vezes — defaults Google sabem |
| **Atribuição: data-driven** | ML do Google distribui crédito entre touchpoints — superior a last-click |
| **Janela 90d/3d/1d** | Defaults do Google são certos pra high-ticket (funil longo) |
| **gtag conversion + Enhanced Conversions client-side** | Cobre 95% dos casos sem precisar Google Ads API server-side |

---

## Variáveis Genéricas → Substituir por Projeto

> ⚠️ **NÃO copiar valores reais.** Cada projeto tem seus próprios IDs. Os valores reais ficam em `~/.env.{projeto}` (mode 600), nunca no código nem no playbook.

```yaml
# Template — substituir TODOS por valores do projeto novo:
PROJECT_NAME:           "MEU_PROJETO - Tipo R$XX"
META_PIXEL_ID:          "<NÚMERO_PIXEL>"
META_ACCESS_TOKEN:      "EAA<TOKEN>"
META_BUSINESS_ID:       "<BUSINESS_ID>"
META_AD_ACCOUNT:        "act_<AD_ACCOUNT_ID>"
META_DOMAIN_ID:         "<DOMAIN_ID>"
GA4_MEASUREMENT_ID:     "G-<MEASUREMENT_ID>"
GA4_API_SECRET:         "<SECRET_22_CHARS>"
GA4_PROPERTY_ID:        "<PROPERTY_ID>"
GA4_STREAM_ID:          "<STREAM_ID>"
GA4_ACCOUNT_ID:         "<ACCOUNT_ID>"
GADS_CUSTOMER_ID:       "XXX-XXX-XXXX"   # AW-XXXXXXXXXX
GADS_CONVERSION_ID:     "AW-<ID_NUMÉRICO>"
GADS_CONVERSION_LABEL:  "<LABEL_~20_CHARS>"
INTERNAL_SECRET:        "<RANDOM_SECRET_GERADO>"
DOMAIN_VERIFICATION:    "<TOKEN_META_DOMAIN>"
LEAD_VALUE_BRL:         <VALOR_DO_LEAD>
```

### Onde armazenar os valores reais (por projeto)

```bash
# Crie ~/.env.{slug-do-projeto} (mode 600) com export VAR="valor"
chmod 600 ~/.env.meu-projeto

# Source no shell antes de rodar scripts:
source ~/.env.meu-projeto
bash apply-google-ids.sh "$GA4_API_SECRET" "$GADS_CONVERSION_ID" "$GADS_CONVERSION_LABEL"
```

### Referência projeto DOMINIA Mercado Invisível v2 (07-Mai-2026)

Os IDs reais deste projeto estão em `~/.env.desafio` (mode 600), apenas no Mac do CEO. **Não copiar para outros projetos** — cada projeto tem seus próprios IDs novos.

---

## Templates Disponíveis (em `~/desafio/`)

| Arquivo | Função |
|---|---|
| `r1/capi.php` | Pixel CAPI v22 server-side com Customer Match upload |
| `r1/google.php` | GA4 Measurement Protocol + Google Ads placeholder |
| `r1/lead.php` | Endpoint de lead capture com BANT scoring 0-100 |
| `apply-google-ids.sh` | Patcher de IDs em batch + SFTP deploy |
| `cron-monitor.py` | Monitor 30min: audiências + domain + lookalike auto |

---

## Checklist D-3 (3 dias antes do evento começar)

> **Obrigatório** para todo evento que rode tráfego pago. Pegar problemas com 72h de margem para resolver, não na hora da live.

```
TRACKING TÉCNICO
[ ] EMQ Score atual no Meta Events Manager → Match Quality (esperar ≥6.5)
[ ] Domain Verification status no Business Manager → Domains (precisa "Verified")
[ ] GA4 Realtime → fazer 1 visita real e ver page_view aparecer em <30s
[ ] Google Ads → Tools → Conversions → status "Recebendo conversões" para CA principal
[ ] GA4 ↔ Ads link badge "Concluídas (1)" verde

PIXEL UNIFICADO (Bug 10 paranoia — auditoria recursiva)
[ ] SFTP ls -R no diretório do projeto inteiro
[ ] Baixar TODOS arquivos HTML/PHP
[ ] grep -oE "fbq\\('init', '[0-9]+'" em cada um → coletar Pixel IDs únicos
[ ] Cross-check: TODOS devem ser o mesmo Pixel oficial do projeto atual
[ ] Páginas legacy/VIP/obrigado/confirmação são suspeitas conhecidas
[ ] Substituir Pixel antigo via sed batch + deploy zero-downtime
[ ] Validar via curl em cada URL HTTP 200 do subdomain

PIPELINE END-TO-END (smoke real)
[ ] Preencher form da LP /r1/ com email TEST → confirmar:
    1. CRM (CLIENTE_EXEMPLO) cadastrou
    2. Pixel CAPI received (Events Manager → Realtime)
    3. GA4 generate_lead aparece em ~10s
    4. Google Ads conversion (browser) dispara — DevTools Network filter "google.com/g/collect"
    5. Hot leads JSONL atualiza /tmp/hot-leads.jsonl (se score >= 75)
    6. Telegram alert chega ao CEO (se score >= 75)

ROUTING POR FAIXA DE SCORE (testar cada uma)
[ ] Score <40 → nurture page só confirmação ✅
[ ] Score 40-59 → comum (Eduzz R$27 slug peb4kcik) ✅
[ ] Score 60-79 → vip (Eduzz R$97 slug 4fdsmzqx) ✅
[ ] Score ≥80 + capacity → conselho WhatsApp wa.me/{número} ✅
[ ] WhatsApp do conselho está ATIVO (alguém responde em <1h durante evento)

EDUZZ (auditoria contra Bug 9 — webhook URL errada silenciosa)
[ ] Login em https://console.eduzz.com/webhook/configs (Developer Hub novo)
[ ] Listar webhooks existentes — se houver um chamado "MI v2 — CAPI Meta", "Tracking",
    "Pixel Meta" ou similar de projetos passados → AUDITAR URL atual
[ ] Para cada webhook ativo: clicar "..." → Editar → confirmar que URL aponta
    pra /r1/eduzz-webhook.php (NÃO /r1/capi.php — capi.php rejeita payload Eduzz)
[ ] Clicar "Verificar URL" no painel → esperar "Status HTTP 200 - Sucesso!"
[ ] Salvar configuração
[ ] Menu "..." → "Testar eventos" → enviar teste real do Eduzz
[ ] Resultado esperado: "Eventos integrados com sucesso (1) | 0 falhas"
[ ] CUIDADO: NÃO clicar no toggle Ativo/Inativo da row — abre modal de DESATIVAR
[ ] Confirmar evento subscribed: myeduzz.invoice_paid (compras pagas)
[ ] Verificar tail /tmp/eduzz-purchases.jsonl no servidor após o teste:
    - Se "purchase_processed": tudo OK
    - Se "eduzz_status_skipped": payload Eduzz veio sem trans_status (esperado em test event)
    - Se 0 entries: webhook não está chegando — auditar URL
[ ] Configurar Pixel nativo do Eduzz nos 3 produtos (R$27, R$97, R$ X.XXX):
    Painel → Produtos → Editar → Marketing → Pixel Facebook ID

CONTA ADS (PARANOIAS DE BILLING)
[ ] Budget limit mensal setado (mínimo R$50) — Tools → Billing
[ ] Cartão correto (não estourar inadvertidamente)
[ ] Notificações de gasto >50% do budget ativas

INFRAESTRUTURA
[ ] cron-monitor rodando (Hostinger preferido vs Mac local)
[ ] Telegram bot online (mandar /start manual e ver resposta)
[ ] Backups *-prev-* limpos a >7d (não deixar 50 arquivos no servidor)
[ ] Domain HTTPS válido (curl -I e ver 200)

DOCUMENTAÇÃO PÓS-EVENTO
[ ] Decidir antes do evento: o que vamos analisar pós-mortem?
    - CPL por canal (utm_source breakdown)
    - Score breakdown vs conversion rate (BANT funcionou?)
    - EMQ score evolução
    - Lookalike performance vs audience seed
[ ] Configurar Reports GA4 + dashboard Meta Ads Manager pra acompanhar live
```

### Sinais Vermelhos no D-3 (abortar evento ou postergar)

| Vermelho | Razão |
|---|---|
| EMQ Score <5.0 | Match quality tão ruim que campanha vai performar 50% pior |
| Domain "Not Verified" | iOS 17+ vai bloquear AAM, atribuição quebra |
| WhatsApp conselho sem responder em ≤2h | Leads R$ X.XXX vão esfriar — perda direta de R$X mil |
| Webhook Eduzz não configurado | ROAS cego, otimização errada na campanha |

---

## Validação E2E (smoke test obrigatório por projeto)

```bash
EID="smoke_$(date +%s)"

# Test 1: GA4 server-side dispatch
curl -s -X POST https://dominio.com.br/r1/google.php \
  -H "Content-Type: application/json" \
  -d "{
    \"_internal_secret\": \"$INTERNAL_SECRET\",
    \"event_id\": \"$EID\",
    \"event_name\": \"generate_lead\",
    \"client_id\": \"smoke.$EID\",
    \"email\": \"usuario@example.com\",
    \"value\": 27,
    \"currency\": \"BRL\"
  }"

# Esperar: {"ok":true,"ga4":{"http":204,"ok":true}}

# Test 2: HTML deployado
curl -s https://dominio.com.br/r1/ | grep -oE "(G-|AW-)[A-Za-z0-9_/-]+" | sort -u
# Esperar: G-${GA4_ID}, AW-XXXXXXXXXX, AW-XXXXXXXXXX/LABEL

# Test 3: gtag NÃO comentado
curl -s https://dominio.com.br/r1/ | grep "gtag('event', 'conversion'"
# Esperar: linha SEM // prefix

# Test 4: Health endpoint (com query buster pra evitar cache LiteSpeed — Bug 6)
curl -s "https://dominio.com.br/r1/google.php?action=health&_=$(date +%s%N)"
# Esperar: "ga4_api_secret":"configured" + "gads_enabled":true (se AW configurado)
# ⚠️ SEM o query buster pode retornar dados antigos cacheados — sempre incluir &_=timestamp
```

---

## Métricas de Qualidade (acompanhar pós-deploy)

| Métrica | Onde | Meta |
|---|---|---|
| Meta EMQ Score | Events Manager → Match Quality | ≥7.0/10 (after 24-48h) |
| GA4 Realtime hits | Realtime → Events | aparece em ~10s |
| Google Ads Conversions | Tools → Conversions → status | "Recebendo conversões" em ~2h |
| Customer Match audiência size | Audiências → tabela | crescimento linear com leads |
| GA4 ↔ Ads link | Admin → Vínculos | "VINCULAÇÃO CRIADA" badge verde |
| Domain Verification | Business Manager → Domains | "Verified" em ≤72h |

---

## Cenário Especial: Webhooks Legados em URL Errada (Bug 9)

> **Validado em produção** — DOMINIA Mercado Invisível v2 (08-Mai-2026): webhook Eduzz "MI v2 — CAPI Meta" estava ATIVO no Developer Hub há semanas mas apontando pra `capi.php` (que rejeita payload Eduzz com 403). Toda compra anterior foi silenciosamente perdida. Apenas auditoria via Playwright pegou.

### Sintomas do Bug 9

| Sintoma | Diagnóstico |
|---|---|
| Painel mostra webhook "Ativo" verde | Mas só significa que existe, não que funciona |
| ROAS dashboard vazio mesmo com vendas | Webhook não está chegando ao endpoint correto |
| Telegram alert de Purchase nunca dispara | URL errada → endpoint correto não recebe |
| `tail /tmp/eduzz-purchases.jsonl` vazio | Endpoint correto sem registros |
| Curl direto na URL retorna 403/forbidden | URL aponta pra endpoint que rejeita o payload |

### Protocolo de Auditoria Antes de Criar Webhook Novo

```
1. SEMPRE listar webhooks existentes ANTES de criar novo
   - Eduzz: console.eduzz.com/webhook/configs (não orbita.eduzz.com legacy)
   - Hotmart: https://app.hotmart.com/tools/webhooks
   - Stripe: dashboard.stripe.com/webhooks
   - Mercado Pago: webhooks IPN no painel

2. Se encontrar webhook com nome relacionado ao projeto/produto:
   - Clicar "Editar" (NÃO toggle Ativo — abre modal de desativar)
   - Validar URL atual aponta pro endpoint que processa o payload do gateway

3. Curl direto na URL configurada (com payload do gateway):
   curl -X POST <URL_NO_PAINEL> -H "Content-Type: application/json" \
        --data '{"trans_cod":"DIAG","trans_status":3,...}'
   - 200 + log entry "purchase_processed" = OK
   - 200 + log "skipped" = endpoint correto, mas payload incompleto
   - 401/403 = URL errada (problema)
   - 404 = endpoint não existe (problema)

4. Se URL errada: **EDITAR** o webhook existente. NÃO criar redundante.

5. Após corrigir, sempre **"Testar eventos"** nativo do painel (envia payload real)
```

### Por que esse bug é traiçoeiro

- Auditoria "feliz" só valida que webhook existe ✅
- Smoke test E2E manual via curl funciona (porque você testa URL correta) ✅
- Só descoberto ao **abrir o painel do gateway e ver URL configurada** ❌
- Bots scanners não pegam (não conseguem ver painel privado)
- Adversário não pega (sem acesso ao painel)

**Heurística: "Webhook 'Ativo' no painel ≠ webhook funcionando. Sempre auditar URL."**

---

## Cenário Especial: Tráfego Gerido por Terceiro (Agência/Gestor)

> **CRÍTICO** — Padrão no mercado brasileiro: gestor de tráfego opera em conta própria (MCC). Sem cuidado, todo o tracking criado fica em conta SEM campanhas.

### Antes de criar a Conversion Action

```
[ ] Pergunte ao gestor: "Você opera em qual Customer ID? Vou criar a Conversion Action lá."
[ ] Se ele já tem conta com tráfego rodando, pedir AW + Label de uma Conversion Action que ele crie
[ ] Se você precisa criar a Conversion Action: peça acesso de Standard ou Admin na conta dele
[ ] Alternativa: configure Cross-Account Conversion Tracking (precisa link MCC bidirecional)
```

### Sinais de risco

| Sinal | Diagnóstico | Ação |
|---|---|---|
| Conta nova SEM campanhas, gestor opera em outra | P0 — tracking decorativo | Pedir AW da conta do gestor OU MCC link |
| Conta sem visualizar conversões 24h após primeiro lead | Conversion Action em conta errada | Verificar Customer ID na campanha vs Customer ID na CA |
| Gestor reporta "zero conversões" mas Realtime do GA4 tem hits | Mesmo problema | Re-criar CA na conta certa |

### Por que isso é especialmente crítico

Para campanhas Performance Max ou Smart Bidding, o algoritmo precisa de signal em tempo real. Sem conversão na conta veicular, ele otimiza no escuro:
- CPL real: 2-4x mais alto que com signal correto
- Lookalikes/Audience Insights ficam vazios
- Bidding strategies "Maximize Conversions" tratam o budget como aleatório

Para evento de 19 dias com 250-500 leads esperados, são **R$ X.XXX-8.000 desperdiçados** em otimização cega.

---

## Quando Aplicar Este Protocolo

| Situação | Aplicar? |
|---|---|
| Novo projeto com captura de lead | **SIM — antes de subir tráfego** |
| Mudança de Pixel (low ticket → high ticket, etc.) | **SIM — re-aplicar fases 1+4** |
| Migração de domínio | **SIM — re-Domain Verification + redeploy** |
| Apenas atualizar criativo de campanha já ativa | NÃO — só fase 4 smoke test |
| Adicionar nova LP no funil existente | PARCIAL — copiar config das LPs ativas + fase 4 |

---

## Referências Cruzadas

- `~/feedback-loop/results.json` — performance real das campanhas após deploy
- `~/cortex/vault/playbooks/playbook-israel-king-trafego.md` — estrutura de campanha Meta
- `~/desafio/cron-monitor.py` — monitor 30min (audiências + domain + lookalike auto)
- `~/.claude/agents/traffic.md` — agente que opera campanhas em cima desse tracking
- Episódios consciousness:
  - `ep_dev_20260507210517` — GA4 from scratch
  - `ep_dev_20260507212517` — Settings + dual-dispatch
  - `ep_dev_20260507221353` — Google Ads end-to-end + GA4↔Ads link

---

## Tempo Total de Implementação (referência DOMINIA, 07-Mai-2026)

| Fase | Tempo |
|---|---|
| FASE 1 (Meta) | 60 min (já existia, ajustes) |
| FASE 2 (GA4 from scratch) | 35 min |
| FASE 3 (Google Ads conta + Conversion + Link) | 45 min |
| FASE 4 (deploy + bug fix + smoke) | 25 min |
| **Total** | **~3h efetivas** (5h corridas com discovery e bug Domain Verification) |

---

## EROS Veredito por implementação

Cada deploy de tracking deve sair com:

```
Completude:  ok — 8 componentes ativos (Pixel, CAPI, GA4 browser/server, gtag conversion, CM, Lookalikes, Domain)
Precisão:    ok — todos IDs validados via curl e smoke test E2E
Qualidade:   ok — dual-dispatch, Enhanced Conversions, dedup via event_id
Coerência:   ok — single event_id atravessa 5 endpoints
Utilidade:   ok — pronto pra subir campanha sem retrabalho
Score: 5/5 | AUTORIZADO
```
