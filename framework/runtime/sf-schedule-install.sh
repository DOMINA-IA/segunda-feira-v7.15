#!/bin/bash
# =============================================================================
# sf-schedule-install.sh — Renderiza schedule.yaml em systemd units (VPS) e ativa.
#
# Roda NA VPS como root:  bash $HOME/framework/runtime/sf-schedule-install.sh [--dry-run]
# (o sf-sync.sh do Mac já deixou schedule.yaml e este script em /opt/segunda-feira)
#
# O que gera, por job:
#   /etc/systemd/system/sf-<id>.service  (User=${RUN_USER}, HOME=/opt/segunda-feira,
#                                         OnFailure=sf-alert@sf-<id>.service quando alert)
#   /etc/systemd/system/sf-<id>.timer    (OnCalendar=<when>, Persistent=true)
#   ou, para when=daemon, só o .service com Restart=always e WantedBy=multi-user.
# Units sf-* que NÃO estão mais no schedule.yaml são desativadas e removidas
# (é assim que os 7 timers de maio saem de cena sem passo manual).
# =============================================================================
set -euo pipefail
DRY="${1:-}"
SF_HOME="/opt/segunda-feira"
YAML="$SF_HOME/framework/runtime/schedule.yaml"
PY="$SF_HOME/.venv/bin/python3"
UNITS=/etc/systemd/system

[[ -f "$YAML" ]] || { echo "schedule.yaml não encontrado em $YAML"; exit 1; }

# unit de alerta (template): sf-alert@<unit>.service → Telegram via sf-notify.sh + fila do dispatcher
cat > "$UNITS/sf-alert@.service" <<EOF
[Unit]
Description=Segunda-feira — alerta de falha de %i

[Service]
Type=oneshot
User=${RUN_USER}
Environment=HOME=$SF_HOME
Environment=PATH=$SF_HOME/.venv/bin:/usr/local/bin:/usr/bin:/bin
# Entra na FILA do dispatcher (notify() de autonomous/lib/common.sh) — sf-notify.sh era osascript
# de macOS e terminava "success" sem enfileirar nada (auditoria Codex 07-Set, QUEUE_MATCHES []).
# Logica no script sf-alert.sh (systemd expande parametros dentro de ExecStart antes do bash)
ExecStart=/bin/bash $SF_HOME/framework/scripts/sf-alert.sh %i
EOF

"$PY" - "$YAML" "$UNITS" "$SF_HOME" "$DRY" <<'PYEOF'
import sys, yaml, os, subprocess
from pathlib import Path
yml, units, home, dry = sys.argv[1:5]
jobs = yaml.safe_load(open(yml))["jobs"]
units = Path(units)
wanted = set()
for j in jobs:
    uid = f"sf-{j['id']}"; wanted.add(uid)
    run = j["run"].replace("$HOME", home)
    log = j.get("log", f"{j['id']}.log")
    alert = j.get("alert", True)
    timeout = int(j.get("timeout", 1800))
    user = j.get("user", "${RUN_USER}")
    on_fail = f"OnFailure=sf-alert@{uid}.service\n" if alert else ""
    if j["when"] == "daemon":
        svc = f"""[Unit]
Description=Segunda-feira — {j['id']} (daemon) — {j.get('note','')}
After=network-online.target
{on_fail}
[Service]
User={user}
Environment=HOME={home}
Environment=PATH={home}/.venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=TZ=America/Sao_Paulo
WorkingDirectory={home}
ExecStart={run}
Restart=always
RestartSec=30
StandardOutput=append:{home}/logs/{log}
StandardError=append:{home}/logs/{log}

[Install]
WantedBy=multi-user.target
"""
        tmr = None
    else:
        svc = f"""[Unit]
Description=Segunda-feira — {j['id']} — {j.get('note','')}
{on_fail}
[Service]
Type=oneshot
User={user}
Environment=HOME={home}
Environment=PATH={home}/.venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=TZ=America/Sao_Paulo
WorkingDirectory={home}
ExecStart={run}
TimeoutStartSec={timeout}
StandardOutput=append:{home}/logs/{log}
StandardError=append:{home}/logs/{log}
"""
        whens = j["when"] if isinstance(j["when"], list) else [j["when"]]
        oncal = "\n".join(f"OnCalendar={w}" for w in whens)
        tmr = f"""[Unit]
Description=Timer — {j['id']} ({'; '.join(whens)})

[Timer]
{oncal}
Persistent=true
RandomizedDelaySec=20

[Install]
WantedBy=timers.target
"""
    if dry:
        print(f"[dry] {uid}: when={j['when']} run={run}")
        for w in (j["when"] if isinstance(j["when"], list) else [j["when"]]):
            if w != "daemon" and subprocess.run(["systemd-analyze", "calendar", w], capture_output=True).returncode != 0:
                print(f"   ✗ OnCalendar inválido: {w}")
        continue
    (units / f"{uid}.service").write_text(svc)
    if tmr:
        (units / f"{uid}.timer").write_text(tmr)
    elif (units / f"{uid}.timer").exists():
        (units / f"{uid}.timer").unlink()

if not dry:
    # remove units sf-* fora do schedule (os 7 de maio, cortex-sync, etc.)
    for f in units.glob("sf-*.service"):
        name = f.stem
        if name.startswith("sf-alert@") or name in wanted:
            continue
        subprocess.run(["systemctl", "disable", "--now", f"{name}.timer"], capture_output=True)
        subprocess.run(["systemctl", "disable", "--now", f"{name}.service"], capture_output=True)
        f.unlink(missing_ok=True); (units / f"{name}.timer").unlink(missing_ok=True)
        print("removida:", name)
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    for j in jobs:
        uid = f"sf-{j['id']}"
        if j["when"] == "daemon":
            subprocess.run(["systemctl", "enable", "--now", f"{uid}.service"], capture_output=True)
        else:
            subprocess.run(["systemctl", "enable", "--now", f"{uid}.timer"], capture_output=True)
    print(f"{len(jobs)} jobs instalados")
PYEOF

[[ -n "$DRY" ]] && exit 0
mkdir -p "$SF_HOME/logs"; chown -R ${RUN_USER}:${RUN_USER} "$SF_HOME/logs"
systemctl list-timers --all --no-pager 'sf-*' | head -40
echo; systemctl --no-pager --plain list-units 'sf-*.service' | grep -E "failed|active" || true
