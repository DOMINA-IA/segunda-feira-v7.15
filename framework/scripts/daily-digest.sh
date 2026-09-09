#!/bin/bash
# daily-digest.sh — Agrega estado do framework Segunda-feira em digest diário.
#
# Origem: passo C do framework-optimization-roadmap (10-Mai-2026).
#
# Coleta:
#   1. Signals novos (não-routed, últimas 24h)
#   2. Heurísticas registradas no Consciousness (últimas 24h)
#   3. Tasks pendentes do framework
#   4. Alertas cost-watchdog
#   5. Pre-flight pendente (.last-preflight.json)
#   6. Resumo CORTEX (notas novas, freshness)
#
# Output:
#   - ~/cortex/reports/daily-digest-YYYY-MM-DD.md
#   - sf-notify.sh para visibilidade no macOS
#
# Como rodar:
#   bash ~/scripts/daily-digest.sh                  # manual agora
#   crontab -e + adicionar:  0 8 * * * /bin/bash ~/scripts/daily-digest.sh
#
# Migração para Cloud Routine (futuro D):
#   - Mesmo prompt em routine cadência diária
#   - Conector Telegram via plugin oficial
#   - Repositório GitHub para acesso aos arquivos

set -uo pipefail

HOME_DIR="${HOME}"
TODAY=$(date +%Y-%m-%d)
NOW=$(date +"%Y-%m-%d %H:%M")
REPORT_DIR="${HOME_DIR}/cortex/reports"
REPORT_FILE="${REPORT_DIR}/daily-digest-${TODAY}.md"
SIGNALS="${HOME_DIR}/broadcast/signals.json"
CONSCIOUSNESS_DIR="${HOME_DIR}/consciousness/memory/episodic"
PREFLIGHT="${HOME_DIR}/.claude/.last-preflight.json"
SF_NOTIFY="${HOME_DIR}/scripts/sf-notify.sh"

mkdir -p "${REPORT_DIR}"

# ─── Cabeçalho ──────────────────────────────────────────────
{
  echo "# Daily Digest — ${TODAY}"
  echo ""
  echo "> Gerado por \`~/scripts/daily-digest.sh\` em ${NOW}"
  echo ""
} > "${REPORT_FILE}"

# ─── 1. Signals ativos ─────────────────────────────────────
{
  echo "## Sinais Ativos (broadcast)"
  echo ""
  if [[ -f "${SIGNALS}" ]]; then
    python3 -c "
import json
from datetime import datetime, timezone, timedelta
try:
    sigs = json.load(open('${SIGNALS}'))
    if not isinstance(sigs, list): sigs = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent = []
    for s in sigs:
        if not isinstance(s, dict): continue
        if s.get('expired'): continue
        ts = s.get('created_at') or s.get('timestamp', '')
        try:
            t = datetime.fromisoformat(ts.replace('Z','+00:00'))
            if t.tzinfo is None: t = t.replace(tzinfo=timezone.utc)
            if t < cutoff: continue
        except Exception: continue
        recent.append(s)
    print(f'**Total ativos últimas 24h:** {len(recent)}')
    print()
    if recent:
        for s in sorted(recent, key=lambda x: x.get('risk',''), reverse=True)[:8]:
            risk = (s.get('risk') or 'low').upper()
            stype = s.get('type','?')
            action = (s.get('action') or s.get('justification') or '')[:120]
            print(f'- [{risk}] **{stype}**: {action}')
    else:
        print('_Nenhum sinal nas últimas 24h._')
except Exception as e:
    print(f'_Erro lendo signals: {e}_')
" 2>&1
  else
    echo "_signals.json não encontrado._"
  fi
  echo ""
} >> "${REPORT_FILE}"

# ─── 2. Heurísticas novas ──────────────────────────────────
{
  echo "## Heurísticas Registradas (24h)"
  echo ""
  if [[ -d "${CONSCIOUSNESS_DIR}" ]]; then
    python3 -c "
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
total = 0
items = []
for f in Path('${CONSCIOUSNESS_DIR}').glob('*.jsonl'):
    try:
        for line in f.read_text().splitlines():
            if not line.strip(): continue
            ep = json.loads(line)
            ts = ep.get('timestamp', '')
            try:
                t = datetime.fromisoformat(ts.replace('Z','+00:00'))
                if t.tzinfo is None: t = t.replace(tzinfo=timezone.utc)
                if t < cutoff: continue
            except Exception: continue
            heur = ep.get('lessons', {}).get('heuristic', '').strip()
            if heur:
                total += 1
                agent = ep.get('agent','?')
                items.append((agent, heur[:150]))
    except Exception: pass
print(f'**Total novas:** {total}')
print()
for ag, h in items[:8]:
    print(f'- {ag}: {h}')
if total == 0:
    print('_Nenhuma heurística registrada nas últimas 24h._')
" 2>&1
  else
    echo "_Diretório consciousness não encontrado._"
  fi
  echo ""
} >> "${REPORT_FILE}"

# ─── 3. Pre-flight pendente ────────────────────────────────
{
  echo "## Pre-Flight Pendente"
  echo ""
  if [[ -f "${PREFLIGHT}" ]]; then
    python3 -c "
import json
try:
    d = json.load(open('${PREFLIGHT}'))
    n = d.get('findings_count', 0)
    print(f'**{n} pendência(s) detectada(s) na última sessão.**')
    print()
    for f in d.get('findings', [])[:5]:
        sev = f.get('severity','info').upper()
        msg = f.get('message','')[:140]
        print(f'- [{sev}] {msg}')
except Exception as e:
    print(f'_Erro lendo preflight: {e}_')
" 2>&1
  else
    echo "_Sem pre-flight pendente (sessão anterior fechou limpa)._"
  fi
  echo ""
} >> "${REPORT_FILE}"

# ─── 4. CORTEX freshness ────────────────────────────────────
{
  echo "## CORTEX — Estado"
  echo ""
  if command -v python3 &> /dev/null; then
    python3 ~/cortex/scripts/cortex_engine.py health 2>/dev/null | grep -E "(notas|edges|tags|freshness|agentes)" | head -8 || echo "_cortex_engine.py health indisponível._"
  fi
  echo ""
} >> "${REPORT_FILE}"

# ─── 5. Tasks pendentes (manual — TaskList só durante sessão) ──
{
  echo "## Roadmap Framework Optimization"
  echo ""
  if [[ -f "${HOME_DIR}/cortex/vault/projects/framework-optimization-roadmap.md" ]]; then
    grep -E "^### (✅|🔜|⏸)" "${HOME_DIR}/cortex/vault/projects/framework-optimization-roadmap.md" | head -8 || echo "_Roadmap sem status visível._"
  else
    echo "_Roadmap não encontrado._"
  fi
  echo ""
} >> "${REPORT_FILE}"

# ─── 6. Footer + ação ───────────────────────────────────────
{
  echo "---"
  echo ""
  echo "## Ações Sugeridas"
  echo ""
  echo "Abra este arquivo: \`open ${REPORT_FILE}\`"
  echo ""
  echo "Próxima geração: amanhã às 08:00 BRT (se cron ativo)."
  echo "Para ativar cron: \`crontab -e\` e adicionar:"
  echo '```'
  echo "0 8 * * * /bin/bash ${HOME_DIR}/scripts/daily-digest.sh >> ${HOME_DIR}/logs/daily-digest.log 2>&1"
  echo '```'
} >> "${REPORT_FILE}"

# ─── Notificação macOS ──────────────────────────────────────
if [[ -x "${SF_NOTIFY}" ]]; then
  bash "${SF_NOTIFY}" "Daily Digest ${TODAY}" "Relatório em ${REPORT_FILE}" info 2>/dev/null || true
fi

echo "Daily digest gerado: ${REPORT_FILE}"
