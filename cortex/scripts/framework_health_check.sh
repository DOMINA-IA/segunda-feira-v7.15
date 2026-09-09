#!/bin/bash
# framework_health_check.sh — Auditoria estrutural completa do Segunda-feira.
#
# Verifica 8 dimensões de saúde:
#   1. Inventário REAL (vs CLAUDE.md)
#   2. Lixo (.bak, .tmp, .old, .orig)
#   3. Arquivos sem frontmatter em diretórios estruturados
#   4. Crontab apontando para scripts inexistentes
#   5. Hooks com permissão errada (não executáveis)
#   6. Diretórios obsoletos ou vazios
#   7. Backup directories velhos
#   8. Drift de números (CLAUDE.md vs realidade)
#
# Output: ~/cortex/reports/framework-health-{YYYY-MM-DD}.md
#
# Origem: pedido CEO 10-Mai antes do bump v7.5 → v7.6.

set -uo pipefail

TODAY=$(date +%Y-%m-%d)
REPORT_DIR="${HOME}/cortex/reports"
REPORT_FILE="${REPORT_DIR}/framework-health-${TODAY}.md"
mkdir -p "${REPORT_DIR}"

# ─── 1. Inventário real ────────────────────────────────────
agents_total=$(ls "${HOME}/.claude/agents/"*.md 2>/dev/null | wc -l | tr -d ' ')
agents_bak=$(ls "${HOME}/.claude/agents/"*.bak* 2>/dev/null | wc -l | tr -d ' ')
skills_total=$(ls "${HOME}/.claude/skills/"*.md 2>/dev/null | wc -l | tr -d ' ')
commands_total=$(ls "${HOME}/.claude/commands/"*.md 2>/dev/null | wc -l | tr -d ' ')
hooks_total=$(ls "${HOME}/.claude/hooks/"*.{py,sh,js} 2>/dev/null | wc -l | tr -d ' ')
rules_global=$(ls "${HOME}/.claude/rules/"*.md 2>/dev/null | wc -l | tr -d ' ')
rules_cortex=$(ls "${HOME}/cortex/vault/rules/"*.md 2>/dev/null | wc -l | tr -d ' ')
rules_total=$((rules_global + rules_cortex))

cortex_notes=$(find "${HOME}/cortex/vault/" -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
cortex_briefings=$(ls "${HOME}/cortex/briefings/"*.md 2>/dev/null | wc -l | tr -d ' ')
cortex_scripts=$(find "${HOME}/cortex/scripts/" -maxdepth 1 \( -name "*.py" -o -name "*.sh" \) 2>/dev/null | wc -l | tr -d ' ')
home_scripts=$(find "${HOME}/scripts/" -maxdepth 1 \( -name "*.py" -o -name "*.sh" \) 2>/dev/null | wc -l | tr -d ' ')

cron_jobs=$(crontab -l 2>/dev/null | grep -cv "^#\|^$" || echo 0)
cron_atreboot=$(crontab -l 2>/dev/null | grep -c "^@reboot" || echo 0)
cron_effective=$((cron_jobs - cron_atreboot))

# ─── 2. Lixo ─────────────────────────────────────────────
trash_files=$(find "${HOME}/.claude" "${HOME}/cortex" "${HOME}/scripts" "${HOME}/broadcast" "${HOME}/consciousness" \
  \( -name "*.bak" -o -name "*.bak.*" -o -name "*.bak-*" -o -name "*.old" -o -name "*.orig" -o -name "*.tmp" \) \
  -not -path "*/node_modules/*" 2>/dev/null | wc -l | tr -d ' ')

trash_archive_dirs=$(find "${HOME}/.claude" "${HOME}/cortex" "${HOME}/broadcast" -type d \
  \( -name "_archive" -o -name "_archived" -o -name ".backup*" -o -name "*-backup*" \) 2>/dev/null)

backup_dirs_size=""
while IFS= read -r d; do
  [[ -z "${d}" ]] && continue
  sz=$(du -sh "${d}" 2>/dev/null | awk '{print $1}')
  backup_dirs_size="${backup_dirs_size}- \`${d/${HOME}/~}\`: ${sz}\n"
done <<< "${trash_archive_dirs}"

# ─── 3. Frontmatter check ────────────────────────────────
missing_frontmatter=""
fm_count=0
for d in "${HOME}/cortex/vault/playbooks" "${HOME}/cortex/vault/projects" "${HOME}/cortex/vault/news"; do
  [[ -d "${d}" ]] || continue
  for f in "${d}"/*.md; do
    [[ -f "${f}" ]] || continue
    first_line=$(head -c 3 "${f}" 2>/dev/null)
    if [[ "${first_line}" != "---" ]]; then
      missing_frontmatter="${missing_frontmatter}- \`${f/${HOME}/~}\`\n"
      fm_count=$((fm_count + 1))
    fi
  done
done

# ─── 4. Cron orphan scripts ──────────────────────────────
cron_orphans=""
cron_orphan_count=0
while IFS= read -r line; do
  [[ "${line}" =~ ^# ]] && continue
  [[ -z "${line}" ]] && continue
  paths=$(echo "${line}" | grep -oE '/[a-zA-Z0-9_./-]+\.(sh|py|js)' | head -3)
  for p in ${paths}; do
    if [[ ! -f "${p}" ]]; then
      cron_orphans="${cron_orphans}- \`${p/${HOME}/~}\`\n"
      cron_orphan_count=$((cron_orphan_count + 1))
      break
    fi
  done
done < <(crontab -l 2>/dev/null)

# ─── 5. Hook permission check ────────────────────────────
hook_nonexec=""
hook_nonexec_count=0
for h in "${HOME}/.claude/hooks/"*.py "${HOME}/.claude/hooks/"*.sh; do
  [[ -f "${h}" ]] || continue
  if [[ ! -x "${h}" ]]; then
    hook_nonexec="${hook_nonexec}- \`${h/${HOME}/~}\` (chmod +x necessário)\n"
    hook_nonexec_count=$((hook_nonexec_count + 1))
  fi
done

# ─── 6. Diretórios vazios ────────────────────────────────
empty_dirs=$(find "${HOME}/cortex/vault" "${HOME}/.claude" -type d -empty 2>/dev/null | head -10)
empty_dirs_count=$(echo -n "${empty_dirs}" | grep -c "^" || echo 0)

# ─── 7. CLAUDE.md drift ──────────────────────────────────
claude_md="${HOME}/.claude/CLAUDE.md"
claude_agents=$(grep -oE "[0-9]+ agentes" "${claude_md}" 2>/dev/null | head -1 | grep -oE "[0-9]+")
claude_skills=$(grep -oE "[0-9]+ skills" "${claude_md}" 2>/dev/null | head -1 | grep -oE "[0-9]+")
claude_rules=$(grep -oE "[0-9]+ rules" "${claude_md}" 2>/dev/null | head -1 | grep -oE "[0-9]+")
claude_hooks=$(grep -oE "[0-9]+ hooks" "${claude_md}" 2>/dev/null | head -1 | grep -oE "[0-9]+")

drift_agents=$((agents_total - ${claude_agents:-0}))
drift_skills=$((skills_total - ${claude_skills:-0}))
drift_rules=$((rules_total - ${claude_rules:-0}))
drift_hooks=$((hooks_total - ${claude_hooks:-0}))

# ─── 8. CORTEX health ────────────────────────────────────
cortex_health=$(python3 "${HOME}/cortex/scripts/cortex_engine.py" health 2>/dev/null | tail -10 || echo "N/A")

# ─── Gerar relatório ─────────────────────────────────────
{
  echo "# Framework Health Check — ${TODAY}"
  echo ""
  echo "> Auditoria estrutural completa. Pré-requisito do bump v7.5 → v7.6."
  echo ""
  echo "## 1. Inventário Real"
  echo ""
  echo "| Componente | CLAUDE.md | Real | Drift |"
  echo "|-----------|-----------|------|-------|"
  echo "| Agentes (.md) | ${claude_agents:-?} | ${agents_total} | ${drift_agents} |"
  echo "| Agentes (.bak) | — | ${agents_bak} | — |"
  echo "| Skills | ${claude_skills:-?} | ${skills_total} | ${drift_skills} |"
  echo "| Commands | — | ${commands_total} | — |"
  echo "| Hooks | ${claude_hooks:-?} | ${hooks_total} | ${drift_hooks} |"
  echo "| Rules (global) | — | ${rules_global} | — |"
  echo "| Rules (cortex) | — | ${rules_cortex} | — |"
  echo "| Rules total | ${claude_rules:-?} | ${rules_total} | ${drift_rules} |"
  echo "| CORTEX notes | — | ${cortex_notes} | — |"
  echo "| CORTEX briefings | — | ${cortex_briefings} | — |"
  echo "| CORTEX scripts | — | ${cortex_scripts} | — |"
  echo "| Home scripts | — | ${home_scripts} | — |"
  echo "| Cron jobs (efetivos) | — | ${cron_effective} | — |"
  echo ""
  echo "## 2. Lixo (${trash_files} arquivos .bak/.old/.orig/.tmp)"
  echo ""
  echo "Detalhamento por diretório:"
  echo -e "${backup_dirs_size:-_Nenhum diretório de backup._}"
  echo ""
  echo "## 3. Arquivos sem frontmatter (${fm_count})"
  echo ""
  if [[ "${fm_count}" -eq 0 ]]; then
    echo "_Todos os arquivos em playbooks/projects/news têm frontmatter._"
  else
    echo -e "${missing_frontmatter}"
  fi
  echo ""
  echo "## 4. Cron orphans (${cron_orphan_count})"
  echo ""
  if [[ "${cron_orphan_count}" -eq 0 ]]; then
    echo "_Todos os jobs apontam para scripts existentes._"
  else
    echo -e "${cron_orphans}"
  fi
  echo ""
  echo "## 5. Hooks sem permissão de execução (${hook_nonexec_count})"
  echo ""
  if [[ "${hook_nonexec_count}" -eq 0 ]]; then
    echo "_Todos os hooks são executáveis._"
  else
    echo -e "${hook_nonexec}"
  fi
  echo ""
  echo "## 6. Diretórios vazios (${empty_dirs_count})"
  echo ""
  if [[ "${empty_dirs_count}" -eq 0 ]]; then
    echo "_Nenhum diretório vazio em \\\`cortex/vault\\\` ou \\\`.claude\\\`._"
  else
    echo "${empty_dirs}" | while read d; do echo "- \`${d/${HOME}/~}\`"; done
  fi
  echo ""
  echo "## 7. CORTEX Health"
  echo ""
  echo '```'
  echo "${cortex_health}"
  echo '```'
  echo ""
  echo "## 8. Drift CLAUDE.md vs Realidade"
  echo ""
  echo "| Métrica | CLAUDE.md | Real | Sinal |"
  echo "|---------|-----------|------|-------|"
  echo "| Agentes | ${claude_agents:-?} | ${agents_total} | $([ "${drift_agents}" -ne 0 ] && echo \"DRIFT ${drift_agents}\" || echo OK) |"
  echo "| Skills | ${claude_skills:-?} | ${skills_total} | $([ "${drift_skills}" -ne 0 ] && echo \"DRIFT +${drift_skills}\" || echo OK) |"
  echo "| Rules | ${claude_rules:-?} | ${rules_total} | $([ "${drift_rules}" -ne 0 ] && echo \"DRIFT +${drift_rules}\" || echo OK) |"
  echo "| Hooks | ${claude_hooks:-?} | ${hooks_total} | $([ "${drift_hooks}" -ne 0 ] && echo \"DRIFT +${drift_hooks}\" || echo OK) |"
  echo ""
  echo "## Como rodar"
  echo ""
  echo '```bash'
  echo "bash ~/cortex/scripts/framework_health_check.sh"
  echo '```'
} > "${REPORT_FILE}"

# Print summary
echo ""
echo "=== FRAMEWORK HEALTH CHECK — ${TODAY} ==="
echo "Agentes:     ${agents_total} (${agents_bak} bak)"
echo "Skills:      ${skills_total}"
echo "Commands:    ${commands_total}"
echo "Hooks:       ${hooks_total}"
echo "Rules:       ${rules_total} (${rules_global} global + ${rules_cortex} cortex)"
echo "CORTEX:      ${cortex_notes} notes, ${cortex_briefings} briefings, ${cortex_scripts} scripts"
echo "Crons:       ${cron_effective} efetivos"
echo ""
echo "Lixo:                ${trash_files} arquivos .bak/.old/.tmp"
echo "Sem frontmatter:     ${fm_count}"
echo "Cron orphans:        ${cron_orphan_count}"
echo "Hooks sem +x:        ${hook_nonexec_count}"
echo "Dirs vazios:         ${empty_dirs_count}"
echo "Drift CLAUDE.md:     A${drift_agents} / S+${drift_skills} / R+${drift_rules} / H+${drift_hooks}"
echo ""
echo "Relatório: ${REPORT_FILE}"
