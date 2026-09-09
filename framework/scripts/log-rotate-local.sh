#!/bin/bash
# log-rotate-local.sh — Rotação leve de logs locais (Mac não tem logrotate nativo)
# Roda diário 04:00 BRT via cron. Logs >500KB ficam só com últimas 2000 linhas + .gz dos antigos.
# Reverter: descomentar o cron e este script.

set -e
LOG_DIR="$HOME/logs"
MAX_SIZE_KB=500
KEEP_LINES=2000

[ -d "$LOG_DIR" ] || exit 0

for log in "$LOG_DIR"/*.log; do
    [ -f "$log" ] || continue
    size_kb=$(du -k "$log" | awk '{print $1}')
    if [ "$size_kb" -gt "$MAX_SIZE_KB" ]; then
        # Guarda cópia comprimida com data
        ts=$(date +%Y%m%d)
        gz="${log%.log}.${ts}.log.gz"
        [ -f "$gz" ] || gzip -c "$log" > "$gz"
        # Mantém apenas últimas N linhas no arquivo ativo.
        # TRUNCA IN-PLACE (cat > $log), não `mv $tmp $log`: o mv troca o inode,
        # e daemons com FileHandler aberto (heartbeat.py) continuam escrevendo no
        # inode antigo órfão — o log fica mudo com o processo vivo (bug 10→16 jul).
        # O redirect `>` preserva o inode, então o fd do daemon segue válido.
        tail -n "$KEEP_LINES" "$log" > "$log.tmp" && cat "$log.tmp" > "$log" && rm -f "$log.tmp"
    fi
done

# Expira .gz com mais de 30 dias
find "$LOG_DIR" -name "*.log.gz" -mtime +30 -delete 2>/dev/null || true

# Marca de execução: sem isto o script é silencioso e o log fica em 0 bytes para
# sempre — nenhum monitor consegue distinguir "rodou e não tinha o que fazer" de
# "não rodou". Diagnóstico de 05-Set-2026.
echo "[$(date +%Y-%m-%dT%H:%M:%S)] log-rotate concluído (rc=0)"
