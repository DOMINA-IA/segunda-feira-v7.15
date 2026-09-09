#!/bin/bash
# =============================================================================
# sf-sync.sh — Sincroniza o framework entre o Mac (desenvolvimento) e a VPS
# (runtime 24/7). Decisão CEO 05-Set-2026: "alertas e disparos rodam na VPS;
# o Mac fica com o framework todo, só desenvolvimento".
#
# Modelo de escrita (um escritor por diretório — o que faltava em maio):
#   CÓDIGO/CONFIG   Mac → VPS, espelho exato (--delete)
#   ESTADO DERIVADO VPS → Mac, espelho exato (index, briefings, heurísticas…)
#   DOIS ESCRITORES união por id nos dois sentidos (episódios, sinais, mailbox)
#   VAULT/PATTERNS  os dois editam → --update nos dois sentidos (mtime vence),
#                   nunca --delete
#
# A VPS não alcança o Mac; por isso o sync roda SEMPRE a partir do Mac:
#   - launchd a cada 20 min enquanto o Mac está acordado
#   - hook SessionStart (pull rápido) e Stop (push de episódios) do Claude Code
#   - à mão: sf-sync.sh full
#
# Uso: sf-sync.sh push|pull|merge|full|quick   [--dry-run]
# Log: ~/logs/sf-sync.log
# =============================================================================
set -uo pipefail

MODE="${1:-full}"; DRY=""; [[ "${2:-}" == "--dry-run" ]] && DRY="--dry-run"
HOST="CLIENTE_EXEMPLO"                       # alias ssh (root@${VPS_HOST}, chave id_ed25519)
REMOTE_HOME="/opt/segunda-feira"      # HOME do ${RUN_USER}; $HOME é symlink para cá
OWNER="${RUN_USER}:${RUN_USER}"
LOG="$HOME/logs/sf-sync.log"; mkdir -p "$HOME/logs"
MERGE="$HOME/framework/runtime/sync/sf-merge-jsonl.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
RS="rsync -az --timeout=120 $DRY"   # sem --chown: rsync do macOS é 2.6.9; chown via ssh ao final
EXC=(--exclude .git --exclude node_modules --exclude __pycache__ --exclude '*.pyc' --exclude .venv
     --exclude dist-v7.14 --exclude '*.bak*' --exclude .DS_Store --exclude '*.mp4' --exclude '*.mov')

log(){ echo "[$(date +%Y-%m-%dT%H:%M:%S)] $*" >> "$LOG"; }
FALHAS=0
falhou(){ FALHAS=$((FALHAS+1)); say "✗ $*"; }
# rsync -a preserva o UID 501 do Mac, que não existe na VPS: ${RUN_USER} (997) não conseguia
# escrever em signals.json, mailbox e vault (auditoria Codex 07-Set: signal-router 142/147 falhas).
# Corrige o dono ao fim de CADA fase, em qualquer modo.
fix_owner(){
  ssh "$HOST" "chown -R $OWNER $REMOTE_HOME/.claude $REMOTE_HOME/cortex $REMOTE_HOME/consciousness $REMOTE_HOME/brain $REMOTE_HOME/framework $REMOTE_HOME/autonomous $REMOTE_HOME/projetos $REMOTE_HOME/broadcast $REMOTE_HOME/patterns $REMOTE_HOME/feedback-loop $REMOTE_HOME/_secrets $REMOTE_HOME/logs 2>/dev/null; mkdir -p $REMOTE_HOME/autonomous/logs $REMOTE_HOME/autonomous/notifications/pending $REMOTE_HOME/autonomous/notifications/sent && chown -R $OWNER $REMOTE_HOME/autonomous; true" || falhou "chown na VPS"
}
say(){ echo "$*"; log "$*"; }

ssh -o ConnectTimeout=8 -o BatchMode=yes "$HOST" true 2>/dev/null || { say "❌ VPS inacessível — sync abortado"; exit 1; }


# ── 0. INIT: primeira carga do estado Mac → VPS (uma vez; depois a VPS escreve) ──
init_state(){
  say "→ INIT: estado Mac → VPS com --delete (cópia de maio é descartada)"
  for d in consciousness/memory cortex/vault cortex/index cortex/briefings cortex/pulse cortex/reports cortex/decisions \
           cortex/wip cortex/inbox cortex/sessions broadcast/mailbox patterns feedback-loop framework/observations \
           framework/agents/athena; do
    [[ -d "$HOME/$d" ]] || continue
    ssh "$HOST" "mkdir -p $REMOTE_HOME/$d" 2>/dev/null
    $RS --delete "${EXC[@]}" "$HOME/$d/" "$HOST:$REMOTE_HOME/$d/"
  done
  for f in broadcast/signals.json broadcast/_signals-archive.json cortex/heuristics-injected.jsonl cortex/skills-usage.jsonl cortex/sessions.db; do
    [[ -f "$HOME/$f" ]] && $RS "$HOME/$f" "$HOST:$REMOTE_HOME/$f"
  done
  ssh "$HOST" "chown -R $OWNER $REMOTE_HOME/consciousness $REMOTE_HOME/cortex $REMOTE_HOME/broadcast $REMOTE_HOME/patterns $REMOTE_HOME/feedback-loop $REMOTE_HOME/framework $REMOTE_HOME/autonomous 2>/dev/null; true"
}

# ── 1. CÓDIGO/CONFIG: Mac → VPS (espelho) ─────────────────────────────────────
push_code(){
  say "→ push código/config"
  # .claude: só a camada de configuração (nunca projects/, history, credenciais)
  for d in agents skills rules commands hooks; do
    $RS --delete "${EXC[@]}" "$HOME/.claude/$d/" "$HOST:$REMOTE_HOME/.claude/$d/"
  done
  $RS "$HOME/.claude/CLAUDE.md" "$HOME/.claude/settings.json" "$HOST:$REMOTE_HOME/.claude/"
  # núcleo do framework
  for d in cortex/scripts cortex/templates consciousness/scripts brain framework/scripts framework/tests \
           framework/runtime framework/agents/athena/scripts autonomous/health \
           autonomous/knowledge-broker autonomous/weekly-report autonomous/dashboard autonomous/lib autonomous/ledger \
           projetos/utm-manager projetos/desafio projetos/${REDIGIDO} projetos/telegram-scraper; do
    [[ -d "$HOME/$d" ]] || continue
    ssh "$HOST" "mkdir -p $REMOTE_HOME/$d && chown -R $OWNER $REMOTE_HOME/$(dirname "$d")" 2>/dev/null
    $RS --delete "${EXC[@]}" --exclude 'data/' --exclude 'logs/' --exclude 'output/' --exclude 'pixel-rk-*' "$HOME/$d/" "$HOST:$REMOTE_HOME/$d/" || falhou "push $d"
  done
  # dispatcher.sh é código; pending/ e sent/ são estado da VPS (sem --delete)
  $RS "$HOME/autonomous/notifications/dispatcher.sh" "$HOST:$REMOTE_HOME/autonomous/notifications/" || falhou "push dispatcher"
  for f in broadcast/send-mail.sh broadcast/check-mail.sh broadcast/consume-signal.sh broadcast/emit-signal.sh \
           broadcast/agent-boot-context.sh broadcast/signal-router.py broadcast/SIGNAL-TYPES.md cortex/CORTEX.md; do
    [[ -f "$HOME/$f" ]] && $RS "$HOME/$f" "$HOST:$REMOTE_HOME/$f"
  done
  $RS --delete "$HOME/broadcast/scripts/" "$HOST:$REMOTE_HOME/broadcast/scripts/"
  # segredos que o runtime consome (600) — só os .env, nunca chaves ssh/recovery codes
  ssh "$HOST" "mkdir -p $REMOTE_HOME/_secrets && chmod 700 $REMOTE_HOME/_secrets && chown $OWNER $REMOTE_HOME/_secrets"
  $RS --perms --chmod=u=rw,g=,o= --exclude 'vps-CLIENTE_EXEMPLO.env' --include '*.env' --exclude '*' "$HOME/_secrets/" "$HOST:$REMOTE_HOME/_secrets/"
  for e in projetos/utm-manager/.env projetos/desafio/.env projetos/${REDIGIDO}/.env autonomous/.env projetos/telegram-scraper/.env; do
    [[ -f "$HOME/$e" ]] && $RS --perms --chmod=u=rw,g=,o= "$HOME/$e" "$HOST:$REMOTE_HOME/$e"
  done
  # ligações que scripts esperam
  ssh "$HOST" "chown -R $OWNER $REMOTE_HOME/.claude $REMOTE_HOME/cortex $REMOTE_HOME/consciousness $REMOTE_HOME/brain $REMOTE_HOME/framework $REMOTE_HOME/autonomous $REMOTE_HOME/projetos $REMOTE_HOME/broadcast $REMOTE_HOME/_secrets 2>/dev/null; true"
  ssh "$HOST" "cd $REMOTE_HOME && [ -e people-ops ] || ln -s framework/agents/athena people-ops; [ -e AGENTS.md ] || ln -s .claude/CLAUDE.md AGENTS.md; mkdir -p logs feedback-loop patterns && chown -R $OWNER $REMOTE_HOME/logs $REMOTE_HOME/feedback-loop $REMOTE_HOME/patterns"
}

# ── 2. DOIS ESCRITORES: união por id ──────────────────────────────────────────
merge_state(){
  say "→ merge episódios/sinais/mailbox"
  mkdir -p "$TMP/r/episodic" "$TMP/r/mailbox" "$TMP/m/episodic" "$TMP/m/mailbox"
  rsync -az --timeout=60 "$HOST:$REMOTE_HOME/consciousness/memory/episodic/" "$TMP/r/episodic/" 2>/dev/null || falhou "rsync episódios da VPS"
  rsync -az --timeout=60 "$HOST:$REMOTE_HOME/broadcast/mailbox/" "$TMP/r/mailbox/" 2>/dev/null
  rsync -az --timeout=60 "$HOST:$REMOTE_HOME/broadcast/signals.json" "$TMP/r/signals.json" 2>/dev/null
  rsync -az --timeout=60 "$HOST:$REMOTE_HOME/cortex/heuristics-injected.jsonl" "$TMP/r/heuristics-injected.jsonl" 2>/dev/null
  # episódios
  for f in "$HOME"/consciousness/memory/episodic/*.jsonl "$TMP"/r/episodic/*.jsonl; do
    [[ -f "$f" ]] || continue; n=$(basename "$f")
    [[ -f "$TMP/m/episodic/$n" ]] && continue
    python3 "$MERGE" jsonl "$HOME/consciousness/memory/episodic/$n" "$TMP/r/episodic/$n" "$TMP/m/episodic/$n" || falhou "merge episódio $n (rc=$?)"
  done
  # mailbox (só .json de agente)
  for f in "$HOME"/broadcast/mailbox/*.json "$TMP"/r/mailbox/*.json; do
    [[ -f "$f" ]] || continue; n=$(basename "$f")
    [[ -f "$TMP/m/mailbox/$n" ]] && continue
    python3 "$MERGE" mailbox "$HOME/broadcast/mailbox/$n" "$TMP/r/mailbox/$n" "$TMP/m/mailbox/$n"
  done
  python3 "$MERGE" signals "$HOME/broadcast/signals.json" "$TMP/r/signals.json" "$TMP/m/signals.json"
  python3 "$MERGE" jsonl "$HOME/cortex/heuristics-injected.jsonl" "$TMP/r/heuristics-injected.jsonl" "$TMP/m/heuristics-injected.jsonl"
  if [[ -z "$DRY" ]]; then
    cp "$TMP"/m/episodic/*.jsonl "$HOME/consciousness/memory/episodic/" 2>/dev/null
    cp "$TMP"/m/mailbox/*.json "$HOME/broadcast/mailbox/" 2>/dev/null
    cp "$TMP/m/signals.json" "$HOME/broadcast/signals.json"
    cp "$TMP/m/heuristics-injected.jsonl" "$HOME/cortex/heuristics-injected.jsonl"
    $RS "$TMP/m/episodic/" "$HOST:$REMOTE_HOME/consciousness/memory/episodic/"
    $RS "$TMP/m/mailbox/" "$HOST:$REMOTE_HOME/broadcast/mailbox/"
    $RS "$TMP/m/signals.json" "$HOST:$REMOTE_HOME/broadcast/signals.json"
    $RS "$TMP/m/heuristics-injected.jsonl" "$HOST:$REMOTE_HOME/cortex/heuristics-injected.jsonl"
  fi
}

# ── 3. VAULT/PATTERNS/FEEDBACK: dois editores, mtime vence, nunca apaga ───────
sync_vault(){
  say "→ vault/patterns/feedback-loop (--update, dois sentidos)"
  for d in cortex/vault patterns feedback-loop framework/observations/evolucao; do
    ssh "$HOST" "mkdir -p $REMOTE_HOME/$d" 2>/dev/null
    $RS --update "${EXC[@]}" "$HOME/$d/" "$HOST:$REMOTE_HOME/$d/"
    rsync -az --update --timeout=120 "${EXC[@]}" "$HOST:$REMOTE_HOME/$d/" "$HOME/$d/" $DRY
  done
}

sync_evolucao(){
  local d=framework/observations/evolucao
  ssh "$HOST" "mkdir -p $REMOTE_HOME/$d" 2>/dev/null
  $RS --update "${EXC[@]}" "$HOME/$d/" "$HOST:$REMOTE_HOME/$d/"
  rsync -az --update --timeout=120 "${EXC[@]}" "$HOST:$REMOTE_HOME/$d/" "$HOME/$d/" $DRY
}

# ── 4. ESTADO DERIVADO: VPS → Mac (espelho; a VPS é o único escritor) ─────────
pull_state(){
  say "← pull estado derivado da VPS"
  for d in consciousness/memory/procedural consciousness/memory/semantic consciousness/memory/consolidation \
           consciousness/memory/prospective cortex/index cortex/briefings cortex/pulse cortex/reports \
           cortex/decisions cortex/wip cortex/inbox framework/observations framework/agents/athena/daily \
           framework/agents/athena/dormancy autonomous/logs; do
    ssh "$HOST" "test -d $REMOTE_HOME/$d" 2>/dev/null || continue
    mkdir -p "$HOME/$d"
    case "$d" in
      cortex/index|cortex/briefings)
        # índice/briefings são gerados na VPS com HOME=/opt/segunda-feira: normalizar em área
        # temporária ANTES de entrar no lugar — o router leu o índice na janela entre o rsync e
        # o sed e injetou paths /opt na sessão (07-Set, segunda vez)
        rm -rf "$TMP/pull-$$"; mkdir -p "$TMP/pull-$$"
        rsync -az --delete --timeout=120 "${EXC[@]}" "$HOST:$REMOTE_HOME/$d/" "$TMP/pull-$$/" $DRY || falhou "pull $d"
        [[ -z "$DRY" ]] && grep -rl "/opt/segunda-feira" "$TMP/pull-$$" 2>/dev/null | while read -r f; do sed -i '' "s#/opt/segunda-feira#$HOME#g" "$f"; done
        [[ -z "$DRY" ]] && rsync -a --delete "$TMP/pull-$$/" "$HOME/$d/"
        ;;
      framework/observations)
        # evolucao/ é escrito nos DOIS lados (ciclo roda no Mac ou na VPS; adoção marca no Mac):
        # fica fora do espelho com --delete (07-Set: o pull apagou a pasta do ciclo em andamento)
        rsync -az --delete --timeout=120 "${EXC[@]}" --exclude 'evolucao/' "$HOST:$REMOTE_HOME/$d/" "$HOME/$d/" $DRY || falhou "pull $d"
        ;;
      *)
        rsync -az --delete --timeout=120 "${EXC[@]}" "$HOST:$REMOTE_HOME/$d/" "$HOME/$d/" $DRY || falhou "pull $d"
        ;;
    esac
  done
  # Ciclo de Evolução — ciclo semanal no Mac (tem transcripts: uso real e correções do CEO), em
  # background e com lock; a VPS também tenta no domingo, se o claude estiver logado lá.
  if [[ -z "$DRY" ]]; then
    EV="$HOME/framework/observations/evolucao"; mkdir -p "$EV"
    ULT=$(python3 -c "import json;print(json.load(open('$EV/estado.json')).get('ultimo_ciclo_ts',0))" 2>/dev/null || echo 0)
    if (( $(date +%s) - ${ULT:-0} > 7*86400 )) && ! [[ -f "$EV/.ciclo.lock" ]]; then
      touch "$EV/.ciclo.lock"
      ( bash "$HOME/framework/runtime/evolucao/sf-evolucao.sh" ciclo >/dev/null 2>&1; rm -f "$EV/.ciclo.lock" ) &
      log "ciclo de evolução disparado em background (último há >7d)"
    fi
  fi
  # Ciclo de Evolução: adota no Mac o que já pode (só após N ciclos aprovados à mão; risco baixo)
  [[ -z "$DRY" && -f "$HOME/framework/runtime/evolucao/pipeline.py" ]] && python3 "$HOME/framework/runtime/evolucao/pipeline.py" aplicar-aprovados 2>>"$LOG" || true
  mkdir -p "$HOME/logs/vps"
  rsync -az --timeout=60 --include '*.log' --exclude '*' "$HOST:$REMOTE_HOME/logs/" "$HOME/logs/vps/" $DRY
}

case "$MODE" in
  push)  push_code; fix_owner ;;
  pull)  pull_state ;;
  merge) merge_state; fix_owner ;;
  quick) merge_state; sync_evolucao; fix_owner; pull_state ;;
  full)  push_code; merge_state; sync_vault; fix_owner; pull_state ;;
  init)  push_code; init_state; fix_owner ;;
  *) echo "uso: sf-sync.sh init|push|pull|merge|quick|full [--dry-run]"; exit 2 ;;
esac
if [[ "$FALHAS" -gt 0 ]]; then say "✗ sf-sync $MODE terminou com $FALHAS falha(s) — ver $LOG"; exit 1; fi
say "✓ sf-sync $MODE concluído"
