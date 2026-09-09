#!/bin/bash
# audit_crons.sh — Auditoria zero-deps do crontab local.
#
# Detecta:
#   1. Jobs apontando para scripts INEXISTENTES (dead code)
#   2. Jobs duplicados (mesmo comando, cron diferente)
#   3. Jobs com cadência conflitante (>2 jobs no mesmo horário)
#   4. Candidatos óbvios a Cloud Routine (cadência >=1h + sem deps locais)
#
# Output: ~/cortex/reports/audit-crons-YYYY-MM-DD.md
#
# Origem: F1 do plano de fragilidades (10-Mai-2026).

set -uo pipefail

TODAY=$(date +%Y-%m-%d)
REPORT_DIR="${HOME}/cortex/reports"
REPORT_FILE="${REPORT_DIR}/audit-crons-${TODAY}.md"
mkdir -p "${REPORT_DIR}"

# Captura crontab
CRONS=$(crontab -l 2>/dev/null)
if [[ -z "${CRONS}" ]]; then
  echo "Crontab vazio."
  exit 0
fi

# Filtra comandos efetivos (ignora comentários e linhas vazias)
EFFECTIVE=$(echo "${CRONS}" | grep -v "^#" | grep -v "^$" | grep -v "^@reboot")

TOTAL=$(echo "${EFFECTIVE}" | wc -l | tr -d ' ')
DEAD=0
DUPLICATES=0
CONFLICTS=0
CLOUD_CANDIDATES=0

dead_list=""
dup_list=""
conflict_list=""
cloud_list=""

# ─── 1. Dead code — script não existe ─────────────────────
while IFS= read -r line; do
  [[ -z "${line}" ]] && continue
  # Extrai paths que parecem scripts (/bin/bash X, python3 X, X.sh, X.py)
  paths=$(echo "${line}" | grep -oE '/[a-zA-Z0-9_./-]+\.(sh|py|js)' | head -3)
  for p in ${paths}; do
    if [[ ! -f "${p}" ]]; then
      DEAD=$((DEAD + 1))
      dead_list="${dead_list}- \`${p}\` → cron: \`${line:0:80}\`...\n"
      break
    fi
  done
done <<< "${EFFECTIVE}"

# ─── 2. Duplicados (mesmo comando, frequência diferente) ──
while IFS= read -r line; do
  [[ -z "${line}" ]] && continue
  cmd=$(echo "${line}" | awk '{$1=$2=$3=$4=$5=""; print substr($0,6)}' | xargs)
  count=$(echo "${EFFECTIVE}" | grep -F "${cmd}" | wc -l | tr -d ' ')
  if [[ "${count}" -gt 1 ]] && ! echo "${dup_list}" | grep -qF "${cmd:0:50}"; then
    DUPLICATES=$((DUPLICATES + 1))
    dup_list="${dup_list}- \`${cmd:0:80}\` aparece ${count}x\n"
  fi
done <<< "${EFFECTIVE}"

# ─── 3. Conflitos de horário (>=3 jobs no mesmo cron) ─────
while IFS= read -r tc; do
  [[ -z "${tc}" ]] && continue
  count=$(echo "${tc}" | awk '{print $1}')
  [[ "${count}" -lt 3 ]] && continue
  schedule=$(echo "${tc}" | awk '{print $2,$3,$4,$5,$6}')
  CONFLICTS=$((CONFLICTS + 1))
  conflict_list="${conflict_list}- ${count} jobs em \`${schedule}\`\n"
done < <(echo "${EFFECTIVE}" | awk '{print $1,$2,$3,$4,$5}' | sort | uniq -c | sort -rn)

# ─── 4. Candidatos Cloud Routine ───────────────────────────
# Heurística: jobs daily/weekly que NÃO mexem em ~/broadcast, ~/consciousness,
# ~/feedback-loop, ~/cortex/vault (esses precisam filesystem local)
LOCAL_DEPS_PATTERN="broadcast|consciousness|feedback-loop|cortex/vault|cortex/scripts|cortex/briefings|brainstem|telegram-scraper|meeting-pipeline|segunda-feira-daemon|utm-manager|observations|/scripts/(auto-orchestrator|daily-scan|inema-weekly|reflect-weekly|cortex-sync|check-overdue|week1-evaluation|consciousness-reminder|sf-notify)"
while IFS= read -r line; do
  [[ -z "${line}" ]] && continue
  schedule=$(echo "${line}" | awk '{print $1,$2,$3,$4,$5}')
  # Daily ou menos frequente? (não tem * em min ou */N em hora)
  minute=$(echo "${schedule}" | awk '{print $1}')
  hour=$(echo "${schedule}" | awk '{print $2}')
  [[ "${minute}" == "*" ]] && continue
  [[ "${hour}" == "*" ]] && continue
  if echo "${hour}" | grep -qE "^\*/[1-9]$"; then continue; fi
  # Tem dep local?
  if echo "${line}" | grep -qE "${LOCAL_DEPS_PATTERN}"; then continue; fi
  CLOUD_CANDIDATES=$((CLOUD_CANDIDATES + 1))
  cloud_list="${cloud_list}- \`${schedule}\` → \`${line:0:80}\`...\n"
done <<< "${EFFECTIVE}"

# ─── Relatório ─────────────────────────────────────────────
{
  echo "# Audit Crons — ${TODAY}"
  echo ""
  echo "> Gerado por \`~/cortex/scripts/audit_crons.sh\`"
  echo ""
  echo "## Inventário"
  echo "- Jobs efetivos (não-comentário, não-vazio, não-@reboot): **${TOTAL}**"
  echo "- Jobs apontando para scripts INEXISTENTES: **${DEAD}**"
  echo "- Comandos duplicados: **${DUPLICATES}**"
  echo "- Horários com 3+ jobs simultâneos: **${CONFLICTS}**"
  echo "- Candidatos a Cloud Routine: **${CLOUD_CANDIDATES}**"
  echo ""
  echo "## 1. Dead Code (${DEAD})"
  echo ""
  if [[ "${DEAD}" -eq 0 ]]; then
    echo "_Nenhum job aponta para script inexistente._"
  else
    echo -e "${dead_list}"
    echo ""
    echo "**Ação:** rodar \`crontab -e\` e remover linhas com paths inexistentes."
  fi
  echo ""
  echo "## 2. Duplicados (${DUPLICATES})"
  echo ""
  if [[ "${DUPLICATES}" -eq 0 ]]; then
    echo "_Nenhuma duplicação detectada._"
  else
    echo -e "${dup_list}"
  fi
  echo ""
  echo "## 3. Conflitos de Horário (${CONFLICTS})"
  echo ""
  if [[ "${CONFLICTS}" -eq 0 ]]; then
    echo "_Nenhum horário com 3+ jobs simultâneos._"
  else
    echo -e "${conflict_list}"
    echo ""
    echo "**Ação:** considerar escalonar — múltiplos jobs no mesmo minuto disputam CPU."
  fi
  echo ""
  echo "## 4. Candidatos a Cloud Routine (${CLOUD_CANDIDATES})"
  echo ""
  if [[ "${CLOUD_CANDIDATES}" -eq 0 ]]; then
    echo "_Nenhum candidato óbvio — todos os jobs daily/weekly têm dep local._"
  else
    echo -e "${cloud_list}"
    echo ""
    echo "**Ação:** rodar skill \`schedule\` para migrar — ver playbook \`~/cortex/vault/playbooks/migrate-cron-to-cloud-routines.md\`."
  fi
  echo ""
  echo "## Como rodar de novo"
  echo "\`\`\`bash"
  echo "bash ~/cortex/scripts/audit_crons.sh"
  echo "\`\`\`"
} > "${REPORT_FILE}"

# Print summary
echo ""
echo "=== AUDIT CRONS — ${TODAY} ==="
echo "Jobs efetivos: ${TOTAL}"
echo "Dead code: ${DEAD}"
echo "Duplicados: ${DUPLICATES}"
echo "Conflitos horário: ${CONFLICTS}"
echo "Candidatos Cloud Routine: ${CLOUD_CANDIDATES}"
echo ""
echo "Relatório: ${REPORT_FILE}"
