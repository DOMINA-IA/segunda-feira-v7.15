#!/usr/bin/env bash
# preload.sh — Cache warming dos top N agentes do dia
# Origem: ruflo worker `preload` + ScheduleWakeup 270s pattern.
#
# Uso:
#   preload.sh --top 5                  # warm top 5 baseado em CORTEX Predict
#   preload.sh --agents @dev,@content   # warm específicos
#   preload.sh --daemon                  # loop com ScheduleWakeup 270s
#   preload.sh --status                  # estado atual
#   preload.sh --stop                    # para daemon

set -uo pipefail

CMD="warm"
TOP=5
AGENTS=""
PIDFILE="$HOME/.claude/.preload.pid"
LOGFILE="$HOME/.claude/logs/preload.log"
mkdir -p "$(dirname $LOGFILE)"

while [ $# -gt 0 ]; do
  case "$1" in
    --top) TOP="$2"; shift 2 ;;
    --top=*) TOP="${1#--top=}"; shift ;;
    --agents) AGENTS="$2"; shift 2 ;;
    --agents=*) AGENTS="${1#--agents=}"; shift ;;
    --daemon) CMD="daemon"; shift ;;
    --status) CMD="status"; shift ;;
    --stop) CMD="stop"; shift ;;
    *) shift ;;
  esac
done

now_ts() { date "+%Y-%m-%d %H:%M:%S"; }

log() {
  echo "[$(now_ts)] $1" | tee -a "$LOGFILE"
}

predict_top() {
  # Simples: usa briefings mais usados nos últimos episódios
  if [ -d "$HOME/consciousness/memory/episodic" ]; then
    ls -1t "$HOME/consciousness/memory/episodic"/*.jsonl 2>/dev/null | \
      head -"$TOP" | xargs -n1 basename | sed 's/.jsonl//'
  else
    echo -e "dev\ncontent\ntraffic\narchitect\nqa"
  fi
}

warm_agent() {
  local agent="$1"
  local briefing="$HOME/cortex/briefings/meta/${agent}.md"
  if [ ! -f "$briefing" ]; then
    briefing="$HOME/cortex/briefings/ops/${agent}.md"
  fi
  if [ -f "$briefing" ]; then
    # Touch para atualizar mtime (sinaliza que foi acessado)
    # Em produção real, isso seria uma chamada Haiku com NoOp para esquentar cache do prefixo
    cat "$briefing" > /dev/null
    log "warmed: $agent ($(wc -l < $briefing | tr -d ' ') linhas)"
    return 0
  else
    log "no briefing: $agent"
    return 1
  fi
}

case "$CMD" in
  warm)
    log "=== Preload ciclo único — TOP=$TOP ==="
    if [ -n "$AGENTS" ]; then
      IFS=',' read -ra arr <<< "$AGENTS"
      for a in "${arr[@]}"; do
        a="${a#@}"; a="${a// /}"
        warm_agent "$a" || true
      done
    else
      while IFS= read -r a; do
        warm_agent "$a" || true
      done < <(predict_top)
    fi
    ;;
  daemon)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then
      echo "Daemon já rodando: $(cat $PIDFILE)"
      exit 1
    fi
    log "=== Daemon preload iniciado (ciclo 270s) ==="
    (
      while true; do
        if [ -n "$AGENTS" ]; then
          IFS=',' read -ra arr <<< "$AGENTS"
          for a in "${arr[@]}"; do
            a="${a#@}"; a="${a// /}"
            warm_agent "$a" || true
          done
        else
          while IFS= read -r a; do
            warm_agent "$a" || true
          done < <(predict_top)
        fi
        sleep 270  # janela cache Anthropic
      done
    ) &
    echo $! > "$PIDFILE"
    log "daemon pid: $(cat $PIDFILE)"
    ;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then
      echo "✓ Daemon rodando: pid $(cat $PIDFILE)"
      echo "  Últimas 10 warm-ups:"
      tail -10 "$LOGFILE" 2>/dev/null
    else
      echo "✗ Daemon não está rodando"
    fi
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      pid=$(cat "$PIDFILE")
      if kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        rm -f "$PIDFILE"
        log "=== Daemon parado (pid $pid) ==="
      else
        echo "PIDFILE existe mas processo não — removendo"
        rm -f "$PIDFILE"
      fi
    else
      echo "Sem PIDFILE — daemon não estava rodando"
    fi
    ;;
esac
