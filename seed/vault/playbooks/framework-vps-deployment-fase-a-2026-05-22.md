---
id: framework-vps-deployment-fase-a-2026-05-22
title: Framework Segunda-feira — Deploy Fase A em VPS (22-Mai-2026)
type: playbook
status: active
created: '2026-05-22'
last_verified: '2026-05-22'
domain:
- infra
- devops
- framework
agents:
- devops
- dev
- sf-master
- people-ops
tags:
- vps
- deploy
- systemd
- segunda-feira
- cortex
- consciousness
- migration
decay_rate: 0.02
links:
- target: vps-principal
  type: parent
- target: automacoes-vps
  type: related
- target: cortex-system
  type: related
- target: CLIENTE_EXEMPLO-licoes-aprendidas
  type: related
- target: segunda-feira-upgrade-multi-ia-orchestrator-2026-05-22
  type: related
- target: framework-optimization-roadmap
  type: related
- target: CLIENTE_EXEMPLO-hardening-2026-05-09
  type: related
- target: lp-r1-tracking-fix-2026-05-05
  type: related
- target: segunda-feira-v7-5-consolida-o-total
  type: related
- target: paperclip-patterns-absorvidos-story-epic-1
  type: related
axis: meta
---

# Playbook — Deploy Framework Segunda-feira na VPS (Fase A)

## Contexto

Em 22-Mai-2026 o framework Segunda-feira ficou disponível na VPS principal (`${VPS_HOST}`). Antes desta data **toda a inteligência rodava no Mac local** — se o Mac desligasse, parava.

Esta nota documenta o processo para reproduzir o deploy, expandir para Fase B/C/D, ou reverter.

## Arquitetura resultante

```
Mac local                                         VPS ${VPS_HOST}
─────────                                         ─────────────────
~/cortex/                                         /opt/segunda-feira/
~/consciousness/   ───── rsync nightly ──→        ├── cortex/
~/broadcast/                                      ├── consciousness/
                                                  ├── broadcast/
                                                  ├── scripts/
                                                  └── .venv/  ← Python isolado

Sync via cortex-sync.sh:                          /opt/segunda-feira-mirror/
                   ───── espelho read-only ──→    └── (snapshot Mac)

7 systemd timers (${RUN_USER} user):
  sf-mailbox-ttl       (02:20)
  sf-feedback-to-conscience (02:25)
  sf-consolidate       (02:30)
  sf-auto-link-orphans (23:30)
  sf-build-briefings   (23:35)
  sf-cortex-sync       (23:45)
  sf-signal-router     (*/15min)
```

## Passos do deploy

Pacote em `~/segunda-feira-vps-deploy/`:
- `deploy.sh` (4.4 KB) — idempotente, reversível com `--uninstall`
- `payload.tar.gz` (3.4 MB) — vault CORTEX + consciousness + scripts
- `systemd/` — 7 .service + 7 .timer
- `README.md` — instruções

### 1. Upload via SFTP (paramiko)
```python
import paramiko
key = paramiko.Ed25519Key.from_private_key_file("~/.ssh/id_ed25519")
t = paramiko.Transport(('${VPS_HOST}', 22))
t.connect(username='root', pkey=key)
sftp = paramiko.SFTPClient.from_transport(t)
# upload deploy.sh, payload.tar.gz, systemd/*
```

### 2. Executar deploy.sh na VPS
```bash
ssh root@${VPS_HOST}
cd /root/sf-deploy
chmod +x deploy.sh && bash deploy.sh
```

O script é idempotente:
- `apt install python3-venv rsync jq logrotate` (skip se já instalado)
- `useradd ${RUN_USER}` (skip se já existe)
- `tar -xzf payload.tar.gz -C /opt/segunda-feira/`
- `sed -i 's|$HOME|/opt/segunda-feira|g' nos scripts (NECESSÁRIO pois scripts usam paths absolutos do Mac)
- `python3 -m venv .venv && pip install pyyaml requests paramiko python-telegram-bot`
- `cp systemd/*.{service,timer} /etc/systemd/system/`
- `systemctl daemon-reload && systemctl enable --now sf-*.timer`
- Smoke test: `cortex_engine.py health`
- logrotate em `/var/log/segunda-feira/*.log`

### 3. Validar
```bash
systemctl list-timers 'sf-*'
journalctl -fu sf-consolidate
sudo -u ${RUN_USER} /opt/segunda-feira/.venv/bin/python3 /opt/segunda-feira/cortex/scripts/cortex_engine.py health
```

### 4. Comentar crons locais migrados (no Mac)
```bash
crontab -l > /tmp/crontab-pre-migration-$(date +%Y%m%d-%H%M).backup
crontab -l | sed -E 's|^([^#].*mailbox-ttl\.sh\|.*feedback-to-conscience\|.*consolidate\.sh\|.*auto-link-orphans\.py\|.*build-briefings\.sh\|.*cortex-sync\.sh\|.*signal-router\.py).*$|# MIGRATED-TO-VPS-2026-05-22: \1|' | crontab -
```

## Reverter

```bash
ssh root@${VPS_HOST}
bash /root/sf-deploy/deploy.sh --uninstall
# Para todos timers, remove units, ARQUIVA dados em /opt/segunda-feira-backup-<timestamp>/
```

No Mac:
```bash
# Re-ativar crons locais
sed -i '' 's|^# MIGRATED-TO-VPS-2026-05-22: ||' <(crontab -l) | crontab -
```

## Heurísticas críticas aprendidas

1. **Paths absolutos `/Users/...` quebram em VPS.** Sempre fazer sed reescrita no deploy. Solução melhor: scripts usarem `$HOME` ou path relativo via `$SF_HOME`.

2. **`agents:` em YAML deve ser lista YAML real, não string única.** Notas com `agents:\n- dev,content` geram chaves Python inválidas em `agents-scope.json`. Guard regex `^[a-z][a-z0-9-]*$` adicionado em `cortex_engine.py:583` previne briefings com nomes inválidos.

3. **`segunda-feira-daemon` (Node Express porta 3005) é DIFERENTE de `/opt/segunda-feira/`.** Daemon = bot Telegram/Discord. Framework = runtime de timers. Não confundir.

4. **`/opt/segunda-feira-mirror/` JÁ existia antes do deploy.** É espelho read-only do Mac via `cortex-sync.sh`. Não tocar. Runtime usa `/opt/segunda-feira/` separado.

5. **Multi-tenant VPS:** uma só máquina hospeda DOMINA.IA + clientes (CLIENTE_EXEMPLO, CLIENTE_EXEMPLO_2, CLIENTE_EXEMPLO, CLIENTE_EXEMPLO, CLIENTE_EXEMPLO, Dominantes). Cada app PM2 com user dedicado quando possível (CLIENTE_EXEMPLO_2 usa user `CLIENTE_EXEMPLO`, Segunda-feira usa `${RUN_USER}`).

6. **Senha em texto plano no MEMORY é anti-pattern.** Vazou tempo nessa operação porque senha estava desatualizada em nota. Solução: referência a 1Password apenas.

## Fases futuras

| Fase | Escopo | Bloqueio |
|------|--------|----------|
| **A (FEITA)** | CORTEX + Consciousness + Broadcast — 7 timers | ✅ DONE |
| **B** | Crons com credenciais externas: cost-watchdog, daily-digest Telegram, meta-smoke, notifications/dispatcher, approvals/engine | Precisa `.env` transferido + credenciais Meta/Telegram |
| **C** | Autonomous suite: health, auto-fix, watchdogs, anomaly, smoke-tests, knowledge-broker, self-critique, weekly-report — 9 timers | Sem bloqueio técnico, escopo ~3h |
| **D** | Daemon `brain/brainstem/heartbeat` (Type=simple, autorestart) | Definir como integra com segunda-feira-daemon existente (porta 3005) |

## Métricas pós-deploy

- 871 notas CORTEX espelhadas (vault completo)
- 49 briefings gerados pela VPS (idêntico ao Mac)
- 7 timers + 7 services systemd ativos
- 0 falhas no smoke test
- Health VPS = Health Mac = 95.5%
- Reverter em 1 comando (uninstall mantém backup)
- 68 MB de footprint em /opt/segunda-feira/

## Conexão programática Mac → VPS

```python
import paramiko
key = paramiko.Ed25519Key.from_private_key_file("~/.ssh/id_ed25519")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('${VPS_HOST}', username='root', pkey=key,
          look_for_keys=False, allow_agent=False)
stdin, stdout, stderr = c.exec_command("systemctl list-timers 'sf-*'")
print(stdout.read().decode())
```