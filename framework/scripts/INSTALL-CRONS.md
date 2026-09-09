# INSTALL-CRONS.md — Cron Jobs do Framework Segunda-feira

> Instruções para instalação de cron jobs. Execute `crontab -e` e adicione as linhas abaixo.

---

## Weekly Sync — Segunda 09:00

Consolida estado semanal de todos os agentes e gera scorecard executivo.

```cron
0 9 * * 1 /bin/bash $HOME/framework/scripts/weekly-sync.sh >> $HOME/logs/weekly-sync.log 2>&1
```

**Verificar:** `tail -f ~/logs/weekly-sync.log`
**Output:** `~/docs/weekly-sync/YYYY-WXX.md`

---

## Daily Scan — Todos os dias 09:00

Análise automática diária de campanhas, sinais, mailboxes e oportunidades.

```cron
0 9 * * * /bin/bash $HOME/framework/scripts/daily-scan.sh >> $HOME/logs/daily-scan.log 2>&1
```

**O que faz:**
- Verifica saúde dos componentes do framework (feedback-loop, signals, patterns)
- Analisa results.json por anomalias (CPL alto, CTR baixo, LP drop)
- Verifica sinais não consumidos (>24h) e mailboxes com mensagens antigas (>48h)
- Gera relatório em `~/observations/daily-scan-YYYY-MM-DD.md`
- Se anomalia crítica: emite sinal `DAILY_SCAN_ALERT` no broadcast
- Adiciona novas oportunidades ao `opportunities.md` (sem sobrescrever)

**Verificar:** `tail -f ~/logs/daily-scan.log`
**Output:** `~/observations/daily-scan-YYYY-MM-DD.md`

**Testar manualmente:**
```bash
/bin/bash $HOME/framework/scripts/daily-scan.sh
```

### Nota macOS

O macOS pode pedir permissão de "Full Disk Access" para o cron.
Se o cron não rodar:
1. Abrir System Settings > Privacy & Security > Full Disk Access
2. Adicionar `/usr/sbin/cron` (pode precisar de Command+Shift+G para navegar)

### Alternativa: launchd (nativo macOS)

```bash
cat > ~/Library/LaunchAgents/com.segundafeira.daily-scan.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.segundafeira.daily-scan</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$HOME/framework/scripts/daily-scan.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$HOME/logs/daily-scan.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/logs/daily-scan.log</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.segundafeira.daily-scan.plist
launchctl list | grep segundafeira
```

Para descarregar: `launchctl unload ~/Library/LaunchAgents/com.segundafeira.daily-scan.plist`

---

## Magic Docs Auto-Update — Diário 23:00

Atualiza automaticamente business-state.md e decisions-log.md com dados reais do feedback loop, sinais ativos e mailboxes. Gera snapshot diário.

```cron
0 23 * * * /bin/bash $HOME/framework/scripts/magic-docs-update.sh >> $HOME/logs/magic-docs.log 2>&1
```

**O que faz:**
- Lê results.json e extrai métricas: spend, leads, CPL, CTR, campanhas ativas, melhor campanha
- Lê signals.json e lista sinais ativos
- Conta mensagens não lidas nas mailboxes
- Atualiza seções de métricas do business-state.md (NÃO sobrescreve conteúdo manual)
- Registra decisões automáticas (council_decision, PROACTIVE_ACTION) no decisions-log.md
- Gera snapshot diário em `~/docs/snapshots/YYYY-MM-DD.json`
- Calcula health score (0-100)

**Verificar:** `tail -f ~/logs/magic-docs.log`
**Output:** `~/docs/business-state.md` + `~/docs/decisions-log.md` + `~/docs/snapshots/YYYY-MM-DD.json`

**Testar manualmente:**
```bash
/bin/bash $HOME/framework/scripts/magic-docs-update.sh
```

### Alternativa: launchd (nativo macOS)

```bash
cat > ~/Library/LaunchAgents/com.segundafeira.magic-docs.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.segundafeira.magic-docs</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$HOME/framework/scripts/magic-docs-update.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>23</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$HOME/logs/magic-docs.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/logs/magic-docs.log</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.segundafeira.magic-docs.plist
launchctl list | grep segundafeira
```

Para descarregar: `launchctl unload ~/Library/LaunchAgents/com.segundafeira.magic-docs.plist`

---

## Feed Results — Importação Manual de Resultados

Script para importar dados no feedback loop (`~/feedback-loop/results.json`). Aceita 5 subcomandos.

**Localização:** `~/scripts/feed-results.sh`

### Subcomandos

#### campaign — Adicionar/atualizar campanha Meta Ads

```bash
bash ~/scripts/feed-results.sh campaign \
  --name "AIF-V2-TESTE" \
  --status "active" \
  --spend 50.00 \
  --impressions 5000 \
  --clicks 150 \
  --ctr 3.0 \
  --leads 5 \
  --cpl 10.00 \
  --angle "Sobrecarregado" \
  --lp "LPA" \
  --notes "Teste angulo novo"
```

Opções opcionais: `--id`, `--platform`, `--angle`, `--lp`, `--notes`
Calcula automaticamente: CPC, CTR (se clicks+impressions), CPL (se spend+leads)
Idempotente por `--name` (atualiza se já existe)

#### content — Adicionar post Instagram

```bash
bash ~/scripts/feed-results.sh content \
  --type "reel" \
  --hook "R\$3K a R\$30K com IA" \
  --angle "dinheiro" \
  --reach 5000 \
  --likes 200 \
  --comments 30 \
  --shares 50 \
  --saves 80 \
  --engagement 5.2
```

Opções opcionais: `--impressions`, `--watch-time`, `--retention`, `--follows`, `--notes`
Calcula automaticamente: engagement_rate (se reach + interações)
Idempotente por `--hook` + data (mesmo dia)

#### whatsapp — Adicionar sequência WhatsApp

```bash
bash ~/scripts/feed-results.sh whatsapp \
  --name "Reativacao MI" \
  --sent 603 \
  --delivered 580 \
  --read 400 \
  --replied 50 \
  --converted 10
```

Opções opcionais: `--clicked`, `--notes`
Calcula automaticamente: delivery_rate, read_rate, reply_rate, conversion_rate
Idempotente por `--name` (atualiza se já existe)

#### sales — Adicionar venda

```bash
bash ~/scripts/feed-results.sh sales \
  --product "Comunidade DOMINA.IA" \
  --revenue 7970 \
  --source "meta_ads" \
  --status "paid"
```

Opções opcionais: `--quantity`, `--campaign`, `--payment`, `--ticket`, `--notes`
Calcula automaticamente: ticket (revenue/quantity), summary (total_revenue, avg_ticket, best_source, best_product, refund_rate)

#### summary — Resumo do feedback loop

```bash
bash ~/scripts/feed-results.sh summary
```

Read-only. Mostra resumo de todas as seções com métricas agregadas.

### Comportamento

- Gera ID automático (`entry_{timestamp}`)
- Adiciona data atual
- Valida que campos numéricos são numéricos
- Preserva dados existentes (merge, não sobrescreve)
- Emite sinal `FEEDBACK_UPDATED` no broadcast após cada inserção
- Requer `python3`
