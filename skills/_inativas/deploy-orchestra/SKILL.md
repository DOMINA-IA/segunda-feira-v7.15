---
name: deploy-orchestra
description: "Orquestra deploy dos projetos hospedados na VPS (CLIENTE_EXEMPLO, CLIENTE_EXEMPLO Dashboard, WhatsApp Bot, DOMINA.IA) com health check, rollback automático e notificação no Telegram. Use quando precisar publicar uma atualização em qualquer app da VPS. NOT for: sites estáticos na Hostinger (isso é /deploy-hostinger)."
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

# Deploy Orchestra — Skill de Deploy Unificado

## Contexto

**VPS:** alias `CLIENTE_EXEMPLO` — `ssh CLIENTE_EXEMPLO` (autenticação por chave; sem senha em script)
**SSH:** Via `expect` com senha (sshpass não instalado no Mac)
**Telegram Bot:** WhatsApp Bot na porta 3003 (para notificações)

---

## Regras Invioláveis

1. **SEMPRE fazer health check** após deploy. Se falhar, rollback automático.
2. **NUNCA misturar credenciais** entre projetos (cada um tem seu DB, porta, PM2 name).
3. **SEMPRE salvar hash do commit atual** antes do deploy (para rollback).
4. **Logs de deploy** registrados em `~/framework/observations/deploy-orchestra.log`.
5. **SEMPRE usar acentos e cedilha** em mensagens e logs em português.

---

## Projetos Registrados

| Projeto | Caminho VPS | PM2 Name | Porta | Health Check | DB |
|---------|-------------|----------|-------|-------------|-----|
| CLIENTE_EXEMPLO | `/opt/CLIENTE_EXEMPLO/` | `CLIENTE_EXEMPLO` | 3000 | `curl -s http://localhost:3000/api/health` | `postgresql://${USER}:<senha em ~/_secrets/db-${USER}.env>@localhost:5432/${USER}` |
| CLIENTE_EXEMPLO Dashboard | `/opt/CLIENTE_EXEMPLO-dashboard/` | `CLIENTE_EXEMPLO-dashboard` | 3002 | `curl -s -o /dev/null -w '%{http_code}' http://localhost:3002` | `postgresql://cliente_user:<senha em ~/_secrets/db-cliente_user.env>@localhost:5433/cliente_dashboard` |
| WhatsApp Bot | `/opt/whatsapp-bot/` | `whatsapp-bot` | 3003 | `curl -s http://localhost:3003/api/health` | Mesmo DB do CLIENTE_EXEMPLO |
| DOMINA.IA | `/opt/dominantes/` | `dominantes` | 3004 | `curl -s -o /dev/null -w '%{http_code}' http://localhost:3004` | SQLite local |
| SF Daemon | `/opt/segunda-feira-daemon/` | `segunda-feira-daemon` | 3005 | `curl -s http://localhost:3005/api/health` | Mesmo DB do CLIENTE_EXEMPLO |
| CLIENTE_EXEMPLO Dashboard | `/opt/clienteexemplo-CLIENTE_EXEMPLO-dashboard/` | `clienteexemplo-dashboard` | 3006 | `curl -s -o /dev/null -w '%{http_code}' http://localhost:3006` | Mesmo DB do CLIENTE_EXEMPLO |

### Notas Importantes por Projeto

- **WhatsApp Bot:** Status PM2 = **stopped** (desde 2026-04-03). Não reiniciar sem motivo — auto_reply=false no DB protege, mas prefira manter parado.
- **SF Daemon:** Build requer `cd /opt/segunda-feira-daemon && ./node_modules/.bin/tsc` antes de restart. Canal WhatsApp BLOQUEADO por flag (`CHANNEL_WHATSAPP_ENABLED=false`). NUNCA trocar para true sem implementar allowlist.
- **CLIENTE_EXEMPLO Dashboard:** Instável (86 restarts). Monitorar após deploy.

---

## Comandos

```
/deploy-orchestra CLIENTE_EXEMPLO      → deploy apenas CLIENTE_EXEMPLO
/deploy-orchestra CLIENTE_EXEMPLO            → deploy apenas CLIENTE_EXEMPLO Dashboard
/deploy-orchestra whatsapp       → deploy apenas WhatsApp Bot
/deploy-orchestra dominantes     → deploy apenas DOMINA.IA
/deploy-orchestra daemon         → deploy SF Daemon (build TS + restart)
/deploy-orchestra clienteexemplo            → deploy CLIENTE_EXEMPLO Dashboard
/deploy-orchestra all            → deploy de TODOS (sequencial)
/deploy-orchestra status         → status PM2 de todos os projetos
```

---

## Fluxo de Deploy (por projeto)

### Função SSH Base

Autenticação por chave via alias do `~/.ssh/config` — sem senha, sem `expect`:

```bash
ssh CLIENTE_EXEMPLO 'COMANDOS_AQUI'
```

Bloco de comandos (heredoc):
```bash
ssh CLIENTE_EXEMPLO <<'REMOTE'
  cd /opt/CLIENTE_EXEMPLO
  COMANDOS_AQUI
REMOTE
```

Enviar arquivo: `scp arquivo CLIENTE_EXEMPLO:/opt/CLIENTE_EXEMPLO/`

### PASSO 1 — Salvar Estado Atual (pré-deploy)

```bash
# Dentro da VPS, para cada projeto:
cd /opt/{projeto}
COMMIT_ANTES=$(git rev-parse HEAD)
echo "$COMMIT_ANTES" > /tmp/deploy-rollback-{projeto}.txt
pm2 save
```

### PASSO 2 — Deploy por Projeto

#### CLIENTE_EXEMPLO (`/opt/CLIENTE_EXEMPLO/`)

```bash
cd /opt/CLIENTE_EXEMPLO
git stash  # salvar alterações locais se houver
git pull origin main
npm install --production
npm run build
pm2 restart CLIENTE_EXEMPLO --update-env
sleep 5
# Health check
HEALTH=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/api/health)
if [ "$HEALTH" != "200" ]; then
  echo "FALHA: health check retornou $HEALTH"
  exit 1
fi
echo "CLIENTE_EXEMPLO deployado com sucesso — $(git rev-parse --short HEAD)"
```

#### CLIENTE_EXEMPLO Dashboard (`/opt/CLIENTE_EXEMPLO-dashboard/`)

```bash
cd /opt/CLIENTE_EXEMPLO-dashboard
git stash
git pull origin main
npm install --production
npx next build
pm2 restart CLIENTE_EXEMPLO-dashboard --update-env
sleep 5
HEALTH=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3002)
if [ "$HEALTH" != "200" ]; then
  echo "FALHA: health check retornou $HEALTH"
  exit 1
fi
echo "CLIENTE_EXEMPLO Dashboard deployado com sucesso — $(git rev-parse --short HEAD)"
```

#### WhatsApp Bot (`/opt/whatsapp-bot/`)

```bash
cd /opt/whatsapp-bot
git stash
git pull origin main
npm install --production
pm2 restart whatsapp-bot --update-env
sleep 5
HEALTH=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3003/api/health)
if [ "$HEALTH" != "200" ]; then
  echo "FALHA: health check retornou $HEALTH"
  exit 1
fi
echo "WhatsApp Bot deployado com sucesso — $(git rev-parse --short HEAD)"
```

#### DOMINA.IA (`/opt/dominantes/`)

```bash
cd /opt/dominantes
git stash
git pull origin main
npm install --production
npm run build
pm2 restart dominantes --update-env
sleep 5
HEALTH=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3004)
if [ "$HEALTH" != "200" ]; then
  echo "FALHA: health check retornou $HEALTH"
  exit 1
fi
echo "DOMINA.IA deployado com sucesso — $(git rev-parse --short HEAD)"
```

### PASSO 3 — Health Check Detalhado

```bash
# Após deploy, verificar:
pm2 status  # todos os processos online?
pm2 logs {pm2-name} --lines 10 --nostream  # erros recentes?

# Health check HTTP
for port in 3000 3002 3003 3004; do
  STATUS=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$port)
  echo "Porta $port: HTTP $STATUS"
done
```

**Critérios de sucesso:**
- HTTP 200 no health check
- PM2 status: `online` (não `errored` ou `stopped`)
- Zero erros nos últimos 10 logs

### PASSO 4 — Rollback Automático (se health check falhar)

```bash
cd /opt/{projeto}
COMMIT_ANTERIOR=$(cat /tmp/deploy-rollback-{projeto}.txt)
git checkout $COMMIT_ANTERIOR
npm install --production
npm run build  # se aplicável
pm2 restart {pm2-name} --update-env
sleep 5

# Verificar se rollback funcionou
HEALTH=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:{porta})
if [ "$HEALTH" == "200" ]; then
  echo "ROLLBACK OK — revertido para $COMMIT_ANTERIOR"
else
  echo "ROLLBACK FALHOU — INTERVENÇÃO MANUAL NECESSÁRIA"
fi
```

### PASSO 5 — Notificação (Telegram ou output)

**Deploy OK:**
```
✅ DEPLOY CONCLUÍDO
Projeto: {nome}
Commit: {hash_curto}
Horário: {timestamp BRT}
Health: HTTP 200
```

**Deploy FALHOU:**
```
❌ DEPLOY FALHOU — ROLLBACK EXECUTADO
Projeto: {nome}
Erro: {descrição}
Revertido para: {commit_anterior}
Horário: {timestamp BRT}
Ação: verificar logs com `pm2 logs {pm2-name}`
```

---

## Comando `/deploy-orchestra all`

Execução **sequencial** (não paralela) para evitar sobrecarga na VPS:

```
1. CLIENTE_EXEMPLO     → deploy + health check
2. CLIENTE_EXEMPLO Dashboard → deploy + health check
3. WhatsApp Bot  → deploy + health check
4. DOMINA.IA     → deploy + health check
```

Se qualquer projeto falhar, os demais continuam. Relatório final consolida todos:

```
📊 DEPLOY REPORT — {data}
┌─────────────────┬────────┬──────────┐
│ Projeto         │ Status │ Commit   │
├─────────────────┼────────┼──────────┤
│ CLIENTE_EXEMPLO       │ ✅ OK  │ a1b2c3d  │
│ CLIENTE_EXEMPLO Dashboard   │ ✅ OK  │ e4f5g6h  │
│ WhatsApp Bot    │ ❌ FAIL│ rollback │
│ DOMINA.IA       │ ✅ OK  │ i7j8k9l  │
└─────────────────┴────────┴──────────┘
Tempo total: 3m 42s
```

---

## Comando `/deploy-orchestra status`

Verificar estado atual sem fazer deploy:

```bash
# Via SSH
pm2 jlist  # JSON format
pm2 status  # tabela visual

# Health checks
for port in 3000 3002 3003 3004; do
  curl -s -o /dev/null -w "Porta $port: HTTP %{http_code}\n" http://localhost:$port
done

# Uso de recursos
free -h
df -h /opt
```

---

## Tratamento de Erros

| Erro | Ação |
|------|------|
| SSH timeout | Retry 3x com 10s de intervalo. Se persistir, alertar CEO. |
| `git pull` conflito | `git stash && git pull && git stash pop`. Se falhar, `git reset --hard origin/main`. |
| `npm install` falhou | Limpar cache: `rm -rf node_modules && npm install --production`. |
| `npm run build` falhou | Verificar `pm2 logs`. Rollback imediato. |
| Health check timeout | Esperar mais 10s. Se persistir, rollback. |
| PM2 `errored` | `pm2 logs {name} --lines 50 --nostream` → diagnosticar. |
| Disco cheio | `npm cache clean --force && pm2 flush`. Alertar CEO. |
| Porta ocupada | `lsof -i :{porta}` → identificar processo → matar se não for crítico. |

---

## Observações

```bash
# Registrar cada deploy
mkdir -p ~/observations
echo "[$(date)] deploy-orchestra: {projeto} deployado — commit {hash} — status {ok/fail}" >> ~/framework/observations/deploy-orchestra.log
```

---

## Segurança

- Senha SSH usada via `expect` (não armazenada em plaintext em scripts permanentes)
- Cada projeto tem seu próprio usuário/senha de DB — NUNCA misturar
- Rollback preserva `auth_state/` do WhatsApp Bot (reconexão sem QR code)
- `git stash` antes de pull preserva alterações locais feitas diretamente na VPS
