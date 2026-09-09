#!/bin/bash
# =============================================================================
# cortex-restore.sh — Restaura CORTEX/agentes/skills/memory da VPS CLIENTE_EXEMPLO de volta para o Mac.
#
# Use APENAS em disaster recovery (Mac perdido, novo Mac, vault corrompido).
# NUNCA roda automático — sempre manual + confirmação.
# =============================================================================

set -uo pipefail

VPS_HOST="root@${VPS_HOST}"
VPS_DEST="/opt/segunda-feira-mirror"

echo "════════════════════════════════════════════════"
echo " CORTEX RESTORE — VPS → Mac"
echo " ⚠️  ISSO VAI SOBRESCREVER seu CORTEX local!"
echo "════════════════════════════════════════════════"
echo ""
echo "Última sincronização registrada na VPS:"
ssh "$VPS_HOST" "cat $VPS_DEST/_last-sync.txt 2>/dev/null || echo '(sem registro)'"
echo ""
read -r -p "Tem certeza? Digite 'CONFIRMO RESTORE' para continuar: " confirm
if [[ "$confirm" != "CONFIRMO RESTORE" ]]; then
  echo "Cancelado."
  exit 1
fi

# Backup local antes de sobrescrever
TS=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$HOME/_pre-restore-backup-$TS"
mkdir -p "$BACKUP_DIR"
echo "→ Backup local em $BACKUP_DIR"
cp -R ~/cortex "$BACKUP_DIR/cortex" 2>/dev/null || true
cp -R ~/.claude/agents "$BACKUP_DIR/agents" 2>/dev/null || true
cp -R ~/.claude/skills "$BACKUP_DIR/skills" 2>/dev/null || true
cp -R ~/.claude/rules "$BACKUP_DIR/rules" 2>/dev/null || true

# Pull
RSYNC_OPTS="-avz --delete --human-readable"
echo ""
echo "→ Restaurando CORTEX vault"
rsync $RSYNC_OPTS "$VPS_HOST:$VPS_DEST/cortex/vault/" "$HOME/cortex/vault/"
echo "→ Restaurando agentes"
rsync $RSYNC_OPTS "$VPS_HOST:$VPS_DEST/claude/agents/" "$HOME/.claude/agents/"
echo "→ Restaurando skills"
rsync $RSYNC_OPTS "$VPS_HOST:$VPS_DEST/claude/skills/" "$HOME/.claude/skills/"
echo "→ Restaurando rules"
rsync $RSYNC_OPTS "$VPS_HOST:$VPS_DEST/claude/rules/" "$HOME/.claude/rules/"
echo "→ Restaurando consciousness memory"
rsync $RSYNC_OPTS "$VPS_HOST:$VPS_DEST/consciousness/memory/" "$HOME/consciousness/memory/"
echo "→ Restaurando patterns"
rsync $RSYNC_OPTS "$VPS_HOST:$VPS_DEST/patterns/" "$HOME/patterns/"
echo "→ Restaurando feedback-loop"
rsync $RSYNC_OPTS "$VPS_HOST:$VPS_DEST/feedback-loop/" "$HOME/feedback-loop/"

echo ""
echo "✅ Restore completo. Backup pré-restore em: $BACKUP_DIR"
echo ""
echo "Próximo passo: rebuild CORTEX index + briefings"
echo "  /usr/local/bin/python3 ~/cortex/scripts/cortex_engine.py build-index"
echo "  bash ~/cortex/scripts/build-briefings.sh"
