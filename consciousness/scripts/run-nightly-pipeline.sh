#!/bin/bash
# Pipeline noturno Segunda-feira — roda assimilação + distribuição + digest Telegram.
# Idempotente: pode ser chamado múltiplas vezes no mesmo dia sem duplicar.

set -u
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

LOG_DIR="$HOME/logs"
STAMP_DIR="$HOME/consciousness/.pipeline-stamps"
mkdir -p "$LOG_DIR" "$STAMP_DIR"

TODAY=$(date +%Y-%m-%d)
STAMP="$STAMP_DIR/pipeline-$TODAY.done"
LOG="$LOG_DIR/nightly-pipeline.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"
}

# ─── LOCK: impede execução dupla ────────────────────────────────────────
# macOS não tem /usr/bin/flock por padrão — usa mkdir (atômico no filesystem)
# como mutex. Protege contra o launchd disparar 2x (ex.: catch-up após o Mac
# acordar de sleep) ou execução manual concorrente com a agendada.
LOCK_DIR="$STAMP_DIR/run-nightly-pipeline.lock"

acquire_lock() {
    if mkdir "$LOCK_DIR" 2>/dev/null; then
        echo "$$" > "$LOCK_DIR/pid"
        trap 'rm -rf "$LOCK_DIR"' EXIT
        return 0
    fi

    # Lock já existe — checar se é de um processo vivo (lock ativo) ou órfão (stale)
    local existing_pid
    existing_pid=$(cat "$LOCK_DIR/pid" 2>/dev/null || echo "")
    if [[ -n "$existing_pid" ]] && kill -0 "$existing_pid" 2>/dev/null; then
        log "Outra execução já em andamento (PID $existing_pid). Abortando esta chamada."
        exit 0
    fi

    # Lock stale (processo não existe mais) — limpar e tentar de novo, uma vez
    log "Lock encontrado sem processo vivo (stale) — removendo e retentando."
    rm -rf "$LOCK_DIR"
    if mkdir "$LOCK_DIR" 2>/dev/null; then
        echo "$$" > "$LOCK_DIR/pid"
        trap 'rm -rf "$LOCK_DIR"' EXIT
        return 0
    fi

    log "Não foi possível adquirir o lock após limpeza. Abortando."
    exit 1
}

acquire_lock

# Skip se já rodou hoje (a menos que --force)
if [[ "${1:-}" != "--force" ]] && [[ -f "$STAMP" ]]; then
    log "Pipeline já rodou hoje ($TODAY). Use --force para rodar novamente."
    exit 0
fi

log "=============================="
log "PIPELINE NOTURNO — iniciado"
log "=============================="

FAILED_STEPS=()

run_step() {
    local name="$1"; shift
    log "[$name] iniciando..."
    if "$@" >>"$LOG" 2>&1; then
        log "[$name] OK"
    else
        log "[$name] FALHOU (exit $?)"
        FAILED_STEPS+=("$name")
    fi
}

# Ordem: ttl → feedback → consolidate → autolink → briefings → digest
run_step "mailbox-ttl" bash "$HOME/broadcast/scripts/mailbox-ttl.sh"
run_step "feedback-to-consciousness" bash "$HOME/consciousness/scripts/feedback-to-consciousness.sh"
run_step "consolidate" bash "$HOME/consciousness/scripts/consolidate.sh"
run_step "auto-link-orphans" python3 "$HOME/cortex/scripts/auto-link-orphans.py"
run_step "build-briefings" bash "$HOME/cortex/scripts/build-briefings.sh"
run_step "nightly-digest" python3 "$HOME/consciousness/scripts/nightly-digest.py"

if [[ ${#FAILED_STEPS[@]} -eq 0 ]]; then
    touch "$STAMP"
    log "PIPELINE COMPLETO — todos os steps OK"

    # Notificação macOS (se disponível)
    if command -v osascript >/dev/null 2>&1; then
        osascript -e 'display notification "Assimilação noturna concluída. Digest enviado via Telegram." with title "Segunda-feira" sound name "Glass"' 2>/dev/null || true
    fi
    exit 0
else
    log "PIPELINE COM FALHAS: ${FAILED_STEPS[*]}"
    # Mandar alerta no Telegram
    TOKEN=$(grep -E '^(TELEGRAM_BOT_TOKEN|BOT_TOKEN)=' "$HOME/.claude/channels/telegram/.env" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
    CHAT=$(python3 -c "import json; print(json.load(open('$HOME/.claude/channels/telegram/access.json'))['allowFrom'][0])" 2>/dev/null)
    if [[ -n "$TOKEN" && -n "$CHAT" ]]; then
        curl -sS --max-time 10 "https://api.telegram.org/bot${TOKEN}/sendMessage" \
            --data-urlencode "chat_id=${CHAT}" \
            --data-urlencode "parse_mode=HTML" \
            --data-urlencode "text=⚠️ <b>Pipeline noturno com falhas</b>%0ASteps: ${FAILED_STEPS[*]}%0AVer log: ~/logs/nightly-pipeline.log" \
            >/dev/null 2>&1
    fi
    exit 1
fi
