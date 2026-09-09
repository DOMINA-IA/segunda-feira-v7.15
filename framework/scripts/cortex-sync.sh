#!/bin/bash
# =============================================================================
# cortex-sync.sh — Mirror Mac → VPS CLIENTE_EXEMPLO (unidirecional, source of truth = Mac).
#
# Sincroniza CORTEX + agentes + skills + rules + memory + patterns + feedback
# para /opt/segunda-feira-mirror/ na VPS clienteexemplo. Não puxa de volta automático.
#
# Restauração manual: ~/scripts/cortex-restore.sh
# Cron sugerido: 0 3 * * *  (diariamente 03:00 BRT, após pipeline noturno)
# =============================================================================

set -uo pipefail

VPS_HOST="root@${VPS_HOST}"
VPS_DEST="/opt/segunda-feira-mirror"
LOG_DIR="$HOME/logs"
mkdir -p "$LOG_DIR"

TS=$(date +%Y-%m-%d_%H:%M:%S)
echo "════════════════════════════════════════════════"
echo " CORTEX SYNC — $TS"
echo " Mac → $VPS_HOST:$VPS_DEST"
echo "════════════════════════════════════════════════"

# Garantir destino existe
ssh -o ConnectTimeout=10 "$VPS_HOST" "mkdir -p $VPS_DEST/{cortex,claude/agents,claude/skills,claude/rules,claude/projects-memory,consciousness,patterns,feedback-loop}" 2>&1 || {
  echo "❌ SSH falhou — abortando"
  exit 1
}

RSYNC_OPTS="-avz --delete --human-readable"

sync_one() {
  local label="$1"
  local src="$2"
  local dst="$3"
  echo ""
  echo "→ $label"
  rsync $RSYNC_OPTS "$src" "$VPS_HOST:$dst" 2>&1 | tail -3
}

# ── CORTEX (vault + briefings + index — IGNORE inbox/decisions/sessions/pulse/wip)
sync_one "CORTEX vault" "$HOME/cortex/vault/" "$VPS_DEST/cortex/vault/"
sync_one "CORTEX briefings" "$HOME/cortex/briefings/" "$VPS_DEST/cortex/briefings/"
sync_one "CORTEX index" "$HOME/cortex/index/" "$VPS_DEST/cortex/index/"
sync_one "CORTEX scripts" "$HOME/cortex/scripts/" "$VPS_DEST/cortex/scripts/"

# ── Claude global
sync_one "Agentes (.claude/agents)" "$HOME/.claude/agents/" "$VPS_DEST/claude/agents/"
sync_one "Skills (.claude/skills)" "$HOME/.claude/skills/" "$VPS_DEST/claude/skills/"
sync_one "Rules (.claude/rules)" "$HOME/.claude/rules/" "$VPS_DEST/claude/rules/"
rsync -avz "$HOME/.claude/CLAUDE.md" "$VPS_HOST:$VPS_DEST/claude/CLAUDE.md" 2>&1 | tail -2

# ── Auto-memory dos projetos (só pasta memory/, não sessions/)
echo ""
echo "→ Project memories (~/.claude/projects/*/memory/)"
for proj_dir in "$HOME"/.claude/projects/*/; do
  proj_name=$(basename "$proj_dir")
  if [[ -d "$proj_dir/memory" ]]; then
    rsync -avz --delete \
      "$proj_dir/memory/" \
      "$VPS_HOST:$VPS_DEST/claude/projects-memory/$proj_name/" 2>&1 | tail -1
  fi
done

# ── Consciousness — só memory/, não scripts (scripts usam paths absolutos do Mac)
sync_one "Consciousness memory" "$HOME/consciousness/memory/" "$VPS_DEST/consciousness/memory/"
sync_one "Consciousness reflections" "$HOME/consciousness/metacognition/reflections/" "$VPS_DEST/consciousness/reflections/"

# ── Patterns + Feedback Loop (texto puro)
sync_one "Patterns" "$HOME/patterns/" "$VPS_DEST/patterns/"
sync_one "Feedback loop" "$HOME/feedback-loop/" "$VPS_DEST/feedback-loop/"

# ── Marcador de última sincronização
ssh "$VPS_HOST" "echo '$TS' > $VPS_DEST/_last-sync.txt" 2>&1

# ── Tamanho final na VPS
echo ""
echo "════════════════════════════════════════════════"
echo " ✅ SYNC COMPLETO — $(date +%H:%M:%S)"
echo "════════════════════════════════════════════════"
ssh "$VPS_HOST" "du -sh $VPS_DEST && echo '---' && ls -la $VPS_DEST | head -15"
